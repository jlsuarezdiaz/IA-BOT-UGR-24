__BOT_TOKEN__="__INSERT_BOT_TOKEN_HERE__"

# This script receives a zip and creates a folder with the files needed for the evaluation.
# The zip is located in . and can have any name.
# The folder is created in the same directory as the zip and will have the name entregas.

# The zip has to have the following structure:
#  - A folder with the name of the student
#  - Inside the folder, a new zip file.
#  - The zip file has to contain two files: jugador.cpp and jugador.hpp.
# If there is any other file, the script will fail and notify the names with wrong files.

# If the script succeeds, it will create a folder with the name entregas, with the following structure:
#  - A folder with the name of the student
#  - Inside the folder, the files jugador.cpp and jugador.hpp.

import os
import sys
import zipfile
import shutil
import requests
import asyncio
from telegram import Bot
import re

RE_VIRTUAL_THINK = re.compile(r"virtual\s+void\s+think\s*\(\s*color\s*&\s*c_piece\s*,\s*int\s*&\s*id_piece\s*,\s*int\s*&\s*dice\s*\)\s*const\s*;", re.IGNORECASE)


def check_integrity(path):
    # Read the file from path as text.
    with open(path, 'r') as f:
        # Check if there is a line "virtual void think(color & c_piece, int & id_piece, int & dice) const;"
        # Allow multiple spaces (i.e. use a regular expression).
        if RE_VIRTUAL_THINK.search(f.read()):
            return True
        else:
            return False


def findFilesinSubfolder(path, file):
    cpp_found = False
    h_found = False
    for subfile in os.listdir(path):
        if subfile == "AIPlayer.cpp":
            cpp_found = True
            # Copy the file to the entregas/file folder.
            shutil.copyfile(os.path.join(path, subfile), os.path.join("entregas", file, "AIPlayer.cpp"))
        elif subfile == "AIPlayer.h":
            h_found = True
            # Copy the file to the entregas/file folder.
            shutil.copyfile(os.path.join(path, subfile), os.path.join("entregas", file, "AIPlayer.h"))
        elif subfile.endswith(".zip"):
            try:
                with zipfile.ZipFile(os.path.join(path, subfile), "r") as zip_ref:
                    # Extract the zip to the same folder, with the same name.
                    zip_ref.extractall(os.path.join(path, subfile[:-4]))
            except:
                return False, False
            # Iterate through the subfolder.
            new_cpp_found, new_h_found = findFilesinSubfolder(os.path.join(path, subfile[:-4]), file)
            cpp_found = cpp_found or new_cpp_found
            h_found = h_found or new_h_found
        # Else, if the file is a folder, also iterate through it.
        elif os.path.isdir(os.path.join(path, subfile)) and subfile != "__MACOSX":
            new_cpp_found, new_h_found = findFilesinSubfolder(os.path.join(path, subfile), file) 
            cpp_found = cpp_found or new_cpp_found
            h_found = h_found or new_h_found
    return cpp_found, h_found


async def main():
    error = None
    # Find the zip file. There must be only one.
    zip_file = None
    for file in os.listdir("."):
        if file.endswith(".zip"):
            if zip_file is None:
                zip_file = file
            else:
                error = "Me ha llegado más de un zip."
    
    if zip_file is None:
        error = "No me ha llegado ningún zip."

    # Unzip the file
    if error is None:
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall("submissions")

        # Find the folder inside the zip. There must be only one.
        folder = None
        for file in os.listdir("submissions"):
            if os.path.isdir(os.path.join("submissions", file)):
                if folder is None:
                    folder = file
        
        # Create the folder entregas
        if folder is None:
            error = "Tiene que haber una carpeta solo dentro del zip. Descarga la entrega tal cual viene de PRADO."

    if error is None:
        # Create the folder entregas (if it doesn't exist)
        if not os.path.exists("entregas"):
            os.mkdir("entregas")
            
        # Copy the files
        wrong_entregas = []
        wrong_virtual = []
        for file in os.listdir(os.path.join("submissions")):
            # Enter all subfolders, except the mac weird folder.
            if os.path.isdir(os.path.join("submissions", file)) and file != "__MACOSX":
                cpp_found = False
                h_found = False
                os.mkdir(os.path.join("entregas", file))

                # Loop through all files in the subfolder.
                # If AIPlayer.cpp or AIPlayer.h are found, copy them to the entregas folder.
                # If a zip is found, unzip it and iterate through the subfolder too.
                for subfile in os.listdir(os.path.join("submissions", file)):
                    if subfile == "AIPlayer.cpp":
                        cpp_found = True
                        # Copy the file to the entregas/file folder.
                        shutil.copyfile(os.path.join("submissions", file, subfile), os.path.join("entregas", file, "AIPlayer.cpp"))
                    elif subfile == "AIPlayer.h":
                        h_found = True
                        # Copy the file to the entregas/file folder.
                        shutil.copyfile(os.path.join("submissions", file, subfile), os.path.join("entregas", file, "AIPlayer.h"))
                    elif subfile.endswith(".zip"):
                        with zipfile.ZipFile(os.path.join("submissions", file, subfile), "r") as zip_ref:
                            # Extract the zip to the same folder, with the same name.
                            zip_ref.extractall(os.path.join("submissions", file, subfile[:-4]))
                        # Iterate through the subfolder.
                        new_cpp_found, new_h_found = findFilesinSubfolder(os.path.join("submissions", file, subfile[:-4]), file)
                        cpp_found = cpp_found or new_cpp_found
                        h_found = h_found or new_h_found
                    # Else, if the file is a folder and is not the mac weird folder, also iterate through it.
                    elif os.path.isdir(os.path.join("submissions", file, subfile)) and subfile != "__MACOSX":
                        new_cpp_found, new_h_found = findFilesinSubfolder(os.path.join("submissions", file, subfile), file) 
                        cpp_found = cpp_found or new_cpp_found
                        h_found = h_found or new_h_found

                if not cpp_found or not h_found:
                    wrong_entregas.append(file)

                # If h_found, find if the think is virtual in AIPlayer.h
                if h_found:
                    if not check_integrity(os.path.join("entregas", file, "AIPlayer.h")):
                        wrong_virtual.append(file)

        error = ""
        if len(wrong_entregas) > 0:
            error += "\nHay entregas que no tienen los archivos correctos: " + ", ".join(wrong_entregas)
            error += "\nNecesaria revisión manual"
        if len(wrong_virtual) > 0:
            error += "\nHay entregas que no tienen el método think declarado correctamente: " + ", ".join(wrong_virtual)
            error += "\nEs necesario modificar el AIPlayer.h manualmente para que el método think sea virtual."

    user_id = sys.argv[1]
    TOKEN=__BOT_TOKEN__
    CHAT_ID=user_id
    bot = Bot(token=TOKEN)
    
    if error is None or error == "":
        msg = "Se ha descomprimido todo correctamente. Me pongo a ejecutar."
        await bot.send_message(chat_id=CHAT_ID, text=msg)
    else:
        await bot.send_message(chat_id=CHAT_ID, text=error)
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())