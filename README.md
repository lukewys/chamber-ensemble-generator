# Chamber Ensemble Generator and CocoChorales Dataset



Chamber Ensemble Generator is a music dataset generation pipeline consist of Coconet and MIDI-DDSP. Chamber Ensemble Generator can generates 4-part Bach Chorales performance audio with aligned notes, note expressions, synthesis parameters (f0, amplitudes, etc) and stems while enabling rich variations in generative process.

We use Chamber Ensemble Generator to generate a large-scale dataset CocoChorlaes. CocoChorales consists of 240,000 pieces in a total duration of 1400 hours, with aligned notes, note expressions, synthesis parameters (f0, amplitudes, etc) and stems. For details of CocoChorales, please check our [paper](https://www.mlasworkshop.com/_files/ugd/35b7d8_ff9e5682cbbe44338b3f1154541ae45f.pdf). 



## CocoChorales Samples

For samples and some statistics of CocoChorales dataset, please check our [dataset website](https://chamber-ensemble-generator.github.io/).



## Dataset Creation

Please check [data_pipeline.md](data_pipeline.md) for detials of Chamber Ensemble Geneartor and how to create CocoChorales Dataset or your won dataset.



## CocoChorales Format

Please check [data_format.md](data_format.md) for the format of the CocoChorlaes dataset.

## Dataset Download

Simply run [data_download/download_cocochorales_full.sh](data_download/download_cocochorales_full.sh) to download the full CocoChorales dataset consists of 240k samples.

The script will download all the data types in the CocoChorales dataset to the `cocochorales_full_v1_zipped` folder it creates under current directory. 
Please see [data_format.md](data_format.md) for details of each type. You could comment the lines of the data download you don't want to download.

Below is size of 5 types of data in CocoChorales:
 - main_dataset: 569G.
 - note_expression: 1.3G.
 - synthesis_parameters: 2.3T.
 - f0: 6.1G.
 - metadata: 279M.
 - total: 2.9T.

You could run [data_download/download_cocochorales_tiny.sh](data_download/download_cocochorales_tiny.sh) to download a tiny version of CocoChorales dataset. 
The script will download all the data types in the CocoChorales tiny dataset to the `cocochorales_tiny_v1_zipped` folder it creates under current directory
The tiny version contains 24k training samples, 8k validation samples and 8k test samples.

Here is [md5](https://storage.googleapis.com/magentadata/datasets/cocochorales/cocochorales_full_v1_zipped/cocochorales_md5s.txt) of the CocoChorales dataset.

## Dataset Extraction
You could run [data_download/extract_tars.py](data_download/extract_tars.py) to extract the downloaded tar files.
```
python data_download/extract_tars.py --data_dir <dir_to_cocochorales_full_v1_zipped> --output_dir <dir_to_cocochorales_full>
```

## Citation
If you use CocoChorales dataset in your research, please cite our paper:
```
[TODO]
```

