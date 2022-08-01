# Chamber Ensemble Generator Pipeline

This file will introduce how to use the Chamber Ensemble Generator pipeline to generate Cocochorales dataset or other
dataset according to your need.

## Install Libraries

To install the libraries needed for running the Chamber Ensemble Generator pipeline, simply run:

```
pip install midi-ddsp pyloudnorm
```

## Utilities

The core of the dataset creation pipeline is MIDI-DDSP and the manipulations around the generation process.
We provided several utilities for you to manipulate the generation at each level.
Not all of them are used in CocoChorales dataset.

- [MIDI Augmentation](./midi_augmentation.py): Augment the generated MIDI files to assign random tempo, expressive
  performance and instrumentation.
- [Note Expressions Augmentation](./expression_augmentation.py): assign random note expressions to MIDI-DDSP.
- [Synthesis Parameters Augmentation](./synth_params_augmentation.py): apply random pitch augmentation
(randomly transpose the pitch a little) to the f0, and input the changed f0 to DDSP to synthesize the audio.
- [Audio Augmentation](./audio_augmentation.py): apply random reverb to the stems.

Other utilities include:
 - [Audio Mixing](./audio_mixing.py): apply loudness normalization to the stems for automatic mixing.
 - [Augment Configuration](./augment_config.yaml) Hyperparameters for the augmentation process.

## CocoChorales Generation

To generate CocoChorales, you could start with the MIDI files generated from
an [open-source implementation of Coconet](https://github.com/lukewys/coconet-pytorch). You could directly download the
MIDIs from [here](https://drive.google.com/file/d/1DH4DCsiqpqvwwD5WnFtF-kv7IPAxMLr4/view?usp=sharing), or you could generate your own Bach Chorales.

After the MIDI files are obtained, go to the root directory of this repo and run the following scripts to generate
CocoChorales: (same script can be found in [./create_cocochorales.sh](./create_cocochorales.sh))

```bash
# Suppose the MIDI files generated from Coconet is saved in the root directory as ./coconet_midi_240k

# Step 1: MIDI Augmentation
python midi_augmentation.py \
  --midi_dir ./coconet_midi_240k \
  --output_dir ./cocochorales_midi \
  --num_tracks_each_ensemble 60000

for ensemble_name in string brass woodwind random; do
  # Step 2: Render MIDI to audio
  midi_ddsp_synthesize \
    --midi_dir ./cocochorales_midi/${ensemble_name} \
    --output_dir ./synthesized_midi \
    --skip_existing_files \
    --save_metadata

  # Optional Step: Note Expression Augmentation
  # python expression_augmentation.py --multi_synthesis_dir ./synthesized_midi

  # Optional Step: Synthesis Augmentation
  # python synth_params_augmentation.py --multi_synthesis_dir ./synthesized_midi

  # Optional Step: Reverb Augmentation
  # python audio_augmentation.py --multi_synthesis_dir ./synthesized_midi

  # Step 3: Mix audio
  python audio_mixing.py --multi_synthesis_dir ./synthesized_midi
done

# Step 4: Post Process
python data_postprocess/postprocess_cocochorales.py \
  --midi_dir ./cocochorales_midi \
  --synthesis_dir ./synthesized_midi \
  --output_dir ./cocochorales_full
```

## Large-scale Generation

In generating CocoChorales, we actually split MIDI files into chunks and generate CocoChorales by running dataset
creation script in parallel. We use a compute cluster to generate CocoChorales where each script is a job to generate
one chunk. After each chunk is generated, we
use [data_postprocess/postprocess_and_unchunk.py](data_postprocess/postprocess_and_unchunk_cocochorales.py) to post process the
output. [Here](https://drive.google.com/file/d/1yhCJgrY1rP01hYqif_lgITSophB3eRaW/view?usp=sharing) you can find the chunked MIDI files.

For each job (chunk), we use 16GB of RAM and 4 cores of CPU. We recommend using CPU for dataset generation as most of
the compute is the autoregressive RNN in MIDI-DDSP to generate pitch curve. We use 256 jobs (chunks) and the total
generation time for each chunk (without post processing) is about 18 hours.

## Creating Your Own Dataset

If you would like to create your own dataset with your own MIDI, you could take the following script for reference:

```bash
# Suppose the MIDI files are saved in <midi_dir>

# Step 1: Render MIDI to audio
midi_ddsp_synthesize \
--midi_dir <midi_dir> \
--output_dir ./synthesized_midi \
--skip_existing_files \
--save_metadata

# Optional Step: Note Expression Augmentation
python expression_augmentation.py --multi_synthesis_dir ./synthesized_midi

# Optional Step: Synthesis Augmentation
python synth_params_augmentation.py --multi_synthesis_dir ./synthesized_midi

# Optional Step: Reverb Augmentation
python audio_augmentation.py --multi_synthesis_dir ./synthesized_midi

# Step 2: Mix audio
python audio_mixing.py --multi_synthesis_dir ./synthesized_midi
```





