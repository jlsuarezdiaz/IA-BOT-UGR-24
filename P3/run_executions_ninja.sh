#!/bin/bash
#SBATCH -p muylarga
#SBATCH -c 16
#SBATCH --mem=1G
#SBATCH -o slurm_outputs/%A.out
#SBATCH -e slurm_outputs/%A.err
#SBATCH --priority=TOP

DB_FOLDER='ninja-battles'
ID=$SLURM_JOB_NAME
DATE=$1
HEURISTIC=$2
# Ninja IDs are the rest of the arguments.
NINJA_IDS=${@:3}

# cd the directory db/{job_name}, where job_name is the name of the slurm job.
cd $DB_FOLDER/$ID/uploads/"$DATE" || exit
# Clone the repository
git clone git@github.com:jlsuarezdiaz/ParchisBoom-Solved.git
# Rename the repository to software and cd into it
mv ParchisBoom-Solved software
cd software
# Copy the files AIPlayer.cpp and AIPlayer.hpp from the parent folder to ./src and ./include, respectively.
cp ../AIPlayer.cpp ./src
cp ../AIPlayer.h ./include

# Cmake
cmake -DCMAKE_BUILD_TYPE=Release .
# Compile
make clean
make -j16
# Copy the script files to the current folder.
cp ../../../../../run_ninja.sh .
cp ../../../../../run_tests.py .
cp ../../../../../db_functions.py .

# Remove the src and include folders
rm -rf src
rm -rf include
rm -rf CMakeFiles
rm CMakeCache.txt
rm cmake_install.cmake
rm Makefile
rm -rf config
rm -rf data
rm -rf doc
rm -rf lib

# Iterate through the ninja IDs and run the tests.
for NINJA_ID in $NINJA_IDS
do
    sbatch -J "$ID" run_ninja.sh $ID "$DATE" 1 $HEURISTIC $NINJA_ID $SLURM_JOB_ID  # Player 1 vs ninja
    sbatch -J "$ID" run_ninja.sh $ID "$DATE" 2 $HEURISTIC $NINJA_ID $SLURM_JOB_ID  # Player 2 vs ninja
done    



# Remove the software folder
#cd ..
#rm -rf software


