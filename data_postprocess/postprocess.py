"""
Postprocess the data generated from MIDI-DDSP to the format of the CocoChorales dataset.
"""

import os
import glob
import shutil
import argparse
from tqdm import tqdm
import pretty_midi
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from utils.file_utils import json_load, pickle_load, pickle_dump, yaml_dump
from midi_ddsp.data_handling.instrument_name_utils import INST_ID_TO_NAME_DICT, INST_NAME_TO_MIDI_PROGRAM_DICT, \
    MIDI_PROGRAM_TO_INST_NAME_DICT
from utils.instrument_utils import AVAILABLE_ENSEMBLES

NUM_TRACK_DIGITS = 6


def get_midi_tempo(midi_path):
    return int(pretty_midi.PrettyMIDI(midi_path).get_tempo_changes()[1][0])


def move_wavs(piece_dir, save_dir, copy=False):
    """Move wav files for re-structure. If copy is True, copy instead of move."""
    stem_audio_save_dir = os.path.join(save_dir, 'stems_audio')
    os.makedirs(stem_audio_save_dir, exist_ok=True)
    all_audios = glob.glob(piece_dir + '/*.wav')
    all_stems = sorted([f for f in all_audios if 'mix.wav' not in f])
    for i, stem in enumerate(all_stems):
        instrument_name = os.path.basename(stem).split('_')[1].replace('.wav', '')
        if copy:
            shutil.copy(stem, os.path.join(stem_audio_save_dir, f'{i + 1}_{instrument_name}.wav'))  # 1-indexed
        else:
            shutil.move(stem, os.path.join(stem_audio_save_dir, f'{i + 1}_{instrument_name}.wav'))  # 1-indexed
    mix_audio = os.path.join(piece_dir, 'mix.wav')
    if copy:
        shutil.copy(mix_audio, os.path.join(save_dir, 'mix.wav'))
    else:
        shutil.move(mix_audio, os.path.join(save_dir, 'mix.wav'))


def copy_and_separate_midi(midi_file, save_dir):
    """Copy the midi file to the save_dir and separate the midi into stems."""
    midi = pretty_midi.PrettyMIDI(midi_file)
    midi.write(os.path.join(save_dir, 'mix.mid'))
    stem_midi_save_dir = os.path.join(save_dir, 'stems_midi')
    os.makedirs(stem_midi_save_dir, exist_ok=True)
    for i, inst in enumerate(midi.instruments):
        stem_midi = pretty_midi.PrettyMIDI(initial_tempo=midi.get_tempo_changes()[1][0])  # use the same tempo
        stem_midi.instruments.append(inst)
        instrument_name = MIDI_PROGRAM_TO_INST_NAME_DICT[inst.program]
        stem_midi.write(os.path.join(stem_midi_save_dir, f'{i + 1}_{instrument_name}.mid'))  # 1-indexed


def save_other_data(metadata,
                    note_expression,
                    synthesis_parameters,
                    split,
                    piece_save_id,
                    piece_save_dir,
                    metadata_dir,
                    note_expression_output_dir,
                    synthesis_parameters_output_dir):
    """Save the metadata, note_expression, and synthesis_parameters to the corresponding directories."""
    # Save metadata to main dataset
    yaml_dump(metadata, os.path.join(piece_save_dir, f'metadata.yaml'))
    # Save a second copy of metadata to standalone metadata folder
    metadata_save_dir = os.path.join(metadata_dir, split)
    yaml_dump(metadata, os.path.join(metadata_save_dir, f'{piece_save_id}.yaml'))

    # Save note expression data
    note_expression_dir = os.path.join(note_expression_output_dir, split, piece_save_id)
    os.makedirs(note_expression_dir, exist_ok=True)
    for key in note_expression:
        instrument_name = metadata['instrument_name'][key]
        note_expression[key].to_csv(os.path.join(note_expression_dir, f'{key}_{instrument_name}.csv'))

    # Save synthesis parameters.
    # The directory for saving synthesized parameters is already created, so no need to create again
    synthesis_parameters_dir = os.path.join(synthesis_parameters_output_dir, split)
    pickle_dump(synthesis_parameters, os.path.join(synthesis_parameters_dir, f'{piece_save_id}.pickle'))


def split_metadata(midi_path, piece_dir, ensemble):
    """Split the metadata of the piece into metadata, note_expression and synthesis_parameters."""

    # dir: the save dir of current split
    metadata_path = os.path.join(piece_dir, 'metadata.pickle')

    # first save intermediate output
    metadata = pickle_load(metadata_path)
    synthesis_parameters_to_save = metadata['synthesis_parameters']

    # Rename the keys in note_expression.
    # This is unnecessary now, but for compatibility with earlier versions of MIDI-DDSP.
    note_expression = metadata['note_expression_control']
    note_expression_to_save = {}
    for key in note_expression:
        note_expression_part = note_expression[key]
        note_expression_part.columns = ['volume', 'vol_fluc', 'vibrato', 'brightness', 'attack', 'vol_peak_pos',
                                        'pitch', 'onset', 'offset', 'note_length']
        note_expression_to_save[key] = note_expression_part

    # delete intermediate output from metadata
    metadata.pop('note_expression_control', None)
    metadata.pop('synthesis_parameters', None)
    instrument_name = {i: INST_ID_TO_NAME_DICT[instrument_id] for i, instrument_id in
                       enumerate(metadata['instrument_id'].values())}
    midi_program_number = {i: INST_NAME_TO_MIDI_PROGRAM_DICT[INST_ID_TO_NAME_DICT[instrument_id]] for i, instrument_id
                           in enumerate(metadata['instrument_id'].values())}

    # delete useless metadata
    metadata.pop('instrument_id', None)
    metadata.pop('integrated_loudness', None)
    # add additional metadata
    metadata['tempo'] = get_midi_tempo(midi_path)
    metadata['ensemble'] = ensemble
    metadata['midi_file'] = os.path.basename(midi_path)
    metadata['instrument_name'] = instrument_name
    metadata['midi_program_number'] = midi_program_number

    # Rearrange keys in metadata for readability.
    metadata_rearrange = {key: metadata[key] for key in ['midi_file',
                                                         'tempo',
                                                         'ensemble',
                                                         'instrument_name',
                                                         'midi_program_number',
                                                         'normalization_factor',
                                                         'target_peak',
                                                         'normalized',
                                                         'overall_gain',
                                                         'stem_integrated_loudness',
                                                         'pitch_correction_amount']}

    # add additional metadata not in the sorted list
    metadata_rearrange.update(metadata)

    return metadata_rearrange, note_expression_to_save, synthesis_parameters_to_save


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Postprocess')
    parser.add_argument('--midi_dir', type=str, default=None, metavar='N',
                        help='the directory containing all the MIDI files.')
    parser.add_argument('--synthesis_dir', type=str, default=None, metavar='N',
                        help='the directory containing all the synthesized audios in each folder.')
    parser.add_argument('--output_dir', type=str, default=None, metavar='N',
                        help='the directory for outputting the postprocessed dataset.')
    args = parser.parse_args()
    midi_dir = args.midi_dir
    synthesis_dir = args.synthesis_dir
    output_dir = args.output_dir

    splits = ['train', 'valid', 'test']

    main_dataset_dir = os.path.join(output_dir, 'main_dataset')
    metadata_dir = os.path.join(output_dir, 'metadata')
    note_expression_output_dir = os.path.join(output_dir, 'note_expression')
    synthesis_parameters_output_dir = os.path.join(output_dir, 'synthesis_parameters')
    os.makedirs(main_dataset_dir, exist_ok=True)

    # create directory for metadata and intermediate_output
    for split in splits:
        os.makedirs(os.path.join(metadata_dir, split), exist_ok=True)
        os.makedirs(os.path.join(note_expression_output_dir, split), exist_ok=True)
        os.makedirs(os.path.join(synthesis_parameters_output_dir, split), exist_ok=True)

    piece_idx = 1
    for ensemble in AVAILABLE_ENSEMBLES:
        # load the split file containing MIDI filenames for each split.
        split_json = json_load(os.path.join(midi_dir, 'split', f'{ensemble}_split.json'))

        for split in splits:
            piece_list = split_json[split]  # find all the MIDI files in the split
            piece_list = [p.replace('.mid', '') for p in piece_list]
            for piece in tqdm(piece_list):
                piece_dir = os.path.join(synthesis_dir, ensemble, piece)
                if os.path.exists(piece_dir):
                    midi_path = os.path.join(midi_dir, ensemble, f'{piece}.mid')

                    # piece_save_id is the name of the piece in the final dataset, different from MIDI file id.
                    piece_save_id = f'{ensemble}_track{str(piece_idx).zfill(NUM_TRACK_DIGITS)}'
                    piece_save_dir = os.path.join(main_dataset_dir, split, piece_save_id)
                    os.makedirs(piece_save_dir, exist_ok=True)
                    copy_and_separate_midi(midi_path, piece_save_dir)
                    move_wavs(piece_dir, piece_save_dir)

                    metadata, note_expression, synthesis_parameters = split_metadata(midi_path, piece_dir, ensemble)
                    save_other_data(metadata,
                                    note_expression,
                                    synthesis_parameters,
                                    split,
                                    piece_save_id,
                                    piece_save_dir,
                                    metadata_dir,
                                    note_expression_output_dir,
                                    synthesis_parameters_output_dir)

                    piece_idx += 1

                else:
                    pass #print(f'Missing piece {piece}')
