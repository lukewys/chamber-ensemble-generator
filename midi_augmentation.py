import numpy as np
from mido import MidiFile
import pretty_midi
import argparse
import glob
import os
from tqdm import tqdm
from utils.instrument_utils import INST_NAME_TO_MIDI_PROGRAM_DICT, get_instrument_by_part, FOUR_BACH_PARTS, \
    AVAILABLE_ENSEMBLES
from utils.file_utils import get_config
from scipy.stats import truncnorm
from utils.file_utils import json_dump


def assign_tempo(midi_file, config):
    mid = MidiFile(midi_file)
    # assign tempo
    tempo = np.random.randint(config['min_tempo'], config['max_tempo'] + 1)
    mid.tracks[0][0].tempo = int(60 / tempo * 1000000)
    # hack here to first save as midi file then read back using pretty_midi
    mid.save('./tmp.mid')
    midi = pretty_midi.PrettyMIDI('./tmp.mid')
    return midi


def assign_instrument(midi, ensemble):
    # assign instruments
    for i, inst in enumerate(midi.instruments):
        instrument = get_instrument_by_part(ensemble, FOUR_BACH_PARTS[i])
        inst.program = INST_NAME_TO_MIDI_PROGRAM_DICT[instrument]
    return midi


def make_instrument_mono(instrument):
    all_notes = instrument.notes
    for i in range(len(all_notes)):
        if i != len(all_notes) - 1:
            if all_notes[i].end > all_notes[i + 1].start:
                all_notes[i].end = all_notes[i + 1].start
    instrument.notes = all_notes


def assign_expressive_performance(midi, config):
    for inst in midi.instruments:
        for note in inst.notes:
            # add expressive timing offset, sampled from truncated normal distribution.
            clip_a = -config['expressive_timing_range_ms']
            clip_b = config['expressive_timing_range_ms']
            mean = config['expressive_timing_mean_ms']
            std = config['expressive_timing_std_ms']

            # sample from truncated normal distribution
            a, b = (clip_a - mean) / std, (clip_b - mean) / std
            timing_offset = truncnorm(a, b).rvs() * std

            # convert to seconds
            timing_offset /= 1000

            note.start += timing_offset
            note.end += timing_offset
        # postprocess notes to make instrument mono
        make_instrument_mono(inst)
    return midi


def midi_augmentation(file_path, ensemble, output_dir, config):
    midi = assign_tempo(file_path, config)
    midi = assign_instrument(midi, ensemble)
    midi = assign_expressive_performance(midi, config)
    midi.write(os.path.join(output_dir, os.path.basename(file_path)))


def generate_split(ensemble_midi_files):
    """Split the midi files into train, val, test"""
    split = {}
    split_name = ['train', 'valid', 'test']
    split_portion = [0.8, 0.1, 0.1]
    midi_filenames = [os.path.basename(f) for f in ensemble_midi_files]
    # split midis to train/valid/test by 0.8/0.1/0.1
    np.random.shuffle(midi_filenames)
    idx = 0
    for name, portion in zip(split_name, split_portion):
        file_num = int(portion * len(midi_filenames))
        split_filenames = midi_filenames[idx:idx + file_num]
        split[name] = split_filenames
        idx += file_num
    return split


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MIDI augmentation')
    parser.add_argument('--midi_dir', type=str, default=None, metavar='N',
                        help='the directory containing all the MIDI files.')
    parser.add_argument('--output_dir', type=str, default=None, metavar='N',
                        help='the directory for outputting the augmented MIDI files.')
    parser.add_argument('--num_tracks_each_ensemble', type=int, default=60000, metavar='N',
                        help='the number of tracks for each ensemble.')
    args = parser.parse_args()

    config = get_config()

    midi_file_list = glob.glob(f'{args.midi_dir}/*.mid')
    np.random.shuffle(midi_file_list)

    os.makedirs(args.output_dir, exist_ok=True)
    split_json_save_dir = os.path.join(args.output_dir, 'split')
    os.makedirs(split_json_save_dir, exist_ok=True)

    file_idx = 0
    for ensemble in AVAILABLE_ENSEMBLES:
        ensemble_midi_files = midi_file_list[file_idx:file_idx + args.num_tracks_each_ensemble]
        for midi_file in tqdm(ensemble_midi_files):
            output_dir = os.path.join(args.output_dir, ensemble)
            os.makedirs(output_dir, exist_ok=True)
            midi_augmentation(midi_file, ensemble, output_dir, config)
        split_json = generate_split(ensemble_midi_files)
        split_json_save_path = os.path.join(split_json_save_dir, f'{ensemble}_split.json')
        json_dump(split_json, split_json_save_path)
        file_idx += args.num_tracks_each_ensemble
