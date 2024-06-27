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
    
def get_level4_points(punt, test):
    umbral1 = test['umbral1']
    umbral2 = test['umbral2']
    umbral3 = test['umbral3']

    if punt < umbral1:
        return punt / umbral1
    elif punt < umbral2:
        return (punt - umbral1) / (umbral2 - umbral1) + 1
    elif punt < umbral3:
        return (punt - umbral2) / (umbral3 - umbral2) + 2
    else:
        return 3 + (punt - umbral3) / (umbral3)

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
    user_id = sys.argv[1]
    timestamp = sys.argv[2]
    job_id = sys.argv[3]
    stealth_argv = sys.argv[4]
    stealth = int(stealth_argv) == 1
    eval_levels = sys.argv[5:]
    eval_levels = [int(level) for level in eval_levels]
    db_path = '../../../../IA_DB.db'
    compile_error = not os.path.exists("practica2SG")
    if not compile_error:
        TOKEN=__BOT_TOKEN__
        CHAT_ID=user_id

        # Create a bot and send the message.
        bot = Bot(token=TOKEN)

        async with bot:
            try:
                await bot.send_message(chat_id=CHAT_ID, text="🔧 La compilación ha terminado correctamente. Comienzan las ejecuciones...")
            except Exception as e:
                print(f"Error sending message: {e}")

        # Create a dictionay to store the results.
        results = {}

        # Read the tests.json file.
        with open('tests.json') as f:
            tests = json.load(f)

            # Group the tests by levels.
            levels = {}
            for key, test in tests.items():
                if test['type'] != 'eval':
                    level = test['level']
                    if level not in levels:
                        levels[level] = []
                    levels[level].append(key)

            
            for level in eval_levels:
                results[level] = {}
                if level in levels:
                    for key in levels[level]:
                        timeout = False
                        test = tests[key]
                        print(f"Running test {key}...")
                        if get_P2_user_notifications(user_id, db_path=db_path) == 1:
                            async with bot:
                                try:
                                    await bot.send_message(chat_id=CHAT_ID, text=f"🧪 Ejecutando test {key}...")
                                except Exception as e:
                                    print(f"Error sending message: {e}")
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
                                emp = int(output.split('Empujones: ')[1].split('\n')[0])
                                # Get the float value {porc} from the output line "Porcentaje de mapa descubierto: {porc_pos}".
                                porc = float(output.split('Porcentaje de mapa descubierto: ')[1].split('\n')[0])
                                # Get the integer values {obj} and {punt} from the output line "Objetivos encontrados: ({obj}) {punt}"
                                obj = int(output.split('Objetivos encontrados: (')[1].split(') ')[0])
                                punt = int(output.split('Objetivos encontrados: (')[1].split(') ')[1].split('\n')[0])
                                # Get if the agent has be rested. Look for the text "Se cayó por un precipicio"
                                reset = output.find("Se cayó por un precipicio") != -1
                                # Get if the objective has be reached by the CLB.
                                obj_clb = output.find("Casilla Objetivo alcanzada por el colaborador") != -1
                                # Get if the objective has been reached by the JUG
                                obj_jug = output.find("Casilla objetivo alcanzada por el jugador") != -1
                                # Store the results.
                                results[level][key] = {
                                    'type': test['type'],
                                    'time': time,
                                    'bat': bat,
                                    'col': col,
                                    'emp': emp,
                                    'porc': max(0, porc),
                                    'cons': cons,
                                    'obj': obj,
                                    'punt': punt,
                                    'reset': reset,
                                    'obj_jug': obj_jug,
                                    'obj_clb': obj_clb
                                }

                                level_alerts = []
                                if level < 4:
                                    if results[level][key]['cons'] not in test['valid_instantes']:
                                        if level >= 2 and results[level][key]['bat'] in test['valid_battery']:
                                            level_alerts.append("NEWPATH")
                                        elif level <= 1:
                                            level_alerts.append("INST")
                                    if results[level][key]['bat'] not in test['valid_battery']:
                                        if level <= 1 and results[level][key]['cons'] in test['valid_instantes']:
                                            level_alerts.append("NEWPATH")
                                        elif level >= 2:
                                            level_alerts.append("BAT")
                                    if results[level][key]['col'] not in test['valid_cols']:
                                        level_alerts.append("COL")
                                    #if results[level][key]['obj'] not in test['valid_objs']:
                                    #    level_alerts.append("OBJ")
                                    if (level == 0 or level == 2) and not (results[level][key]['obj_jug']):
                                        level_alerts.append("OBJ")
                                    if (level == 1 or level == 3) and not (results[level][key]['obj_clb']):
                                        level_alerts.append("OBJ")
                                    if results[level][key]['time'] < test['valid_time'][0] and ("INST" in level_alerts or "BAT" in level_alerts or "COL" in level_alerts):
                                        level_alerts.append("TIME-")
                                    if results[level][key]['time'] > test['valid_time'][1]:
                                        level_alerts.append("TIME+")
                                    if results[level][key]['reset']:
                                        level_alerts.append("RESET")
                            except:
                                results[level][key] = {
                                    'type': test['type'],
                                    'error': 'Error parsing the output file. Unexpected output:' + output
                                }
                                level_alerts = []

                            

                        # Summarize the results.
                        results[level][key]['summary'] = {
                            'error': True if 'error' in results[level][key] else False,
                            'timeout': True if timeout else False,
                            'discovered': results[level][key]['porc'] if not 'error' in results[level][key] else None,
                            'end': "ERR" if 'error' in results[level][key] else "BAT" if results[level][key]['bat'] == 0 else 
                                   "INST" if results[level][key]['cons'] == 0 else
                                   "TIME" if results[level][key]['time'] > 300 else
                                   "OBJ" if (results[level][key]['obj_jug'] and level in [0, 2]) or (results[level][key]['obj_clb'] and level in [1, 3]) else
                                   "RESET" if results[level][key]['reset'] else "???",
                            'level_alerts': level_alerts,
                            
                        }

                        if level < 4:
                            if 'timeout' in results[level][key]:
                                results[level][key]['summary']['test_points'] = 'timeout'
                            elif 'error' in results[level][key]:
                                results[level][key]['summary']['test_points'] = 'error'
                            elif len(level_alerts) > 0:
                                if 'INST' in level_alerts or 'BAT' in level_alerts or 'OBJ' in level_alerts or 'RESET' in level_alerts:
                                    results[level][key]['summary']['test_points'] = 'fail'
                                elif 'TIME-' in level_alerts or 'TIME+' in level_alerts or 'COL' in level_alerts or 'OBJ' in level_alerts:
                                    results[level][key]['summary']['test_points'] = 'warning'
                                else:
                                    results[level][key]['summary']['test_points'] = 'info'    
                            else:
                                results[level][key]['summary']['test_points'] = 'ok'
                            
                        else:
                            if 'timeout' in results[level][key]:
                                results[level][key]['summary']['points'] = 0
                                results[level][key]['summary']['test_points'] = -0.1
                            elif 'error' in results[level][key]:
                                results[level][key]['summary']['points'] = 0
                                results[level][key]['summary']['test_points'] = -0.1
                            else:
                                results[level][key]['summary']['points'] = results[level][key]['punt']
                                results[level][key]['summary']['test_points'] = get_level4_points(results[level][key]['punt'], test)
                        # tot_casillas = map_size[0] * map_size[1]

            # Create a message with the results.
            message_intro = "✅ La ejecución ha terminado.\n\n"
            message_intro += "📊 Resultados:\n"
            message_intro += "0️⃣1️⃣2️⃣3️⃣ | Estimación Nivel 4\n"

            # Average the results per level.
            level_avgs = {}
            results["final"] = {}
            for level in range(4):
                if level in results:
                    total_oks = len([key for key in results[level] if results[level][key]['summary']['test_points'] == 'ok' or results[level][key]['summary']['test_points'] == 'info'])
                    total_warnings = len([key for key in results[level] if results[level][key]['summary']['test_points'] == 'warning'])
                    total_fails = len([key for key in results[level] if results[level][key]['summary']['test_points'] == 'fail' or results[level][key]['summary']['test_points'] == 'error' or results[level][key]['summary']['test_points'] == 'timeout'])
                    total_tests = total_oks + total_warnings + total_fails

                    if total_oks == total_tests:
                        level_avgs[level] = 'ok'
                    elif total_warnings > 0 and total_warnings + total_fails < total_tests:
                        level_avgs[level] = 'warning'
                    else:
                        level_avgs[level] = 'fail'

                    level_emoji = "✅" if level_avgs[level] == 'ok' else "⚠️" if level_avgs[level] == 'warning' else "❌"
                    
                    results["final"][level] = {
                        "avg": level_avgs[level]
                    }
                    message_intro += f"{level_emoji}"
                else:
                    message_intro += "❔"

            for level in [4]:
                if level in results:
                    level_avgs[level] = sum([results[level][key]['summary']['test_points'] for key in results[level]]) / len(results[level])
                    level_emoji = get_level4_blob(level_avgs[level])
                    results["final"][level] = {
                        "avg": level_avgs[level]
                    }
                    message_intro += f" | {level_avgs[level]:.3f} / 3 {level_emoji}"
                else:
                    message_intro += " | ❔"


            message_legend = """Leyenda:
            🗺 - Problema
            🏁 - Motivo de finalización:
                - 🪫: Batería agotada.
                - ⏳: Instantes de simulación agotados.
                - ⏱: Tiempo agotado.
                - ❌: Error.
                - 🎯: Casilla objetivo alcanzada.
                - ☠️: Agente caído por un precipicio.
            🔎 - Análisis del problema (solo hasta nivel 3):
                ✅ - Todo correcto.
                ℹ️ - ¡Has encontrado un nuevo camino que no tenía en mi base de datos!
                💨 - Tu algoritmo ha tardado demasiado poco tiempo. ¿Quizás no estás desarrollando bien el árbol de búsqueda?
                🕰 - Tu algoritmo ha tardado demasiado tiempo. ¿Quizás no estás controlando bien los nodos repetidos?
                ❌ - La ejecución no termina con el número de acciones (nivel 0-1,) o el nivel de batería (nivel 2-3) correcto, o ha terminado con error.
                🚫 - No has llegado a la casilla objetivo.
                🤕 - Tu agente se ha chocado.
                ☠️ - Tu agente se ha caído por un precipicio.
            💯 - Puntuación (nivel 4):
            
            ⚠️ - Mensajes de error (si hubiera, si hay error pero no ningún mensaje lo más probable es que se haya producido un core).
            """

            # Detailed results for each level.
            msg_levels = {}
            for level in range(4):
                if level in results:
                    nmessages = len(results[level]) // __TESTS_MESSAGE_LIMIT__ + 1
                    msg_levels[level] = []
                    for i in range(nmessages):
                        if i == 0:
                            msg_levels[level].append(f"*Resultados del nivel {level}*:\n")
                        else:
                            msg_levels[level].append(f"*Resultados del nivel {level} (parte {i + 1})*:\n")
                        msg_levels[level][i] += "️```\n"
                        msg_levels[level][i] += f" 🗺 | 🏁 |   🔎   | ⚠️"
                        msg_levels[level][i] += "\n-----------------------------------\n"
                    for line, (key, res) in enumerate(results[level].items()):
                        summary = res['summary']
                        moti = summary['end']
                        moti_emoji = "🪫" if moti == "BAT" else "⏳" if moti == "INST" else "⏱" if moti == "TIME" else "🎯" if moti == "OBJ" else "☠️" if moti == "RESET" else "❌"
                        
                        level_alerts = summary['level_alerts']
                        alerts_str = ""
                        if len(level_alerts) > 0:
                            if 'NEWPATH' in level_alerts and not 'error' in res and not 'timeout' in res:
                                alerts_str += "ℹ️"
                            if 'TIME-' in level_alerts:
                                alerts_str += "💨"
                            if 'TIME+' in level_alerts:
                                alerts_str += "🕰"
                            if 'INST' in level_alerts:
                                alerts_str += "❌"
                            if 'BAT' in level_alerts:
                                alerts_str += "❌"
                            if 'COL' in level_alerts:
                                alerts_str += "🤕"
                            if 'OBJ' in level_alerts:
                                alerts_str += "🚫"
                            if 'RESET' in level_alerts:
                                alerts_str += "☠️"
                        elif 'error' in res or 'timeout' in res:
                            alerts_str += "❌"
                        else:
                            alerts_str += "✅"
                        
                        msg_levels[level][line // __TESTS_MESSAGE_LIMIT__] += f"{key:<3} | {moti_emoji} | {alerts_str} | {res['error'] if 'error' in res else ''}\n"
                    
                    for i in range(nmessages):
                        msg_levels[level][i] += "️```\n"

            for level in [4]:
                if level in results:
                    nmessages = len(results[level]) // __TESTS_MESSAGE_LIMIT__ + 1
                    msg_levels[level] = []
                    for i in range(nmessages):
                        if i == 0:
                            msg_levels[level].append(f"*Resultados del nivel {level}*:\n")
                        else:
                            msg_levels[level].append(f"*Resultados del nivel {level} (parte {i + 1})*:\n")
                        msg_levels[level][i] += "️```\n"
                        msg_levels[level][i] += f" 🗺 | 🏁 |        💯        | ⚠️"
                        msg_levels[level][i] += "\n-----------------------------------\n"
                    for line, (key, res) in enumerate(results[level].items()):
                        summary = res['summary']
                        moti = summary['end']
                        moti_emoji = "🪫" if moti == "BAT" else "⏳" if moti == "INST" else "⏱" if moti == "TIME" else "🎯" if moti == "OBJ" else "☠️" if moti == "RESET" else "❌"
                        
                        
                        msg_levels[level][line // __TESTS_MESSAGE_LIMIT__] += f"{key:<3} | {moti_emoji} | {get_level4_blob(summary['test_points'])} {summary['points']:<3} pts. ({summary['test_points']:.3f} / 3) | {res['error'] if 'error' in res else ''}\n"

                    for i in range(nmessages):
                        msg_levels[level][i] += "️```\n"

            # Save the results and summaries.
            # First get the path.
            
            # Path is ../results/<timestamp>/results.json and ../results/<timestamp>/summary.json
            # Create all the folders if they don't exist.
            os.makedirs(os.path.dirname(f"../results/{timestamp}/"), exist_ok=True)
            # Save the results.
            with open(f"../results/{timestamp}/results.json", 'w') as f:
                json.dump(results, f)
        
            # Save the submission in the database.
            good_enough_lb_result = results["final"][4]['avg'] > 0.1 if 4 in results else False
            upload_to_lb = not stealth and good_enough_lb_result
            
            insert_P2_submission(user_id, timestamp, os.path.abspath(f"../results/{timestamp}/results.json"), db_path=db_path, public=upload_to_lb)
            insert_P2_submission_metrics3(user_id, timestamp, *compute_P2_metrics3(results, tests), db_path=db_path)
            if 4 in results:
                insert_P2_submission_metrics4(user_id, timestamp, *compute_P2_metrics4(results, tests), db_path=db_path)
        
        message_leaderboard = ""
        if not stealth:
            # Get the user classification.
            user_classification = get_P2_user_classification(user_id, db_path=db_path)
            # If not good enough for the leaderboard
            if not good_enough_lb_result:
                message_leaderboard += "🤕 No he subido tu resultado del nivel 4 a la leaderboard. ¡Sigue intentándolo!"
            elif user_classification is None:
                message_leaderboard += "😱 Parece que aún no has subido nada a la leaderboard, ¿no? ¡Sigue con el resto de niveles y cuando acabes, a por el 4!"
            # If it was its first upload
            elif user_classification['total_submissions'] == 1:
                message_leaderboard += "💙 ¡Gracias por participar por primera vez! Tu resultado se ha subido a la /leaderboard, consúltala para ver tu posición."
            # If it was its best upload
            elif user_classification['total_submissions'] == user_classification['id_submission']:
                message_leaderboard += "🏆 ¡Has superado tu mejor resultado, enhorabuena! Tu puntuación ha sido actualizada en la /leaderboard, consúltala para ver tu posición."
            # If it was not its best upload
            else:
                message_leaderboard += "🤕 ¡Buen intento, aunque no has superado tu mejor resultado en la /leaderboard! ¡Sigue intentándolo!"
            string_medal = ""

            if good_enough_lb_result and user_classification is not None:
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

        TOKEN=__BOT_TOKEN__
        CHAT_ID=user_id

        # Create a bot and send the message.
        bot = Bot(token=TOKEN)

        async with bot:
            try:
                await bot.send_message(chat_id=CHAT_ID, text=message_intro)
            except Exception as e:
                print(f"Error sending message: {e}")

            try:
                await bot.send_message(chat_id=CHAT_ID, text=message_legend)
            except Exception as e:
                print(f"Error sending message: {e}")

            # Send the level results as monospace (with markdown V2).
            for level in msg_levels.keys():
                for msg in msg_levels[level]:
                    message = msg.replace(".", "\.").replace("(","\(").replace(")","\)")
                    try:
                        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
                    except Exception as e:
                        print(f"Error sending message: {e}")

            if not stealth:
                try:
                    await bot.send_message(chat_id=CHAT_ID, text=message_leaderboard)
                except Exception as e:
                    print(f"Error sending message: {e}")

    else:
        # Get the first command line argument.

        TOKEN=__BOT_TOKEN__
        CHAT_ID=user_id

        # Create a bot and send the message.
        bot = Bot(token=TOKEN)

        async with bot:
            message="❌ Ha habido un error. No se ha podido generar el ejecutable. Posiblemente haya habido un error de compilación con tu código."

            try:
                await bot.send_message(chat_id=CHAT_ID, text=message)
            except Exception as e:
                print(f"Error sending message: {e}")

            # Send the file slurm_outputs/<job_id>.err to the user.
            with open(f"../../../slurm_outputs/{job_id}.err", 'r') as f:
                try:
                    await bot.send_document(chat_id=CHAT_ID, document=f, filename=f"error_log.txt", caption="Archivo de errores")
                except Exception as e:
                    print(f"Error sending message: {e}")

        #message="❌ Ha habido un error. No se ha podido generar el ejecutable. Posiblemente haya habido un error de compilación con tu código."

        #url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
        #print(requests.get(url).json())

if __name__ == "__main__":
    asyncio.run(main())