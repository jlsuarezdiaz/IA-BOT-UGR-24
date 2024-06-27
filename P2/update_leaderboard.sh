#!/bin/bash
#SBATCH -p muylarga
#SBATCH -c 2
#SBATCH -o slurm_outputs/%A.out
#SBATCH -e slurm_outputs/%A.err
#SBATCH -J lb_updater

export PATH="/home/profesia/anaconda/condabin:$PATH"
eval "$(conda shell.bash hook)"
conda activate IA

while true
do
    sleep 10
    python update_leaderboard.py
    scp db/leaderboard.json hercules:/var/www/hercules.ugr.es/IA/P2/data/leaderboard.json
done