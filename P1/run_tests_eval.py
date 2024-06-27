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
    

async def main():
    compile_error = not os.path.exists("practica1SG")
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

            # Save the results and summaries.
            
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
            json.dump({}, f)

        # Copy the summary file into ../../results/$alumno.json
        shutil.copyfile(f"./results.json", f"../../results/{alumno}.json")



if __name__ == "__main__":
    asyncio.run(main())