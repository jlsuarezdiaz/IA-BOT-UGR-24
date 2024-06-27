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

__TESTS_MESSAGE_LIMIT__ = 40

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
    
def get_perc_blob(points):
    if points <= 0:
        return "❌"
    elif points < 50:
        return "🔴"
    elif points < 70:
        return "🟠"
    elif points < 85:
        return "🟢"
    elif points < 100:
        return "🔵"
    else:
        return "🏆"
    
def get_map_blob(points):
    if points <= 0:
        return "❌"
    elif points < 25:
        return "🔴"
    elif points < 50:
        return "🟠"
    elif points < 70:
        return "🟢"
    elif points < 85:
        return "🔵"
    else:
        return "🏆"
    

async def main():
    compile_error = not os.path.exists("practica1SG")
    if not compile_error:
        # Create a dictionay to store the results.
        results = {}

        stealth_argv = sys.argv[4]
        stealth = int(stealth_argv) == 1

        # Read the tests.json file.
        with open('tests.json') as f:
            tests = json.load(f)

            # Group the tests by levels.
            levels = {}
            for key, test in tests.items():
                level = test['level']
                if level not in levels:
                    levels[level] = []
                levels[level].append(key)

            
            for level in range(4):
                results[level] = {}
                if level in levels:
                    for key in levels[level]:
                        timeout = False
                        test = tests[key]
                        print(f"Running test {key}...")
                        # Call the test['command']. If there is an error, notify it.
                        cmd = test['command'].split(' ')
                        process = None
                        with open(f'output{level}{key}.txt', 'w') as f:
                            process = subprocess.Popen(cmd, stdout=f, stderr=subprocess.PIPE)
                            try:
                                process.wait(timeout=400)
                            except subprocess.TimeoutExpired:
                                process.kill()
                                process.wait()
                                timeout = True
                        
                        if process.returncode != 0 or timeout:
                            results[level][key] = {
                                'type': test['type'],
                                'error': process.stderr.read().decode('utf-8') if not timeout else 'TIMEOUT'
                            }
                        else:
                            output = None
                            os.system(f'cat output{level}{key}.txt | tail -n 20 > output{level}{key}s.txt')
                            with open(f'output{level}{key}s.txt', 'r') as f:
                                output = f.read()
                
                            try:
                                # Get the integer value {cons} from the output line "Instantes de simulacion no consumidos: {cons}".
                                cons = int(output.split('Instantes de simulacion no consumidos: ')[1].split('\n')[0])
                                # Get the float value {time} from the output line "Tiempo Consumido: {time}".
                                time = float(output.split('Tiempo Consumido: ')[1].split('\n')[0])
                                # Get the integer value {bat} from the output line "Nivel Final de Bateria: {bat}".
                                bat = int(output.split('Nivel Final de Bateria: ')[1].split('\n')[0])
                                # Get the integer value {col} from the output line "Colisiones: {col}".
                                col = int(output.split('Colisiones: ')[1].split('\n')[0])
                                # Get the integer value {emp} from the output line "Empujones: {emp}".
                                emp = int(output.split('Reinicios: ')[1].split('\n')[0])
                                # Get the float value {porc} from the output line "Porcentaje de mapa descubierto: {porc_pos}".
                                porc_pos = float(output.split('Porcentaje de mapa descubierto: ')[1].split('\n')[0])
                                # Get the true value {porc} penalyzing errors from the output line "Porcentaje de mapa descubierto restando errores: {porc}".
                                porc = float(output.split('Porcentaje de mapa descubierto restando errores: ')[1].split('\n')[0])

                                # Store the results.
                                results[level][key] = {
                                    'type': test['type'],
                                    'time': time,
                                    'bat': bat,
                                    'col': col,
                                    'emp': emp,
                                    'porc_pos': porc_pos,
                                    'porc': max(0, porc),
                                    'cons': cons
                                }
                            except:
                                results[level][key] = {
                                    'type': test['type'],
                                    'error': 'Error parsing the output file. Unexpected output:' + output
                                }

                        # Summarize the results.
                        results[level][key]['summary'] = {
                            'error': True if 'error' in results[level][key] else False,
                            'timeout': True if timeout else False,
                            'discovered': results[level][key]['porc'] if not 'error' in results[level][key] else None,
                            'discovered_abs': results[level][key]['porc_pos'] if not 'error' in results[level][key] else None,
                            'end': "ERR" if 'error' in results[level][key] else "BAT" if results[level][key]['bat'] == 0 else 
                                   "INST" if results[level][key]['cons'] == 0 else
                                   "TIME" if results[level][key]['time'] > 300 else "???"
                        }
                        results[level][key]['summary']['netos'] = max(results[level][key]['summary']['discovered'] / 100, 0) if not 'error' in results[level][key] else -0.1
                        map_size = test["map_size"]
                        # tot_casillas = map_size[0] * map_size[1]
                        results[level][key]['summary']['s'] = min(1.0, results[level][key]['summary']['netos'] / (0.85)) if not 'error' in results[level][key] else -0.1

            # Create a message with the results.
            message_intro = "✅ La ejecución ha terminado.\n\n"
            message_intro += "📊 Resultados:\n"
            message_intro += "0️⃣1️⃣2️⃣3️⃣ | Estimación Global (sobre 10)\n"

            # Average the results per level using 's' as the metric.
            level_avgs = {}
            results["final"] = {}
            for level in range(4):
                if level in results:
                    level_avgs[level] = sum([x['summary']['s'] for x in results[level].values()]) / len(results[level])
                    results["final"][level] = {
                        "avg": level_avgs[level]
                    }
                    message_intro += f"{get_perc_blob(level_avgs[level] * 100)}"

            # Compute the global results.
            level_points = {0: 2, 1: 3, 2: 2, 3: 3}
            global_points = sum([level_points[i] * level_avgs[i] for i in range(4)])
            results["final"]["global"] = {
                "avg": global_points
            }
            message_intro += f" | {global_points:.3f} {get_perc_blob(global_points * 10)}\n\n"

            message_legend = """Leyenda:
            🗺 - Problema
            🤖 - Total descubierto (restando errores)
            👽 - ¿Coincide con total descubierto? (Es decir, ¿no hay casillas mal escritas?) 👍|👎
            🏁 - Motivo de finalización:
                - 🪫: Batería agotada.
                - ⏳: Instantes de simulación agotados.
                - ⏱: Tiempo agotado.
                - ❌: Error.
            👀 - Valoración del mapa.
            💯 - Puntuación del mapa en la práctica (s_i, sobre 1)
            ⚠️ - Mensajes de error (si hubiera, si hay error pero no ningún mensaje lo más probable es que se haya producido un core).
            """

            # Detailed results for each level.
            msg_levels = {}
            for level in range(4):
                nmessages = len(results[level]) // __TESTS_MESSAGE_LIMIT__ + 1
                msg_levels[level] = []
                for i in range(nmessages):
                    if i == 0:
                        msg_levels[level].append(f"*Resultados del nivel {level}*:\n")
                    else:
                        msg_levels[level].append(f"*Resultados del nivel {level} (parte {i + 1})*:\n")
                    msg_levels[level][i] += "️```\n"
                    msg_levels[level][i] += f" 🗺 |   🤖   | 👽 | 🏁 | 👀 | 💯 | ⚠️\n"
                    msg_levels[level][i] += "-----------------------------------\n"
                for line, (key, res) in enumerate(results[level].items()):
                    summary = res['summary']
                    moti = summary['end']
                    moti_emoji = "🪫" if moti == "BAT" else "⏳" if moti == "INST" else "⏱" if moti == "TIME" else "❌"
                    disc = summary['discovered'] if summary['discovered'] is not None else 0.0
                    disc_abs = summary['discovered_abs'] if summary['discovered_abs'] is not None else 0.0
                    coinciden = "👍" if disc == disc_abs else "👎" if summary['discovered'] is not None else "❌"
                    s_i = res['summary']['s']
                    msg_levels[level][line // __TESTS_MESSAGE_LIMIT__] += f"{key} | {disc:05.2f}% | {coinciden} | {moti_emoji} | {get_map_blob(disc)} | {s_i:.2f} | {res['error'] if 'error' in res else ''}\n"
                
                for i in range(nmessages):
                    msg_levels[level][i] += "️```\n"

            # Save the results and summaries.
            # First get the path.
            timestamp = sys.argv[2]
            # Path is ../results/<timestamp>/results.json and ../results/<timestamp>/summary.json
            # Create all the folders if they don't exist.
            os.makedirs(os.path.dirname(f"../results/{timestamp}/"), exist_ok=True)
            # Save the results.
            with open(f"../results/{timestamp}/results.json", 'w') as f:
                json.dump(results, f)
        
            # Save the submission in the database.
            user_id = sys.argv[1]
            db_path = '../../../../IA_DB.db'
            
            insert_submission(user_id, timestamp, os.path.abspath(f"../results/{timestamp}/results.json"), db_path=db_path, public=not stealth)
            insert_submission_metrics(user_id, timestamp, *compute_metrics(results, tests), db_path=db_path)
        
        message_leaderboard = ""
        if not stealth:
            # Get the user classification.
            user_classification = get_user_classification(user_id, db_path=db_path)
            # If it was its first upload
            if user_classification['total_submissions'] == 1:
                message_leaderboard += "💙 ¡Gracias por participar por primera vez! Tu resultado se ha subido a la /leaderboard, consúltala para ver tu posición."
            # If it was its best upload
            elif user_classification['total_submissions'] == user_classification['id_submission']:
                message_leaderboard += "🏆 ¡Has superado tu mejor resultado, enhorabuena! Tu puntuación ha sido actualizada en la /leaderboard, consúltala para ver tu posición."
            # If it was not its best upload
            else:
                message_leaderboard += "🤕 ¡Buen intento, aunque no has superado tu mejor resultado en la /leaderboard! ¡Sigue intentándolo!"
            string_medal = ""
            player_position = user_classification['position']
            if player_position == 1:
                string_medal = "🥇"
            elif player_position == 2:
                string_medal = "🥈"
            elif player_position == 3:
                string_medal = "🥉"
            elif player_position <= 5:
                string_medal = "🎖"
            elif player_position <= 10:
                string_medal = "🔝"
            message_leaderboard += f"\n\n{string_medal} Tu posición actual: {player_position}."
        
        #message_leaderboard = "⚠️🛠 Estamos completando los tests para el bot. La leaderboard no estará disponible temporalmente. Volverá a estar en funcionamiento cuando estén los tests definitivos. De momento puedes seguir consultando los resultados de los tests."
        
        # Send the message to the user.
        user_id = sys.argv[1]

        TOKEN=__BOT_TOKEN__
        CHAT_ID=user_id

        # Create a bot and send the message.
        bot = Bot(token=TOKEN)

        async with bot:
            await bot.send_message(chat_id=CHAT_ID, text=message_intro)
            await bot.send_message(chat_id=CHAT_ID, text=message_legend)
            # Send the level results as monospace (with markdown V2).
            for level in range(4):
                for msg in msg_levels[level]:
                    message = msg.replace(".", "\.").replace("(","\(").replace(")","\)")
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)

            if not stealth:
                await bot.send_message(chat_id=CHAT_ID, text=message_leaderboard)

    else:
        # Get the first command line argument.
        user_id = sys.argv[1]
        job_id = sys.argv[3]

        TOKEN=__BOT_TOKEN__
        CHAT_ID=user_id

        # Create a bot and send the message.
        bot = Bot(token=TOKEN)

        async with bot:
            message="❌ Ha habido un error. No se ha podido generar el ejecutable. Posiblemente haya habido un error de compilación con tu código."

            await bot.send_message(chat_id=CHAT_ID, text=message)

            # Send the file slurm_outputs/<job_id>.err to the user.
            with open(f"../../../slurm_outputs/{job_id}.err", 'r') as f:
                await bot.send_document(chat_id=CHAT_ID, document=f, filename=f"error_log.txt", caption="Archivo de errores")

        #message="❌ Ha habido un error. No se ha podido generar el ejecutable. Posiblemente haya habido un error de compilación con tu código."

        #url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
        #print(requests.get(url).json())

if __name__ == "__main__":
    asyncio.run(main())