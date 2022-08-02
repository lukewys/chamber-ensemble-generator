"""Create the tiny version of CocoChorales."""

import os
import shutil
import argparse
import glob

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create the tiny version of CocoChorales.')
    parser.add_argument('--cocochorales_full_dir', type=str, default=None, metavar='N',
                        help='the directory containing the full CocoChorales dataset.')
    parser.add_argument('--output_dir', type=str, default=None, metavar='N',
                        help='the directory for outputting the tiny version of CocoChorales.')
    args = parser.parse_args()
    cocochorales_full_dir = args.cocochorales_full_dir
    output_dir = args.output_dir

    num_tars = {'train': 12,  # 12*2000 per tar = 24000 pieces.
                'valid': 4,  # 4*2000 per tar = 8000 pieces.
                'test': 4  # 4*2000 per tar = 8000 pieces.
                }

    splits = ['train', 'valid', 'test']
    folders = ['main_dataset', 'metadata', 'note_expression', 'synthesis_parameters', 'f0']
    for split in splits:
        for folder in folders:
            # create directory
            os.makedirs(os.path.join(output_dir, folder, split), exist_ok=True)

            # get all the tars
            tars_all = sorted(glob.glob(os.path.join(cocochorales_full_dir, folder, split, '*.tar.bz2')),
                              key=lambda x: int(os.path.basename(x).split('.')[0]))
            tars_to_copy = tars_all[::(len(tars_all) // num_tars[split])]  # take every tar in equidistant intervals.
            for tar in tars_to_copy:
                shutil.copy(tar, os.path.join(output_dir, folder, split))
                print(f'{tar} copied to {os.path.join(output_dir, folder, split)}')
