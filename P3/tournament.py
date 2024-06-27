__BOT_TOKEN__="__INSERT_BOT_TOKEN_HERE__"

import os
import telegram
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot, Update
from telegram.ext import Updater, MessageHandler, filters, CommandHandler, ConversationHandler, ApplicationBuilder, ContextTypes
import queue
import logging
import json
import datetime
import random
import sys
import requests
import subprocess
import math
import pandas as pd
import time
from filelock import FileLock
from db_functions import *
import asyncio
import sys
from utils import send_leaderboard


async def main():
    # cd to "tour-executions" folder
    os.chdir("tour-executions")

    bot = Bot(__BOT_TOKEN__)
    notify_groups = {
        "GRADO": (-1002094212883, 2118),
        "DOBLE": (-1002135484699, 698)
    }

    # Get a list with all the folders in the current directory
    folders = [f for f in os.listdir('.') if os.path.isdir(f)]

    # Remove the folder named "software" from the list.
    folders.remove("software")


    # Create a table with the tournament results.
    current_date = sys.argv[1]
    # current_date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    # create_P3_tournament_table(current_date, db_path="../../IA_DB.db")
    # copy_P3_tour_players(current_date, db_path="../../IA_DB.db")
    all_players = get_P3_tour_players_date(current_date, "../../IA_DB.db")

    # Notify all the players that the tournament has started.
    async with bot:
        try:
            # msg = f"⚔️ ¡COMIENZAN LAS BATALLAS! ⚔️ ¡Hoy participan {len(all_players)} combatientes! [{current_date}]"
            msg = f"⚔️ ¡COMIENZAN LAS BATALLAS! ⚔️ ¡Se juegan el campeonato final {len(all_players)} valientes! [{current_date}]"
            for player_id in all_players.keys():
                if all_players[player_id]["notify"] in [1, 2] and all_players[player_id]['type'] != 'LNINJA':
                    await bot.send_message(chat_id=player_id, text=msg)

            for _, (group_id, thread_id) in notify_groups.items():
                await bot.send_message(chat_id=group_id, text=msg, message_thread_id=thread_id)
        except Exception as e:
            print(f"Error sending message to {player_id}. {e}")
    

    # cd ..
    os.chdir("..")

    # Check the number of players. If there are less than 60, we will do a round-robin.
    # All will have to battle against all, playing as player 1 and player 2.
    # A player will not play against itself.
    print(all_players)
    if len(all_players) < 300:
        all_pairings = []
        for player1 in all_players:
            for player2 in all_players:
                if player1 != player2:
                    all_pairings.append((player1, player2))
        print(all_pairings)
   
        for p1, p2 in all_pairings:
            # For each pair of battles submit a slurm job
            os.system(f'sbatch -J tour-{p1}-{p2} tour_battle.sh {p1} {p2} {current_date}')

        # Wait until all the battles have finished.
        all_battles_finished = False
        while not all_battles_finished:
            all_battles_finished = get_P3_total_battles(current_date) == len(all_pairings)
            # Wait 30 seconds before checking again.
            time.sleep(30)
        
        update_P3_current_battles_table(current_date, db_path="../IA_DB.db")
        
        classification_table = get_P3_classification("current", db_path="../IA_DB.db")
        try:
            # Save the clssification_table (is a pandas dataframe) as a json file.
            classification_table.T.to_json(f"classification_table_full.json")
            public_cf = classification_table.drop(columns=["player_id", "name", "surname"])
            public_cf.T.to_json(f"classification_table.json")
            battles_table = get_P3_detailed_battles_df("current", db_path="../IA_DB.db")
            battles_table.T.to_json(f"battles_table_full.json")
            public_bt = battles_table.drop(columns=["P1_id", "P1_name", "P1_surname", "P2_id", "P2_name", "P2_surname"])
            public_bt.T.to_json(f"battles_table.json")

        except Exception as e:
            print(f"Error saving classification_table. {e}")
        # Notify all the players that the tournament has finished and send them their position and result.
        msg1 = f"🏆 EL TORNEO DEFINITIVO HA FINALIZADO 🏆 [{current_date}]"
        msg2 = "ENHORABUENA A LOS CAMPEONES: 🥇🥈🥉🎖️🔝"
        msg3 = ""
        msg4 = ""
        msg_end = f"Hola. Aquí termina mi trabajo. Ha sido un placer. Me lo he pasado muy bien estos meses. Espero que hayas disfrutado del torneo y de la asignatura en general. Mucha suerte con los exámenes. ¡Hasta pronto y gracias! 👋🫡"
        for player in all_players:
            if all_players[player]["notify"] in [1, 2] and all_players[player]['type'] != 'LNINJA':
                try:
                    msg3 = ""
                    msg4 = ""
                    # Get the row of the player in the classification table.
                    player_row = classification_table[classification_table["player_id"] == player]
                    # # Get the position of the player in the classification table.
                    player_position = player_row["position"].values[0]
                    string_medal = ""
                    if player_position == 1:
                        string_medal = "🥇"
                    elif player_position == 2:
                        string_medal = "🥈"
                    elif player_position == 3:
                        string_medal = "🥉"
                    elif player_position <= 5:
                        string_medal = "🎖️"
                    elif player_position <= 10: # Use TOP emoji
                        string_medal = "🔝"
                    # Get the points of the player.
                    player_points = player_row["points"].values[0]
                    # Get the number of games played by the player.
                    player_games = player_row["total_games"].values[0]
                    # Get the number of wins of the player.
                    player_wins = player_row["total_wins"].values[0]
                    # Get the number of loses of the player.
                    player_loses = player_row["total_loses"].values[0]
                    # Get the number of null games of the player.
                    player_null = player_row["total_nulls"].values[0]
                    # Get the number of errors of the player.
                    player_errors = player_row["total_errors"].values[0]
                    

                    msg3 = f"{string_medal} Tu posición: {player_position}"
                    msg4 = f"🎮Partidas totales: {player_games}\n" \
                            f"✅Victorias: {player_wins}\n" \
                            f"❌Derrotas: {player_loses}\n" \
                            f"❔Partidas nulas: {player_null}\n" \
                            f"☠️ Partidas con errores: {player_errors}\n" \
                            f"🏆Puntos: {player_points}"

                except Exception as e:
                    print(f"Error computing classification of {player}. {e}")
                
                # # Send the message to the player.
                async with bot:
                    try:
                        await bot.send_message(chat_id=player, text=msg1)
                        await bot.send_message(chat_id=player, text=msg2)
                        await send_leaderboard(bot, player, player, chat_type='private')
                        if msg3 != "" and msg4 != "":
                            await bot.send_message(chat_id=player, text=msg3)
                            await bot.send_message(chat_id=player, text=msg4)
                    except Exception as e:
                        print(f"Error sending message to {player}. {e}")

            if all_players[player]['type'] != 'LNINJA':
                # La despedida :(
                async with bot:
                    try:
                        await bot.send_message(chat_id=player, text=msg_end)
                    except Exception as e:
                        print(f"Error sending message to {player}. {e}")

        for _, (group_id, thread_id) in notify_groups.items():
            async with bot:
                try:
                    await bot.send_message(chat_id=group_id, text=msg1, message_thread_id=thread_id)
                    await bot.send_message(chat_id=group_id, text=msg2, message_thread_id=thread_id)
                    await send_leaderboard(bot, group_id, "-104", chat_type='group', message_thread_id=thread_id)
                    await bot.send_message(chat_id=group_id, text=msg_end, message_thread_id=thread_id)
                except Exception as e:
                    print(f"Error sending message to {group_id}. {e}")

if __name__ == "__main__":
    asyncio.run(main())