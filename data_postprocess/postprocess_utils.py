"""
Utilities for postprocess the data generated from MIDI-DDSP.
"""

import os
import glob
import shutil
import pretty_midi
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from utils.file_utils import pickle_load, pickle_dump, yaml_dump
from midi_ddsp.data_handling.instrument_name_utils import INST_ID_TO_NAME_DICT, INST_NAME_TO_MIDI_PROGRAM_DICT, \
    MIDI_PROGRAM_TO_INST_NAME_DICT


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


def get_f0(synthesis_parameters):
    """Get the f0 from the synthesis parameters."""
    return {key: synthesis_parameters[key]['f0_hz'] for key in synthesis_parameters}


def save_other_data(metadata,
                    note_expression,
                    synthesis_parameters,
                    split,
                    piece_save_id,
                    piece_save_dir,
                    metadata_dir,
                    note_expression_output_dir,
                    synthesis_parameters_output_dir,
                    f0_output_dir):
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

    f0 = get_f0(synthesis_parameters)
    f0_dir = os.path.join(f0_output_dir, split)
    pickle_dump(f0, os.path.join(f0_dir, f'{piece_save_id}.pickle'))


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
    key_sorted = [k for k in ['midi_file',
                              'tempo',
                              'ensemble',
                              'instrument_name',
                              'midi_program_number',
                              'normalization_factor',
                              'target_peak',
                              'normalized',
                              'overall_gain',
                              'stem_integrated_loudness',
                              'pitch_correction_amount'] if k in metadata.keys()]
    metadata_rearrange = {key: metadata[key] for key in key_sorted}

    # add additional metadata not in the sorted list
    metadata_rearrange.update(metadata)

    return metadata_rearrange, note_expression_to_save, synthesis_parameters_to_save
