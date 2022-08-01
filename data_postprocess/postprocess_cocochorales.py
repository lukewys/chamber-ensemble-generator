"""
Postprocess the data generated from MIDI-DDSP to the format of the CocoChorales dataset.
"""

import os
import argparse
from tqdm import tqdm
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from utils.file_utils import json_load
from utils.instrument_utils import AVAILABLE_ENSEMBLES
from .postprocess_utils import copy_and_separate_midi, move_wavs, split_metadata, save_other_data

NUM_TRACK_DIGITS = 6

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
    f0_output_dir = os.path.join(output_dir, 'f0')
    os.makedirs(main_dataset_dir, exist_ok=True)

    # create directory for metadata and intermediate_output
    for split in splits:
        os.makedirs(os.path.join(metadata_dir, split), exist_ok=True)
        os.makedirs(os.path.join(note_expression_output_dir, split), exist_ok=True)
        os.makedirs(os.path.join(synthesis_parameters_output_dir, split), exist_ok=True)
        os.makedirs(os.path.join(f0_output_dir, split), exist_ok=True)

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
                                    synthesis_parameters_output_dir,
                                    f0_output_dir)

                    piece_idx += 1

                else:
                    pass  # print(f'Missing piece {piece}')
