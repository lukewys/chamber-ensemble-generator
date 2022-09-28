#!/bin/bash

mkdir cocochorales_full_v1_zipped
cd cocochorales_full_v1_zipped

# download md5
wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/cocochorales_md5s.txt

# download main dataset
for i in {1..96}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/main_dataset/train/"$i".tar.bz2
done
for i in {1..12}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/main_dataset/valid/"$i".tar.bz2
done
for i in {1..12}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/main_dataset/test/"$i".tar.bz2
done

# download metadata
for i in {1..96}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/metadata/train/"$i".tar.bz2
done
for i in {1..12}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/metadata/valid/"$i".tar.bz2
done
for i in {1..12}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/metadata/test/"$i".tar.bz2
done

# download f0
for i in {1..96}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/f0/train/"$i".tar.bz2
done
for i in {1..12}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/f0/valid/"$i".tar.bz2
done
for i in {1..12}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/f0/test/"$i".tar.bz2
done

# download note expression
for i in {1..96}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/note_expression/train/"$i".tar.bz2
done
for i in {1..12}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/note_expression/valid/"$i".tar.bz2
done
for i in {1..12}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/note_expression/test/"$i".tar.bz2
done

# download synthesis parameters
for i in {1..96}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/synthesis_parameters/train/"$i".tar.bz2
done
for i in {1..12}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/synthesis_parameters/valid/"$i".tar.bz2
done
for i in {1..12}; do
  wget https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/synthesis_parameters/test/"$i".tar.bz2
done