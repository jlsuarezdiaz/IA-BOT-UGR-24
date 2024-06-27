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
from filelock import FileLock
import pandas as pd
import time
import random
from db_functions import *
import asyncio

async def main():
    P1_ID = int(sys.argv[1])
    P2_ID = int(sys.argv[2])
    DATE = sys.argv[3]

    bot = Bot(__BOT_TOKEN__)

    # # cd to "tournament-results/{DATE}" folder
    # os.chdir("tournament-results/" + DATE)

    # # Read the metadata.json file and store the information in a dictionary.
    # with open("metadata.json") as f:
    #     metadata = json.load(f)

    # Get P1 and P2 metadata.
    # print current directory
    all_players = get_P3_tour_players_date(date=DATE, db_path="../IA_DB.db")
    p1_metadata = all_players[P1_ID]
    p2_metadata = all_players[P2_ID]

    os.chdir("./tour-executions")

    # Start the server battle (P1 will be hosting).
    compile_error_p1 = not os.path.exists(f"{P1_ID}/ParchisGame")
    compile_error_p2 = not os.path.exists(f"{P2_ID}/ParchisGame")

    timeout = False

    if not compile_error_p1 and not compile_error_p2:
        # Range of ports to use.
        ports = list(range(49162, 65535))
        # Choose the first port to use randomly.
        current_port_id = random.randint(0, len(ports) - 1)

        game_started = False
        while not game_started:
            # Get the port to use.
            port = ports[current_port_id]
            current_port_id = (current_port_id + 1) % len(ports)

            print(f"Trying port {port}...")

            # ./$P1_ID/ParchisGame --server $player_type1 $heuristica1 J1 --port $port --no-gui &
            # Run the program.
            cmd = [f'./{P1_ID}/ParchisGame', '--server', p1_metadata['type'], str(p1_metadata['heuristic']), p1_metadata['alias'], '--port', str(port), '--no-gui']
            
            with open(f'output-{P1_ID}-{P2_ID}-server.txt', 'w') as f:
                process_server = subprocess.Popen(cmd, stdout=f, stderr=subprocess.PIPE)
                # Wait 10 seconds. If the process has ended before, it means that the port is already in use.
                time.sleep(10)
                if process_server.poll() is None:
                    game_started = True
                    print(f"Game started on port {port}.")
                    # ./$P2_ID/ParchisGame --p1 Remote 0 J1 --p2 AI $heuristica2 J2 --ip localhost --port $port --no-gui
                    # Notify the users that the game has started.
                    msg = f"🎲 ¡COMIENZA LA BATALLA! J1: {p1_metadata['alias']} vs J2: {p2_metadata['alias']}"
                    if 'notify' in p1_metadata and p1_metadata['notify'] == 2 and p1_metadata['type'] != 'LNINJA':
                        try:
                            async with bot:
                                await bot.send_message(chat_id=P1_ID, text=msg)
                        except:
                            print("Error sending message to P1.")
                    if 'notify' in p2_metadata and p2_metadata['notify'] == 2 and p2_metadata['type'] != 'LNINJA':
                        try:
                            async with bot:
                                await bot.send_message(chat_id=P2_ID, text=msg)
                        except:
                            print("Error sending message to P2.")
                    # Run the client.
                    cmd = [f'./{P2_ID}/ParchisGame', '--p1', 'Remote', '0', p1_metadata['alias'], '--p2', p2_metadata['type'], str(p2_metadata['heuristic']), p2_metadata['alias'], '--ip', 'localhost', '--port', str(port), '--no-gui']
                    with open(f'output-{P1_ID}-{P2_ID}-client.txt', 'w') as f:
                        process_client = subprocess.Popen(cmd, stdout=f, stderr=subprocess.PIPE)
                        try:
                            process_client.wait(timeout=3600)
                            process_server.wait(timeout=3600)
                        except subprocess.TimeoutExpired:
                            process_client.kill()
                            process_server.kill()
                            process_client.wait()
                            process_server.wait()
                            timeout = True
        
    # Open with lock "./tournament-results/" + current_date + "/battle_results.csv" as pd.DataFrame
    # os.chdir("../tournament-results/" + DATE)
    battle_result = None

    #with FileLock("battle_results.csv.lock"):
    #results = pd.read_csv("battle_results.csv")
    battle_result = {'player1_id': P1_ID,
                    'player2_id': P2_ID,
                    'player1_name': p1_metadata['name'],
                    'player2_name': p2_metadata['name'],
                    'player_winner': None,
                    'winner': 0,
                    'player1_error': None,
                    'player2_error': None,
                    'timeout': timeout}

    if compile_error_p1 or compile_error_p2:
        battle_result['player1_error'] = 'Compile error' if compile_error_p1 else None
        battle_result['player2_error'] = 'Compile error' if compile_error_p2 else None
        if compile_error_p1 and not compile_error_p2:
            battle_result['winner'] = 2
            battle_result['player_winner'] = P2_ID
        elif not compile_error_p1 and compile_error_p2:
            battle_result['winner'] = 1
            battle_result['player_winner'] = P1_ID
    else:
        if process_server.returncode != 0:
            battle_result['player1_error'] = process_server.stderr.read().decode('utf-8')
        if process_client.returncode != 0:
            battle_result['player2_error'] = process_client.stderr.read().decode('utf-8')
        if process_server.returncode != 0 and process_client.returncode == 0:
            battle_result['winner'] = 2
            battle_result['player_winner'] = P2_ID
        elif process_server.returncode == 0 and process_client.returncode != 0:
            battle_result['winner'] = 1
            battle_result['player_winner'] = P1_ID
        elif process_server.returncode == 0 and process_client.returncode == 0:
            # Read the output starting from the end and find the line containing "Ha ganado el jugador {i} ({color})".
            result_line_server = ""
            disconnect_server = False
            with open(f'output-{P1_ID}-{P2_ID}-server.txt', 'r') as f:
                lines = f.readlines()
                for line in lines[::-1]:
                    if "Ha ganado el jugador" in line:
                        result_line_server = line
                    if "400 ERROR_DISCONNECTED" in line:
                        disconnect_server = True

            result_line_client = ""
            disconnect_client = False
            with open(f'output-{P1_ID}-{P2_ID}-client.txt', 'r') as f:
                lines = f.readlines()
                for line in lines[::-1]:
                    if "Ha ganado el jugador" in line:
                        result_line_client = line
                    if "400 ERROR_DISCONNECTED" in line:
                        disconnect_client = True

            print("Server: ", result_line_server)
            print("Client: ", result_line_client)
            print("Disconnect server: ", disconnect_server)
            print("Disconnect client: ", disconnect_client)

            if not result_line_server:
                battle_result['player1_error'] = "Partida no terminada (motivos desconocidos)"
            if not result_line_client:
                battle_result['player2_error'] = "Partida no terminada (motivos desconocidos)"
            if not result_line_server and result_line_client:
                battle_result['winner'] = 2
                battle_result['player_winner'] = P2_ID
            elif result_line_server and not result_line_client:
                battle_result['winner'] = 1
                battle_result['player_winner'] = P1_ID
            elif result_line_server and result_line_client:
                winner_server = int(result_line_server.split("Ha ganado el jugador ")[1].split(" (")[0])
                winner_client = int(result_line_client.split("Ha ganado el jugador ")[1].split(" (")[0])
                if winner_server == 1 and winner_client == 1:
                    battle_result['winner'] = 1
                    battle_result['player_winner'] = P1_ID
                elif winner_server == 2 and winner_client == 2:
                    battle_result['winner'] = 2
                    battle_result['player_winner'] = P2_ID
                else:
                    #battle_result['player1_error'] = "Error desconocido: no se pudo determinar el ganador."
                    #battle_result['player2_error'] = "Error desconocido: no se pudo determinar el ganador."
                    if disconnect_client and not disconnect_server:
                        if winner_server == 1:
                            battle_result['winner'] = 1
                            battle_result['player_winner'] = P1_ID
                        elif winner_server == 2:
                            battle_result['winner'] = 2
                            battle_result['player_winner'] = P2_ID
                    elif disconnect_server and not disconnect_client:
                        if winner_client == 1:
                            battle_result['winner'] = 1
                            battle_result['player_winner'] = P1_ID
                        elif winner_client == 2:
                            battle_result['winner'] = 2
                            battle_result['player_winner'] = P2_ID
                    else:
                        battle_result['player1_error'] = "Error desconocido: no se pudo determinar el ganador."
                        battle_result['player2_error'] = "Error desconocido: no se pudo determinar el ganador."

    # Save the battle_result to battle_results/$P1_ID-$P2_ID.json
    # with open(f"battle_results/{P1_ID}-{P2_ID}.json", "w") as f:
    #     json.dump(battle_result, f, indent=4)

    # Submit the result to the database.
    submitted_ok = False
    while not submitted_ok:
        try:
            insert_P3_tournament_battle(DATE, P1_ID, P2_ID, battle_result['winner'], battle_result['player1_error'] is not None, battle_result['player2_error'] is not None, battle_result['timeout'], db_path="../../IA_DB.db")
            submitted_ok = True
        except Exception as e:
            print("Error submitting battle result to the database. Retrying...")
            print(e)
            submitted_ok = False
            time.sleep(5)
    
    #results = results.append(battle_result, ignore_index=True)
    #results.to_csv("battle_results.csv", index=False)

    # Notify the players with the result.
    msg = ""
    if 'notify' in p1_metadata and p1_metadata['notify'] == 2 and p1_metadata['type'] != 'LNINJA':
        if battle_result['winner'] == 1:
            msg = f"🟢 J1: {p1_metadata['alias']} vs J2: {p2_metadata['alias']}: ¡Has ganado!"
        elif battle_result['winner'] == 2:
            if battle_result['player1_error']:
                msg = f"💀 J1: {p1_metadata['alias']} vs J2: {p2_metadata['alias']}: Tu programa ha fallado: {battle_result['player1_error']}"
            else:
                msg = f"🔴 J1: {p1_metadata['alias']} vs J2: {p2_metadata['alias']}: Has perdido..."
        else:
            msg = f"🟠 J1: {p1_metadata['alias']} vs J2: {p2_metadata['alias']}: Partida nula. Posibles errores: {battle_result['player1_error']}, {battle_result['player2_error']}"

        try:
            async with bot:
                await bot.send_message(chat_id=P1_ID, text=msg)
        except:
            print("Error sending message to P1.")

    if 'notify' in p2_metadata and p2_metadata['notify'] == 2 and p2_metadata['type'] != 'LNINJA':
        if battle_result['winner'] == 2:
            msg = f"🟢 J1: {p1_metadata['alias']} vs J2: {p2_metadata['alias']}: ¡Has ganado!"
        elif battle_result['winner'] == 1:
            if battle_result['player2_error']:
                msg = f"💀 J1: {p1_metadata['alias']} vs J2: {p2_metadata['alias']}: Tu programa ha fallado: {battle_result['player2_error']}"
            else:
                msg = f"🔴 J1: {p1_metadata['alias']} vs J2: {p2_metadata['alias']}: Has perdido..."
        else:
            msg = f"🟠 J1: {p1_metadata['alias']} vs J2: {p2_metadata['alias']}: Partida nula. Posibles errores: {battle_result['player1_error']}, {battle_result['player2_error']}"

        try:
            async with bot:
                await bot.send_message(chat_id=P2_ID, text=msg)
        except:
            print("Error sending message to P2.")

if __name__ == "__main__":
    asyncio.run(main())