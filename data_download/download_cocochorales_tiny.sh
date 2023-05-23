#!/bin/bash

mkdir cocochorales_tiny_v1_zipped
cd cocochorales_tiny_v1_zipped

# download md5
wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/cocochorales_md5s.txt

# download main dataset
mkdir main_dataset
mkdir main_dataset/train
mkdir main_dataset/valid
mkdir main_dataset/test
for i in 1 2 3 25 26 27 49 50 51 73 74 75; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/main_dataset/train/"$i".tar.bz2 -P main_dataset/train
done
for i in 1 4 7 10; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/main_dataset/valid/"$i".tar.bz2 -P main_dataset/valid
done
for i in 1 4 7 10; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/main_dataset/test/"$i".tar.bz2 -P main_dataset/test
done

# download metadata
mkdir metadata
mkdir metadata/train
mkdir metadata/valid
mkdir metadata/test
for i in 1 2 3 25 26 27 49 50 51 73 74 75; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/metadata/train/"$i".tar.bz2 -P metadata/train
done
for i in 1 4 7 10; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/metadata/valid/"$i".tar.bz2 -P metadata/valid
done
for i in 1 4 7 10; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/metadata/test/"$i".tar.bz2 -P metadata/test
done

# download f0
mkdir f0
mkdir f0/train
mkdir f0/valid
mkdir f0/test
for i in 1 2 3 25 26 27 49 50 51 73 74 75; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/f0/train/"$i".tar.bz2 -P f0/train
done
for i in 1 4 7 10; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/f0/valid/"$i".tar.bz2 -P f0/valid
done
for i in 1 4 7 10; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/f0/test/"$i".tar.bz2 -P f0/test
done

# download note expression
mkdir note_expression
mkdir note_expression/train
mkdir note_expression/valid
mkdir note_expression/test
for i in 1 2 3 25 26 27 49 50 51 73 74 75; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/note_expression/train/"$i".tar.bz2 -P note_expression/train
done
for i in 1 4 7 10; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/note_expression/valid/"$i".tar.bz2 -P note_expression/valid
done
for i in 1 4 7 10; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/note_expression/test/"$i".tar.bz2 -P note_expression/test
done

# download synthesis parameters
mkdir synthesis_parameters
mkdir synthesis_parameters/train
mkdir synthesis_parameters/valid
mkdir synthesis_parameters/test
for i in 1 2 3 25 26 27 49 50 51 73 74 75; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/synthesis_parameters/train/"$i".tar.bz2 -P synthesis_parameters/train
done
for i in 1 4 7 10; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/synthesis_parameters/valid/"$i".tar.bz2 -P synthesis_parameters/valid
done
for i in 1 4 7 10; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/synthesis_parameters/test/"$i".tar.bz2 -P synthesis_parameters/test
done