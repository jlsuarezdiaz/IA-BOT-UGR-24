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
import shutil
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
    

async def main():
    compile_error = not os.path.exists("practica2SG")
    if not compile_error:
        # Create a dictionay to store the results.
        results = {}

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


            # Run the level 0-4 tests.
            for level in range(5):
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

            # Create a message with the results.
            message_intro = "✅ La ejecución ha terminado.\n\n"
            message_intro += "📊 Resultados:\n"
            message_intro += "0️⃣1️⃣2️⃣3️⃣ | Estimación Global (sobre 10)\n"

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
                    elif total_warnings > 0 and total_fails == 0:
                        level_avgs[level] = 'almost_ok'
                    elif total_fails < total_oks:
                        level_avgs[level] = 'warning'
                    else:
                        level_avgs[level] = 'fail'

                    level_emoji = "✅" if level_avgs[level] == 'ok' else "⚠️" if level_avgs[level] == 'warning' else "🆗" if level_avgs[level] == 'almost_ok' else "❌"
                    
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

            # Save the results and summaries.
            results["compiled"] = True
            # Save the results.
            with open(f"./results.json", 'w') as f:
                json.dump(results, f)
        
            alumno = sys.argv[1]
            # Copy the summary file into ../../results/$alumno.json
            shutil.copyfile(f"./results.json", f"../../results/{alumno}.json")
           

    else:
        # Get the first command line argument.
        user_id = sys.argv[2]
        alumno = sys.argv[1]

        TOKEN=__BOT_TOKEN__
        CHAT_ID=user_id

        # Create a bot and send the message.
        bot = Bot(token=TOKEN)

        async with bot:
            message=f"❌ Ha habido un error con {alumno}. No se ha podido generar el ejecutable. Posiblemente haya habido un error de compilación con el código."

            await bot.send_message(chat_id=CHAT_ID, text=message)

        with open(f"./results.json", 'w') as f:
            json.dump({"compiled": False}, f)

        # Copy the summary file into ../../results/$alumno.json
        shutil.copyfile(f"./results.json", f"../../results/{alumno}.json")

if __name__ == "__main__":
    asyncio.run(main())