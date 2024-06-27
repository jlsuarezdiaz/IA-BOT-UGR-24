#!/bin/bash
#SBATCH -p muylarga
#SBATCH -c 2
#SBATCH --mem=10G
#SBATCH -o slurm_outputs/%A.out
#SBATCH -e slurm_outputs/%A.err

DB_FOLDER='db'
ID=$SLURM_JOB_NAME
DATE=$1
STEALTH=$2
# The next arguments in the list are the levels to evaluate
LEVELS=${@:3}

# cd the directory db/{job_name}, where job_name is the name of the slurm job.
cd $DB_FOLDER/$ID

# Remove the practica2 folder if it exists
rm -rf practica2

# Clone the repository
git clone https://github.com/ugr-ccia-IA/practica2.git

if [ $? -ne 0 ]; then
    python notify.py $ID "Lo siento, se ha producido un error que no depende de mí. Vuelve a intentarlo."
    exit 1
fi
# Rename the repository to software and cd into it
mv practica2 software
cd software
# Copy the files jugador.cpp and jugador.hpp from ../uploads/$DATE to ./Comportamientos_Jugador
cp ../uploads/"$DATE"/jugador.cpp ./Comportamientos_Jugador
cp ../uploads/"$DATE"/jugador.hpp ./Comportamientos_Jugador
#cp ../../../motorlib/* ./src/motorlib
#cp ../../../patches/* ./Comportamientos_Jugador
# Update the motorlib/motor_juego.cpp to modify its output.
sed -i 's/if (monitor\.mostrarResultados() and monitor\.getLevel() < 2)/if(false)/g; s/else if (monitor\.mostrarResultados() and monitor\.getLevel() < 4)/else if(false)/g' ./src/motorlib/motor_juego.cpp 
# Remove the couts from jugador.cpp and jugador.hpp
#sed -i '/\bcout\s*<<.*;/d' ./Comportamientos_Jugador/jugador.cpp
#sed -i '/\bcout\s*<<.*;/d' ./Comportamientos_Jugador/jugador.hpp

# Cmake
cmake -DCMAKE_BUILD_TYPE=Release .
# Compile
make clean
make

# Run the tests.
export PATH="/home/profesia/anaconda/condabin:$PATH"
eval "$(conda shell.bash hook)"
conda activate IA
cp ../../../run_tests.py .
cp ../../../db_functions.py .
cp ../../../mapas/* mapas/
cp ../../../tests.json .
python run_tests.py $ID "$DATE" $SLURM_JOB_ID $STEALTH $LEVELS

# Remove the software folder
cd ..
rm -rf software