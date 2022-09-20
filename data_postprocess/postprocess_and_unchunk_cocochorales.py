"""
Post-process the chunked output from MIDI-DDSP
(each chunk corresponds to a job using MIDI-DDSP to synthesize several MIDIs)
and chunk the final dataset by compress pieces into tars.
"""
import os
import glob
import shutil
import argparse
from tqdm import tqdm
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from utils.file_utils import json_load
from utils.instrument_utils import AVAILABLE_ENSEMBLES
from data_postprocess.postprocess_utils import copy_and_separate_midi, move_wavs, split_metadata, save_other_data

NUM_TRACK_DIGITS = 6


def split_piece_list(piece_list, split_json):
    piece_list_split = {}
    for split, split_pieces in split_json.items():
        split_pieces_filename = [f.replace('.mid', '') for f in split_pieces]
        piece_list_split[split] = [p for p in piece_list if os.path.basename(p) in split_pieces_filename]
    return piece_list_split


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Postprocess and Unchunk')
    parser.add_argument('--midi_dir', type=str, default=None, metavar='N',
                        help='The directory containing all the MIDI files.')
    parser.add_argument('--postprocess_output_dir', type=str, default=None, metavar='N',
                        help='The temporary directory for outputting the postprocessed data for each piece.'
                             'The data for each piece will be compressed into tars.')
    parser.add_argument('--zip_dir', type=str, default=None, metavar='N',
                        help='The directory for the zip of each chunk output by MIDI-DDSP.')
    parser.add_argument('--zip_extract_dir', type=str, default=None, metavar='N',
                        help='The temporary directory for outputting the '
                             'extracted data for each chunk output by MIDI-DDSP.')
    parser.add_argument('--final_output_dir', type=str, default=None, metavar='N',
                        help='The directory for the final output containing tars.')
    args = parser.parse_args()
    midi_dir = args.midi_dir
    postprocess_output_dir = args.postprocess_output_dir
    final_output_dir = args.final_output_dir

    splits = ['train', 'valid', 'test']
    main_dataset_dir = os.path.join(postprocess_output_dir, 'main_dataset')
    metadata_dir = os.path.join(postprocess_output_dir, 'metadata')
    note_expression_output_dir = os.path.join(postprocess_output_dir, 'note_expression')
    synthesis_parameters_output_dir = os.path.join(postprocess_output_dir, 'synthesis_parameters')
    f0_output_dir = os.path.join(postprocess_output_dir, 'f0')
    os.makedirs(main_dataset_dir, exist_ok=True)

    # create directory
    for split in splits:
        os.makedirs(os.path.join(metadata_dir, split), exist_ok=True)
        os.makedirs(os.path.join(note_expression_output_dir, split), exist_ok=True)
        os.makedirs(os.path.join(synthesis_parameters_output_dir, split), exist_ok=True)
        os.makedirs(os.path.join(f0_output_dir, split), exist_ok=True)

        os.makedirs(os.path.join(os.path.join(final_output_dir, 'main_dataset'), split), exist_ok=True)
        os.makedirs(os.path.join(os.path.join(final_output_dir, 'metadata'), split), exist_ok=True)
        os.makedirs(os.path.join(os.path.join(final_output_dir, 'note_expression'), split), exist_ok=True)
        os.makedirs(os.path.join(os.path.join(final_output_dir, 'synthesis_parameters'), split), exist_ok=True)
        os.makedirs(os.path.join(os.path.join(final_output_dir, 'f0'), split), exist_ok=True)

    os.makedirs(args.zip_extract_dir, exist_ok=True)

    # you may need to change the following three lines according to your own dataset and split
    split_idx = {'train': 1, 'valid': 192001, 'test': 216001}  # the ID of the first piece in each split
    zip_idx = {'train': 1, 'valid': 1, 'test': 1}  # the ID of the first zip in each split
    NUM_PIECES_IN_ZIP = 2000  # the number of pieces in each zip

    for ensemble in AVAILABLE_ENSEMBLES:
        split_json = json_load(os.path.join(midi_dir, 'split', f'{ensemble}_split.json'))
        ensemble_zip_dir = os.path.join(args.zip_dir, ensemble)
        all_zip_files = sorted(glob.glob(ensemble_zip_dir + '/*.zip'))
        for zip_file in all_zip_files:
            zip_save_path = os.path.join(args.zip_extract_dir, os.path.basename(zip_file))

            os.system(f'cp "{zip_file}" "{zip_save_path}"')
            os.system(f'unzip -q {zip_save_path} -d {args.zip_extract_dir}')

            piece_list = sorted(glob.glob(args.zip_extract_dir + '/*'))
            piece_list_splited = split_piece_list(piece_list, split_json)
            for split, piece_list in piece_list_splited.items():
                for piece_dir in tqdm(piece_list):
                    piece_idx = split_idx[split]
                    piece = os.path.basename(piece_dir)  # piece=name of synthesis dir
                    midi_path = os.path.join(midi_dir, ensemble, f'{piece}.mid')
                    # the name of the piece in the final dataset, different from MIDI file id.
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

                    split_idx[split] += 1

            # Check if each output directory has more than 1000 folders, if so, zip them.
            # Here we use pbzip2 instead of zip because it is faster for large amount of files.
            for split in splits:
                piece_list = glob.glob(main_dataset_dir + f'/{split}/*')
                piece_list = sorted(piece_list, key=lambda x: os.path.basename(x).split('_')[1])
                if len(piece_list) >= NUM_PIECES_IN_ZIP:

                    print(f'start zipping part {zip_idx[split]} of {split}')

                    # zip the first 1000 folders
                    zip_tmp_dir = os.path.join(args.zip_extract_dir, f'tmp')
                    os.makedirs(zip_tmp_dir, exist_ok=True)
                    piece_list_to_remove = piece_list[:NUM_PIECES_IN_ZIP]

                    chunk_file_name = f'{args.zip_extract_dir}/{zip_idx[split]}.tar.bz2'

                    # main dataset
                    for piece in piece_list_to_remove:
                        shutil.move(piece, zip_tmp_dir)
                    os.system(f'tar cf {chunk_file_name} --use-compress-prog=pbzip2 -C {zip_tmp_dir}/ .')
                    os.system(f'mv {chunk_file_name} {final_output_dir}/main_dataset/{split}/')
                    os.system(f'rm -rf {zip_tmp_dir}/*')

                    # metadata
                    for piece in piece_list_to_remove:
                        shutil.move(os.path.join(metadata_dir, split, os.path.basename(piece) + '.yaml'), zip_tmp_dir)
                    os.system(f'tar cf {chunk_file_name} --use-compress-prog=pbzip2 -C {zip_tmp_dir}/ .')
                    os.system(f'mv {chunk_file_name} {final_output_dir}/metadata/{split}/')
                    os.system(f'rm -rf {zip_tmp_dir}/*')

                    # note_expression
                    for piece in piece_list_to_remove:
                        shutil.move(os.path.join(note_expression_output_dir, split, os.path.basename(piece)),
                                    zip_tmp_dir)
                    os.system(f'tar cf {chunk_file_name} --use-compress-prog=pbzip2 -C {zip_tmp_dir}/ .')
                    os.system(f'mv {chunk_file_name} '
                              f'{final_output_dir}/note_expression/{split}/')
                    os.system(f'rm -rf {zip_tmp_dir}/*')

                    # synthesis_parameters
                    for piece in piece_list_to_remove:
                        shutil.move(os.path.join(os.path.join(synthesis_parameters_output_dir, split),
                                                 os.path.basename(piece) + '.pickle'), zip_tmp_dir)
                    os.system(f'tar cf {chunk_file_name} --use-compress-prog=pbzip2 -C {zip_tmp_dir}/ .')
                    os.system(f'mv {chunk_file_name} '
                              f'{final_output_dir}/synthesis_parameters/{split}/')
                    os.system(f'rm -rf {zip_tmp_dir}/*')

                    # f0
                    for piece in piece_list_to_remove:
                        shutil.move(os.path.join(f0_output_dir, split, os.path.basename(piece) + '.pickle'),
                                    zip_tmp_dir)
                    os.system(f'tar cf {chunk_file_name} --use-compress-prog=pbzip2 -C {zip_tmp_dir}/ .')
                    os.system(f'mv {chunk_file_name} '
                              f'{final_output_dir}/f0/{split}/')
                    os.system(f'rm -rf {zip_tmp_dir}/*')

                    zip_idx[split] += 1

            # Remove the zip file
            os.remove(zip_save_path)
            # Remove the unziped directory
            os.system(f'rm -rf {args.zip_extract_dir}/*')
