import numpy as np
from mido import MidiFile
import pretty_midi
import argparse
import glob
import os
from tqdm import tqdm
from utils.instrument_utils import (
    INST_NAME_TO_MIDI_PROGRAM_DICT,
    get_instrument_by_part,
    FOUR_BACH_PARTS,
    AVAILABLE_ENSEMBLES,
)
from utils.file_utils import get_config
from scipy.stats import truncnorm
from utils.file_utils import json_dump
import wandb


def assign_tempo(midi_file, config):
    """
    Assigns a random tempo to a MIDI file.

    Args:
        midi_file (str): The path to the MIDI file.
        config (dict): A dictionary containing the configuration parameters.

    Returns:
        pretty_midi.PrettyMIDI: The modified MIDI object with the assigned tempo.
    """
    mid = MidiFile(midi_file)
    # assign tempo
    tempo = np.random.randint(config["min_tempo"], config["max_tempo"] + 1)
    mid.tracks[0][0].tempo = int(60 / tempo * 1000000)
    # hack here to first save as midi file then read back using pretty_midi
    mid.save("./tmp.mid")
    midi = pretty_midi.PrettyMIDI("./tmp.mid")
    return midi


def assign_instrument(midi, ensemble):
    """
    Assigns instruments to the MIDI tracks based on the given ensemble.

    Args:
        midi (MIDIFile): The MIDI object containing the tracks.
        ensemble (list): The list of instruments in the ensemble.

    Returns:
        MIDIFile: The modified MIDI object with instruments assigned to tracks.
    """
    # assign instruments
    for i, inst in enumerate(midi.instruments):
        instrument = get_instrument_by_part(ensemble, FOUR_BACH_PARTS[i])
        inst.program = INST_NAME_TO_MIDI_PROGRAM_DICT[instrument]
    return midi


def make_instrument_mono(instrument):
    """
    Make the instrument monophonic by adjusting the note durations.

    Args:
        instrument (Instrument): The instrument to make monophonic.

    Returns:
        None
    """
    all_notes = instrument.notes
    for i in range(len(all_notes)):
        if i != len(all_notes) - 1:
            if all_notes[i].end > all_notes[i + 1].start:
                all_notes[i].end = all_notes[i + 1].start
    instrument.notes = all_notes


def assign_expressive_performance(midi, config):
    """
    Assigns expressive performance to the MIDI notes by adding timing offsets sampled from a truncated normal distribution.

    Args:
        midi (MIDIFile): The MIDI object containing the notes.
        config (dict): A dictionary containing configuration parameters for the expressive performance.

    Returns:
        MIDIFile: The modified MIDI object with expressive performance assigned to the notes.
    """
    for inst in midi.instruments:
        for note in inst.notes:
            # add expressive timing offset, sampled from truncated normal distribution.
            clip_a = -config["expressive_timing_range_ms"]
            clip_b = config["expressive_timing_range_ms"]
            mean = config["expressive_timing_mean_ms"]
            std = config["expressive_timing_std_ms"]

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


def midi_augmentation(file_path, ensemble, output_dir, config, expressive_timing=True):
    """
    Applies MIDI augmentation to the given file.

    Args:
        file_path (str): The path to the MIDI file to be augmented.
        ensemble (str): The ensemble to assign to the MIDI file.
        output_dir (str): The directory where the augmented MIDI file will be saved.
        config (dict): Configuration settings for the augmentation process.

    Returns:
        None
    """
    midi = assign_tempo(file_path, config)
    midi = assign_instrument(midi, ensemble)
    if expressive_timing:
        midi = assign_expressive_performance(midi, config)
    midi.write(os.path.join(output_dir, os.path.basename(file_path)))


def generate_split(ensemble_midi_files):
    """Split the midi files into train, val, test.

    Args:
        ensemble_midi_files (list): List of MIDI file paths.

    Returns:
        dict: A dictionary containing the split MIDI file names, with keys 'train', 'valid', and 'test'.
    """
    split = {}
    split_name = ["train", "valid", "test"]
    split_portion = [0.8, 0.1, 0.1]
    midi_filenames = [os.path.basename(f) for f in ensemble_midi_files]
    # split midis to train/valid/test by 0.8/0.1/0.1
    np.random.shuffle(midi_filenames)
    idx = 0
    for name, portion in zip(split_name, split_portion):
        file_num = int(portion * len(midi_filenames))
        split_filenames = midi_filenames[idx : idx + file_num]
        split[name] = split_filenames
        idx += file_num
    return split


def augment_midi_files(
    midi_dir,
    output_dir,
    num_tracks_each_ensemble,
    config=get_config(),
    expressive_timing=True,
):
    """
    Augments MIDI files by generating variations of the original tracks for different ensembles.

    Args:
        midi_dir (str): The directory path containing the MIDI files.
        output_dir (str): The directory path to save the augmented MIDI files.
        num_tracks_each_ensemble (int): The number of tracks to generate for each ensemble.
        config (dict, optional): Configuration settings for the augmentation process. Defaults to get_config().

    Returns:
        None
    """
    midi_file_list = glob.glob(f"{midi_dir}/*.mid")
    np.random.shuffle(midi_file_list)

    os.makedirs(output_dir, exist_ok=True)
    split_json_save_dir = os.path.join(output_dir, "split")
    os.makedirs(split_json_save_dir, exist_ok=True)

    file_idx = 0
    for ensemble in AVAILABLE_ENSEMBLES:
        ensemble_midi_files = midi_file_list[
            file_idx : file_idx + num_tracks_each_ensemble
        ]
        for midi_file in tqdm(ensemble_midi_files):
            ensemble_output_dir = os.path.join(output_dir, ensemble)
            os.makedirs(ensemble_output_dir, exist_ok=True)
            midi_augmentation(
                midi_file, ensemble, ensemble_output_dir, config, expressive_timing=True
            )  # Assumes midi_augmentation is defined elsewhere in the script
        split_json = generate_split(
            ensemble_midi_files
        )  # Assumes generate_split is defined elsewhere
        split_json_save_path = os.path.join(
            split_json_save_dir, f"{ensemble}_split.json"
        )
        json_dump(
            split_json, split_json_save_path
        )  # Assumes json_dump is defined elsewhere
        file_idx += num_tracks_each_ensemble


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="MIDI augmentation")
    parser.add_argument(
        "--midi_dir",
        type=str,
        required=True,
        help="the directory containing all the MIDI files.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="the directory for outputting the augmented MIDI files.",
    )
    parser.add_argument(
        "--num_tracks_each_ensemble",
        type=int,
        default=60000,
        help="the number of tracks for each ensemble.",
    )
    args = parser.parse_args()

    config = get_config()

    augment_midi_files(
        args.midi_dir,
        args.output_dir,
        args.num_tracks_each_ensemble,
        config,
        expressive_timing=True,
    )
