from db_functions import *
import json
import os
import shutil

DB_FOLDER = 'db/'

if __name__ == "__main__":
    # Get the leaderboard table from the sql database.
    leaderboard = get_P2_classification()
    # Convert the leaderboard to a dictionary
    leaderboard_dict = {}

    for row in leaderboard:
        leaderboard_dict[row[0]] = {
            "Nombre": row[1],
            "Grupo": row[2],
            "Puntos": row[3],
            "P1": row[30],
            "P2": row[31],
            "P3": row[32],
            "P4": row[33],
            "P5": row[34],
            "P6": row[35],
            "P7": row[36],
            "P8": row[37],
            "P9": row[38],
            "P10": row[39],
            "H1": row[40],
            "H2": row[41],
            "H3": row[42],
            "H4": row[43],
            "H5": row[44],
            "H6": row[45],
            "H7": row[46],
            "H8": row[47],
            "H9": row[48],
            "H10": row[49],
            "S1": row[50],
            "S2": row[51],
            "S3": row[52],
            "S4": row[53],
            "Best submission": row[4],
            "Last submission": row[5],
        }

    # Save the leaderboard in a json file
    leaderboard_file = os.path.join(DB_FOLDER, "leaderboard.json")
    with open(leaderboard_file, "w") as f:
        json.dump(leaderboard_dict, f, indent=4)

    # Save the leaderboard in a csv file TOFO
    #leaderboard_file = os.path.join(DB_FOLDER, "leaderboard.csv")
