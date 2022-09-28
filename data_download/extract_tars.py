import os
import glob
from tqdm import tqdm
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default=None, metavar='N',
                        help='the directory containing all the zip files downloaded from the GCS.')
    parser.add_argument('--output_dir', type=str, default=None, metavar='N',
                        help='the directory for outputting the extracted dataset.')

    args = parser.parse_args()

    data_dir = args.data_dir
    output_dir = args.output_dir

    # you could only use 'main_dataset'
    for data_type in ['f0', 'main_dataset', 'metadata', 'note_expression', 'synthesis_parameters']:
        for split in ['train', 'test', 'valid']:
            os.makedirs(os.path.join(output_dir, data_type, split), exist_ok=True)
            tar_files = sorted(glob.glob(os.path.join(data_dir, data_type, split, '*.tar.bz2')),
                               key=lambda x: int(os.path.basename(x).split('.')[0]))
            for tar_file in tqdm(tar_files):
                os.system(
                    f'tar -xf {tar_file} --use-compress-prog=pbzip2 -C {os.path.join(output_dir, data_type, split)}')
