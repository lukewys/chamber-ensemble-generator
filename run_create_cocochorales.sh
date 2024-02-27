#!/bin/bash
#SBATCH -A debug
#SBATCH -t 0:30:00
#SBATCH -p gilbreth-debug
#SBATCH -N 1
#SBATCH --gpus-per-node=1
#SBATCH --ntasks-per-node=1 
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name="as-gen-data"
#SBATCH --error=./logs/gen/%x-%J-%u.err
#SBATCH --output=./logs/gen/%x-%J-%u.out


module --force purge
module load rcac 
module load anaconda 
module list

set -x
source activate /depot/yunglu/data/ben/.conda/score2audio
cd /home/chou150/depot/code/chamber-ensemble-generator

# export CUDA_VISIBLE_DEVICES=

python create_cocochorales.py