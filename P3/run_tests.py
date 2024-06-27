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
import asyncio
from db_functions import *
# from utils import get_level4_blob

def get_level4_blob(points):
    if points <= 0:
        return "❌"
    elif points < 1:
        return "🔴"
    elif points < 2:
        return "🟠"
    elif points < 3:
        return "🟢"
    else:
        return "🔵"

def get_win_lose_error_emoji(result):
    if result == 'WIN':
        return "🟢"
    elif result == 'LOSE':
        return "🔴"
    elif result == 'ERROR':
        return "❌"
    else:
        return "🟠"
    

async def main():
    user_id = sys.argv[1]
    date = sys.argv[2]
    player = int(sys.argv[3])
    heuristic_id = sys.argv[4]
    ninja_id = sys.argv[5]
    job_id = sys.argv[6]

    key = ""
    if int(ninja_id) >= 1 and int(ninja_id) <= 3:
        if player == 1:
            key = f"J1vsN{ninja_id}"
        else:
            key = f"N{ninja_id}vsJ2"

    result = "C"

    TOKEN=__BOT_TOKEN__
    CHAT_ID=user_id

    bot = Bot(token=TOKEN)

    compile_error = not os.path.exists("ParchisGame")
    result_msg = ""
    error_msg = ""
    if not compile_error:
        # Create a dictionay to store the results.
        results = {}

        final_results = {}

        if player == 1:
            #cmd = f'./ParchisGame --p1 AI {heuristic_id} J1 --p2 LNinja {ninja_id} J2 --no-gui'
            cmd = ['./ParchisGame', '--p1', 'AI', heuristic_id, 'J1', '--p2', 'LNinja', ninja_id, 'J2', '--no-gui']
        else:
            #cmd = f'./ParchisGame --p1 LNinja {ninja_id} J1 --p2 AI {heuristic_id} J2 --no-gui'
            cmd = ['./ParchisGame', '--p1', 'LNinja', ninja_id, 'J1', '--p2', 'AI', heuristic_id, 'J2', '--no-gui']

        the_other_player = 1 if player == 2 else 2

        # Send the start message to the user.
        start_msg = f"[{date}] 🤖 JUGADOR {player} VS NINJA {ninja_id} (J{the_other_player}): ¡EMPIEZA LA PARTIDA! 🎲"
        async with bot:
            await bot.send_message(chat_id=CHAT_ID, text=start_msg)
        
        process = None
        timeout = False
        with open(f'output{player}-{heuristic_id}-{ninja_id}.txt', 'w') as f:
            process = subprocess.Popen(cmd, stdout=f, stderr=subprocess.PIPE)
            try:
                process.wait(timeout=3600)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                timeout = True
        
        if process.returncode != 0 or timeout:
            if not timeout:
                result_msg = f"[{date}] 🔴 JUGADOR {player} VS NINJA {ninja_id} (J{the_other_player}): ERROR"
                error_msg = process.stderr.read().decode('utf-8')
                result = "E"
            else:
                result_msg = f"[{date}] 🔴 JUGADOR {player} VS NINJA {ninja_id} (J{the_other_player}): TIMEOUT"
                error_msg = f"[{date}] 🕖 He tenido que cortar la partida porque llevaba más de una hora ejecutándose. Las partidas con los algoritmos pedidos no deberían tardar tanto en ningún caso. Revisa tu minimax o poda."
                result = "T"
        else:
            # Read the output starting from the end and find the line containing "Ha ganado el jugador {i} ({color})".
            result_line = ""
            with open(f'output{player}-{heuristic_id}-{ninja_id}.txt', 'r') as f:
                lines = f.readlines()
                for line in lines[::-1]:
                    if "Ha ganado el jugador" in line:
                        result_line = line
                        break

            if not result_line:
                result_msg = f"[{date}] 🔴 JUGADOR {player} VS NINJA {ninja_id} (J{the_other_player}): ERROR"
                error_msg = f"[{date}] ❌ La partida no ha terminado correctamente. No he sido capaz de averiguar el motivo, lo siento 😓"
                result = "F"
            else:
                # Get the winner and the color.
                winner = int(result_line.split("Ha ganado el jugador ")[1].split(" (")[0])
                color = result_line.split(" (")[1].split(")")[0]

                # Check that the color is Amarillo, Azul, Rojo or Verde.
                if color not in ["Amarillo", "Azul", "Rojo", "Verde"]:
                    result_msg = f"[{date}] 🔴 JUGADOR {player} VS NINJA {ninja_id} (J{the_other_player}): DERROTA/ERROR"
                    error_msg = f"[{date}] ❌ La partida no ha terminado correctamente. Es posible que hayas hecho algún movimiento ilegal o que tu jugador haya excedido el número de rebotes permitidos."
                    result = "L"
                else:
                    if winner == player:
                        result_msg = f"[{date}] 🟢 JUGADOR {player} VS NINJA {ninja_id} (J{the_other_player}): ¡VICTORIA! 🎉"
                        result = "W"
                    else:
                        result_msg = f"[{date}] 🔴 JUGADOR {player} VS NINJA {ninja_id} (J{the_other_player}): DERROTA... 😢"
                        result = "L"
                

        

        # Send the message to the user.
        async with bot:
            await bot.send_message(chat_id=CHAT_ID, text=result_msg)

        if error_msg:
            async with bot:
                await bot.send_message(chat_id=CHAT_ID, text=error_msg)

    else:
        message="❌ Ha habido un error. No se ha podido generar el ejecutable. Posiblemente haya habido un error de compilación con tu código."
        result = "C"

        async with bot:
            await bot.send_message(chat_id=CHAT_ID, text=message)

        # Send the file slurm_outputs/<job_id>.err to the user.
        with open(f"../../../../../slurm_outputs/{job_id}.err", "r") as f:
            try:
                async with bot:
                    await bot.send_document(chat_id=CHAT_ID, document=f, filename=f"error_log.txt", caption="Archivo de errores")
            except Exception as e:
                print(f"Error sending document: {e}")

    # Update the database.
    if key != "":
        update_P3_submission_metrics(user_id, date, key, result, db_path='../../../../../../IA_DB.db')



if __name__ == "__main__":
    asyncio.run(main())