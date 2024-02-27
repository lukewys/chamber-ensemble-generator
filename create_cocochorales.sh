#!/bin/bash
#SBATCH -A debug
#SBATCH -t 0:30:00
#SBATCH -p gilbreth-debug
#SBATCH -N 1
#SBATCH --gpus-per-node=1
#SBATCH --ntasks-per-node=2 # Adjusted to run 8 tasks in parallel
#SBATCH --mem-per-cpu=16gb
#SBATCH --cpus-per-task=1 # Adjusted to allocate 4 CPUs per task
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name="as-gen-data"
#SBATCH --error=./logs/gen/%x-%J-%u.err
#SBATCH --output=./logs/gen/%x-%J-%u.out


module --force purge
module load rcac
module load anaconda 
module load ffmpeg
module list

set -x
source activate /depot/yunglu/data/ben/.conda/score2audio
cd /home/chou150/depot/code/chamber-ensemble-generator


# Suppose the MIDI files generated from Coconet is saved in the root directory as ./coconet_midi_240k

# Step 1: MIDI Augmentation
python midi_augmentation.py \
  --midi_dir /home/chou150/depot/datasets/cocochorales_full/org_chunked_midi/brass/0 \
  --output_dir /home/chou150/depot/datasets/cocochorals_exp/cocochorales_midi \
  --num_tracks_each_ensemble 60000

for ensemble_name in string brass woodwind random; do
  # Step 2: Render MIDI to audio
  midi_ddsp_synthesize \
    --midi_dir /home/chou150/depot/datasets/cocochorals_exp/cocochorales_midi/${ensemble_name} \
    --output_dir /home/chou150/depot/datasets/cocochorals_exp/synthesized_midi \
    --skip_existing_files \
    --save_metadata

  # Optional Step: Note Expression Augmentation
  # python expression_augmentation.py --multi_synthesis_dir ./synthesized_midi

  # Optional Step: Synthesis Augmentation
  # python synth_params_augmentation.py --multi_synthesis_dir ./synthesized_midi

  # Optional Step: Reverb Augmentation
  # python audio_augmentation.py --multi_synthesis_dir ./synthesized_midi

  # Step 3: Mix audio
  python audio_mixing.py --multi_synthesis_dir /home/chou150/depot/datasets/cocochorals_exp/synthesized_midi
done

# Step 4: Post Process
python data_postprocess/postprocess_cocochorals.py \
  --midi_dir /home/chou150/depot/datasets/cocochorals_exp/cocochorales_midi \
  --synthesis_dir /home/chou150/depot/datasets/cocochorals_exp/synthesized_midi \
  --output_dir /home/chou150/depot/datasets/cocochorals_exp/cocochorales_full
