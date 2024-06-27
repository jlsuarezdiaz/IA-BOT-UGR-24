__BOT_TOKEN__="__INSERT_BOT_TOKEN_HERE__"

import os
import telegram
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, filters, CommandHandler, ConversationHandler, ApplicationBuilder, ContextTypes, CallbackQueryHandler
import queue
import logging
import json
import datetime
import random
import shutil
import sys
import re
import unidecode
import sqlite3
from db_functions import *
import pytz
import pandas as pd
import subprocess
from utils import send_leaderboard, position_to_emoji, GROUP_CHATS, GROUP_FILTERS, LB_BUTTONS, get_ok_warn_fail, get_perc_blob, get_level4_blob

# Define the different states of the conversation
START, NAME, GROUP, FILES, HEURISTIC, NINJA = range(6)

# ConversationHandler states for registration.
NEW_USER, EXPECTING_TOKEN, EXPECTING_ALIAS = range(3)

DB_FOLDER = 'db/'
EVAL_FOLDER = 'evals/'
NINJA_FOLDER = 'ninja-battles/'
TOUR_FOLDER = 'tour-submissions/'

START_COUNT = 200

# Define regular expressions for some sentence patterns that the bot will recognize
# The regular expressions are defined using the re module

RE_HELLO = re.compile(r'\b(hola|buenos dias|buenas tardes|buenas noches|buenas)\b', re.IGNORECASE)
RE_GOODBYE = re.compile(r'\b(hasta luego|hasta pronto|hasta mañana|adios)\b', re.IGNORECASE)
RE_THANKS = re.compile(r'\b(gracias|muchas gracias)\b', re.IGNORECASE)
RE_DIFFERENT_RESULTS = re.compile(r'\b(resultados diferentes|resultados distintos|otro resultado|diferente resultado|distinto resultado|resultados distintos|resultados diferentes|no .* mismo.? resultado.?|bot .* no .* termina|termina .* bot .* no|no .* termina .* bot)\b', re.IGNORECASE)
# RE_VALGRIND: "que|como * valgrind" (e.g. "¿Qué es valgrind?", "¿Cómo se usa valgrind?")
RE_VALGRIND = re.compile(r'\b(que|como) .* valgrind\b', re.IGNORECASE)
# RE_NOTABOT: "* (nota|evaluacion) * bot" or "bot * (nota|evaluacion)" (e.g. "¿Qué nota me has puesto, bot?", "bot, ¿qué nota me has puesto?")
RE_NOTABOT = re.compile(r'\b((bot) .* (nota.?|evaluacion)|(nota.?|evaluacion) .* (bot))\b', re.IGNORECASE)
# RE_NOTALB = "* (nota|evaluacion) * leaderboard" or "leaderboard * (nota|evaluacion)" (e.g. "¿Qué nota tengo en la leaderboard?", "leaderboard, ¿qué nota tengo?")
RE_NOTALB = re.compile(r'\b((leaderboard) .* (nota.?|evaluacion)|(nota.?|evaluacion) .* (leaderboard))\b', re.IGNORECASE)
# RE_CUANDO = "(cuando|fecha|dia) * entrega"
RE_CUANDO = re.compile(r'\b(cuando|fecha|dia) .* entrega\b', re.IGNORECASE)
#RE_NOCOMPILA = "bot * no * compila" or "no * compila * bot" or "compila * bot * no"
RE_NOCOMPILA = re.compile(r'\b((bot) .* (no) .* (compila)|(no) .* (compila) .* (bot)|(compila) .* (bot) .* (no))\b', re.IGNORECASE)

# RE_VIRTUAL_THINK: "[spaces]virtual[spaces]void[spaces]think[spaces]([spaces]color[spaces]&[spaces]c_piece[spaces],[spaces]int[spaces]&[spaces]id_piece[spaces],[spaces]int[spaces]&[spaces]dice[spaces])[spaces]const[spaces];[spaces]"
RE_VIRTUAL_THINK = re.compile(r"virtual\s+void\s+think\s*\(\s*color\s*&\s*c_piece\s*,\s*int\s*&\s*id_piece\s*,\s*int\s*&\s*dice\s*\)\s*const\s*;", re.IGNORECASE)

# La fecha de entrega es el 7 de abril de 2024 a las 23:00 (UTC+2)
FECHA_ENTREGA = datetime.datetime(2024, 4, 7, 23, 0, 0, 0, pytz.timezone('Europe/Madrid'))
FECHA_ENTREGA_CUESTIONARIO = datetime.datetime(2024, 4, 10, 23, 0, 0, 0, pytz.timezone('Europe/Madrid'))



logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)



def check_integrity(path):
    # Read the file from path as text.
    with open(path, 'r') as f:
        # Check if there is a line "virtual void think(color & c_piece, int & id_piece, int & dice) const;"
        # Allow multiple spaces (i.e. use a regular expression).
        if RE_VIRTUAL_THINK.search(f.read()):
            return True
        else:
            return False
    

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if it is a user chat or a group chat
    if update.message.chat.type == 'private':
        if find_user_in_db(update.message.from_user.id) is not None:
            await context.bot.send_message(chat_id=update.message.chat_id, text='¡Hola! ¡Bienvenid@ al bot de la práctica 3! Te ayudaré a ver si tu poda funciona bien, a enfrentarte a los ninjas más rápido y a participar en el torneo de Parchís. Escribe /help para ver los comandos que puedes usar.')
        else:
            await context.bot.send_message(chat_id=update.message.chat_id, text='¡Hola! ¡Bienvenido al bot de la práctica 1! Antes de comenzar, debes registrarte. Por favor, introduce tu token. '
                                                                                'Si eres estudiante del curso, tu token es tu número de DNI o NIE. Si no consigues acceder, contacta con '
                                                                                'tus profesores para que te faciliten tu token. Si quieres salir, escribe /cancel.')

            return EXPECTING_TOKEN


    else:
        # await context.bot.send_message(chat_id=update.message.chat_id, text='Mejor hablamos en privado. 😅', reply_to_message_id=update.message.message_id)
        global START_COUNT
        # await context.bot.send_message(chat_id=update.message.chat_id, text=f'¡Enhorabuena! Eres el/la usuari@ número {START_COUNT} en usar este comando sin leerse las instrucciones 🎉🎉🎉\nComo premio tendrás un punto menos en la evaluación 😈', reply_to_message_id=update.message.message_id)
        # Send the meme in memes/ah-shit.mp4
        await context.bot.send_video(chat_id=update.message.chat_id, video=open("memes/ah-shit.mp4", 'rb'), supports_streaming=True, reply_to_message_id=update.message.message_id)
        
        START_COUNT += 1        
        return ConversationHandler.END
    
    return ConversationHandler.END

async def check_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user has sent the /cancel command
    if update.message.text == '/cancel':
        await context.bot.send_message(chat_id=update.message.chat_id, text='Muy bien.')
        return ConversationHandler.END
    
    # Get the token and check if it is in the database
    token = update.message.text
    token_in_db = find_token_in_db(token)
    found = token_in_db is not None
    if found:
        # Check if the token is being used by another user
        repeated = find_token_in_registered(token) is not None
        if repeated:
            await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, el token que has introducido ya está siendo utilizado por otro usuario. Si has cambiado de cuenta de Telegram, '
                                                                                'o si es otra persona la que está utilizando tu token, por favor, contacta con tus profesores o escríbenos por el grupo de Telegram '
                                                                                'para solucionarlo. Si estás usando el token '
                                                                                'de otra persona, bórralo inmediatamente y usa el tuyo propio. El uso inapropiado de los tokens puede tener sanciones.')   
            return ConversationHandler.END
        else:
            # Get the information of the token row
            name = token_in_db[1]
            surname = token_in_db[2]
            group = token_in_db[3]
            prado_id = token_in_db[4]
            # If the group ends with D, remove the D and add " (DG)" to the group
            strgroup = group
            if group[-1] == 'D':
                strgroup = group[:-1] + " (DG)"
            print(f"REGISTERING: {name} {surname} {group} {prado_id} {token}")
            context.user_data['token'] = token
            # Ask the user for their alias
            msg = f"¡Autenticación correcta! Eres del grupo {strgroup}, ¿verdad? Si no es correcto, escribe a tus profesores o contáctanos por el grupo de Telegram para que lo corrijamos."
            await context.bot.send_message(chat_id=update.message.chat_id, text=msg)
            msg = f"¿Cómo quieres que te llame? Puedes decirme tanto tu nombre real como un alias, siempre que sea respetuoso. El nombre que elijas será el que aparezca en las leaderboards que se realicen con este bot."
            await context.bot.send_message(chat_id=update.message.chat_id, text=msg)
            return EXPECTING_ALIAS
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, el token que has introducido no es válido. Por favor, inténtalo de nuevo. Si sigues teniendo problemas, contacta a tus profesores o escríbenos por el grupo de Telegram.')
        return EXPECTING_TOKEN
    
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user has sent the /cancel command
    if update.message.text == '/cancel':
        await context.bot.send_message(chat_id=update.message.chat_id, text='Muy bien. El registro se ha cancelado. Cuando quieras registrarte tendrás que repetir todo el proceso con /start.')
        return ConversationHandler.END

    blacklist = []
    warn_list = []
    # Check if the name provided is in the blacklist or contains a substring of the blacklist.
    if any(word in update.message.text.lower() for word in blacklist):
        await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, el nombre que has puesto está en la lista negra. Por favor, elige otro.')
        return EXPECTING_ALIAS
    # Check if the name provided is in the warnlist or contains a substring of the warnlist. Accept the name but warn the user.
    if any(word in update.message.text.lower() for word in warn_list):
        await context.bot.send_message(chat_id=update.message.chat_id, text='⚠️⚠️ Te lo acepto, pero, ¿estás seguro de que ese nombre es apropiado? ⚠️⚠️')

    # Check if the name contains only spaces.
    if not update.message.text.strip():
        await context.bot.send_message(chat_id=update.message.chat_id, text='Por favor, escribe un nombre que no esté vacío.')
        return EXPECTING_ALIAS

    # Register the user (if new user)
    name = update.message.text
    user_id = update.message.from_user.id
    if 'token' in context.user_data:
        token = context.user_data['token']
        register_user(user_id, token, name)
        print(f"REGISTERED: {name} {token}")
        # Remove the token from the context data
        context.user_data.pop('token')
    else:
        update_user_alias(user_id, name)
        print(f"UPDATED: {name} {user_id}")
        
    # Inform that the register was successful.
    await context.bot.send_message(chat_id=update.message.chat_id, text=f'¡Perfecto! Te has registrado con el nombre {name}. Si en algún momento quieres cambiar tu  alias, escribe el comando /changename.')
    await context.bot.send_message(chat_id=update.message.chat_id, text='¡Espero que lo pases bien con el bot! 😊')
    return ConversationHandler.END

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if it is a user chat or a group chat
    if True:  # update.message.chat.type == 'private':
        msg = """¡Hola! Soy el bot de la práctica 3. Estos son los comandos que puedes usar:
        /start: Si no te has registrado todavía, inicia el proceso de registro con este comando.
        /testpoda: Te enseño cómo debería ser el resultado de una partida de de ValoracionTest contra lo que me pidas.
        /battleninja: Enfréntate a los ninjas que quieras sin ejecutar en tu ordenador y en paralelo a múltiples de ellos.
        /batteninja <list[int]>: Si me especificas la lista de ninjas con los que quieres enfrentarte, te enfrentarás a esos. Si no, te la pediré después.
        /tourjoin: Sube tu solución actual para participar en el torneo de Parchís.
        /tourleave: Si te arrepientes, puedes retirarte del torneo con este comando.
        /notify: Cambia tu configuración de notificaciones.
        /changename: Cambia tu alias.
        /cancel: Cancela el proceso de subir tu solución.
        /stop: Si tienes alguna solución subida y ejecutándose, este comando las detendrá.
        /leaderboard: Muestra el enlace a la leaderboard.
        /history: Muestra el historial de subidas de tu solución.
        /get <fecha>: Te devuelvo el código la solución que subiste en la fecha indicada. El formato de la fecha es el mismo que el que aparece al usar /history.
        /help: Muestra esta ayuda. LÉELA BIEN ANTES DE EMPEZAR A USARME O DE PREGUNTAR.
        /faq: Muestra las preguntas frecuentes. LÉELAS BIEN ANTES DE EMPEZAR A USARME O DE PREGUNTAR.
        /about: Muestra información sobre el bot. LÉELO BIEN ANTES DE EMPEZAR A USARME O DE PREGUNTAR.

        Ten en cuenta que muchos de estos comandos son solo para usarlos en privado.
        Si tienes alguna otra pregunta sobre el bot o estás teniendo algún problema, puedes escribirnos por el canal de SOPORTE BOT en el grupo de Telegram.
        """
        if update.message.chat.type == 'private':
            await context.bot.send_message(chat_id=update.message.chat_id, text=msg)
        else:
            await context.bot.send_message(chat_id=update.message.chat_id, text=msg, reply_to_message_id=update.message.message_id)
    else:
        msg = "Mejor hablamos en privado. 😅"
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg, reply_to_message_id=update.message.message_id)

async def changename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if it is a user chat or a group chat
    if update.message.chat.type != 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text='Mejor hablamos en privado. 😅', reply_to_message_id=update.message.message_id)
        return ConversationHandler.END
    # Check if the user is registered
    the_user = get_full_user(update.message.from_user.id)
    if the_user is None:
        await context.bot.send_message(chat_id=update.message.chat_id, text='Todavía no te has registrado. Escribe /start para iniciar el proceso.')
        return ConversationHandler.END
    # Ask the user for their alias
    msg = f"¿Cómo quieres que te llame? Puedes decirme tanto tu nombre real como un alias, siempre que sea respetuoso. El nombre que elijas será el que aparezca en las leaderboards que se realicen con este bot."
    await context.bot.send_message(chat_id=update.message.chat_id, text=msg)
    return EXPECTING_ALIAS

async def upload_core(update: Update, context: ContextTypes.DEFAULT_TYPE, levels=None, stealth=False):
    # Uncomment this message when the leaderboard date is due.
    if not stealth:
        await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, la práctica 2 ha terminado. ¡Nos vemos pronto con la práctica 3! 😊 🔴🟡🟢🔵🎲💣🧨💥', reply_to_message_id=update.message.message_id)
        return ConversationHandler.END

    # Check if it is a user chat or a group chat
    if update.message.chat.type != 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text='Esto mejor mándamelo por privado. ¿No querrás que nos copiemos de ti? 😳', reply_to_message_id=update.message.message_id)
        return ConversationHandler.END
    # Check if the user is registered
    the_user = get_full_user(update.message.from_user.id)
    if the_user is None:
        await context.bot.send_message(chat_id=update.message.chat_id, text='Tienes que estar registrado para poder subir tu solución. Escribe /start para iniciar el proceso.')
        return ConversationHandler.END

    #if the_user['group'] != 'PROFES':
    #    await context.bot.send_message(chat_id=update.message.chat_id, text='A ver, tranquilidad. Aún estoy en pruebas. Ya avisarán los profesores cuando se pueda usar el bot.')
    #    return ConversationHandler.END
    # Randomly with a 1/20 probability, send a message reminding to read the instructions instead of running the upload
    if random.randint(1, 20) == 1:
        await context.bot.send_message(chat_id=update.message.chat_id, text='🚨🚨 ¡Hola! Aprovecho para recordarte que debes leer mis instrucciones y las preguntas frecuentes si no lo has hecho aún. '
                                                                            'Es importante para conocer bien cómo funciono, y evitar a los profesores responder 100 veces las mismas preguntas. '
                                                                            'Para ello, tienes los comandos /about, /help y /faq. Si no los has leído, aprovecha ahora. Después vuelve a escribirme /upload. '
                                                                            'Si ya lo habías leído todo, siento la interrupción. ¡Gracias! 🚨🚨')
        return ConversationHandler.END
    
    # If there are no arguments, upload the solution for all levels.

    
    # Get the user's folder. It is a folder named with the telegram id of the user.
    user_folder = DB_FOLDER + str(update.message.from_user.id)
    # If the folder doesn't exist, create it.
    if not os.path.exists(user_folder):
        os.mkdir(user_folder)
    # Check if the user has a solution being executed. To do this, check if there is a folder called software in the user's folder.
    if os.path.exists(user_folder + '/software'):
        await context.bot.send_message(chat_id=update.message.chat_id, text='⚠️⚠️ ¡Ups! Parece que ya tienes una solución ejecutándose. Solo puedes tener una solución ejecutándose a la vez. Espera a que termine o para la ejecución con el comando /stop.')
        return ConversationHandler.END
    
    await context.bot.send_message(chat_id=update.message.chat_id, text=f"¡Hola de nuevo, {the_user['alias']}, del grupo {the_user['group']}! ¿Preparad@ para subir tu solución? ¡Vamos allá! Solo tienes que enviarme tus ficheros jugador.cpp y jugador.hpp.")
    await context.bot.send_message(chat_id=update.message.chat_id, text=f"Recuerda que puedes elegir niveles concretos en los que quieres que te evalue si quieres que sea más rápido (si no lo has hecho ya). Usa /help para ver todas las opciones. Con el comando y argumentos que me has mandado ahora mismo, te voy a evaluar estos niveles: {levels}.")
    context.user_data['files'] = []
    context.user_data['stealth'] = stealth
    context.user_data['levels'] = levels
    
    # Return the FILES state
    return FILES

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the arguments of the command
    args = update.message.text.split(' ')
    # If there are no arguments, upload the solution for all levels.
    if len(args) == 1:
        levels = [0, 1, 2, 3, 4]
    else:
        levels = []
        for arg in args[1:]:
            try:
                level = int(arg)
                if level < 0 or level > 4:
                    await context.bot.send_message(chat_id=update.message.chat_id, text='Los niveles tienen que ser un número entre 0 y 4.')
                    return ConversationHandler.END
                levels.append(level)
            except ValueError:
                await context.bot.send_message(chat_id=update.message.chat_id, text='Los niveles tienen que ser un número entre 0 y 4.')
                return ConversationHandler.END

    return await upload_core(update, context, levels, False)

async def upload4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await upload_core(update, context, [4], False)

async def upload3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await upload_core(update, context, [0, 1, 2, 3], False)

async def stealth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the chat is private
    if update.message.chat.type != 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text='¡Oye! ¡No puedes hacer eso! 😡', reply_to_message_id=update.message.message_id)
        return ConversationHandler.END
    # Check if the user is registered
    the_user = get_full_user(update.message.from_user.id)
    if the_user is None:
        await context.bot.send_message(chat_id=update.message.chat_id, text='¡Oye! ¡No puedes hacer eso! 😡')
        return ConversationHandler.END
    # Check if the user is a professor
    if the_user['group'] != 'PROFES' and the_user['telegram_id'] != 6542778:
        await context.bot.send_message(chat_id=update.message.chat_id, text='¡Oye! ¡No puedes hacer eso! 😡')
        return ConversationHandler.END
    args = update.message.text.split(' ')
    if len(args) == 1:
        levels = [0, 1, 2, 3, 4]
    else:
        levels = []
        for arg in args[1:]:
            try:
                level = int(arg)
                if level < 0 or level > 4:
                    await context.bot.send_message(chat_id=update.message.chat_id, text='Los niveles tienen que ser un número entre 0 y 4.')
                    return ConversationHandler.END
                levels.append(level)
            except ValueError:
                await context.bot.send_message(chat_id=update.message.chat_id, text='Los niveles tienen que ser un número entre 0 y 4.')
                return ConversationHandler.END

    return await upload_core(update, context, levels, True)

async def get_files(update, context):
    # Check if the user has sent the /cancel command
    if update.message.text == '/cancel':
        await context.bot.send_message(chat_id=update.message.chat_id, text='Muy bien. Si quieres subir tu solución más tarde, vuelve a escribirme /upload.')
        return ConversationHandler.END

    # Check if the message contains a file
    if not update.message.document:
        # If not, ask the user to send a file
        await context.bot.send_message(chat_id=update.message.chat_id, text='Por favor, necesito los ficheros.')
        # update.message.reply_text('Please send me a file.')
        return FILES

    # Get the file information
    file = await context.bot.get_file(update.message.document.file_id)
    file_name = update.message.document.file_name
    #file = update.message.document
    file_extension = os.path.splitext(file_name)[1].lower()

    if file_name in  ['jugador.cpp', 'jugador.hpp']:
        # Check if it was already sent.
        if file_name in context.user_data['files']:
            await context.bot.send_message(chat_id=update.message.chat_id, text='Ya me habías enviado este archivo. Si te has confundido de versión, escribe /cancel y vuelve a empezar.')
            return FILES
        else:
            # Download the file and store it in memory
            # Create a folder with the telegram id as a name.
            os.makedirs(os.path.join(os.getcwd(), DB_FOLDER, str(update.message.from_user.id)), exist_ok=True)
            # Create a folder inside called 'uploads'
            os.makedirs(os.path.join(os.getcwd(), DB_FOLDER, str(update.message.from_user.id), 'uploads'), exist_ok=True)
            # Create a folder inside with the current timestamp.
            if 'curr_timestamp' not in context.user_data:
                context.user_data['curr_timestamp'] = str(datetime.datetime.now())
            os.makedirs(os.path.join(os.getcwd(), DB_FOLDER, str(update.message.from_user.id), 'uploads', context.user_data['curr_timestamp']), exist_ok=True)
            # Download the file to the folder.
            await file.download_to_drive(os.path.join(os.getcwd(), DB_FOLDER, str(update.message.from_user.id), 'uploads', context.user_data['curr_timestamp'], file_name))
            context.user_data['files'].append(file_name)

            remaining_files = [f for f in ['jugador.cpp', 'jugador.hpp'] if f not in context.user_data['files']]
            if len(remaining_files) == 0:
                await context.bot.send_message(chat_id=update.message.chat_id, text='¡Gracias! He recibido todos los ficheros. Ahora, en cuanto tenga un hueco disponible, voy a compilarlos y ejecutarlos. Si todo va bien, te enviaré un mensaje cuando tu resultado esté disponible.')
                # Call to sbatch and submit the job.
                levels = context.user_data['levels']
                str_levels = ' '.join([str(l) for l in levels])
                # print(f'sbatch -J {update.message.from_user.id} run_executions.sh "{context.user_data["curr_timestamp"]}" {1 if context.user_data["stealth"] else 0} {str_levels}')
                    
                os.system(f'sbatch -J {update.message.from_user.id} run_executions.sh "{context.user_data["curr_timestamp"]}" {1 if context.user_data["stealth"] else 0} {str_levels}')
                context.user_data.pop('curr_timestamp')
                return ConversationHandler.END
            else:
                files_str = ', '.join(remaining_files)
                await context.bot.send_message(chat_id=update.message.chat_id, text=f'Me falta(n) el/los ficheros: {files_str}.')
                return FILES
    else:
        remaining_files = [f for f in ['jugador.cpp', 'jugador.hpp'] if f not in context.user_data['files']]
        files_str = ', '.join(remaining_files)
        await context.bot.send_message(chat_id=update.message.chat_id, text=f'Lo que me has mandado no me sirve. Me falta(n) el/los ficheros: {files_str}.')
        return FILES
    
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if it is a user chat or a group chat
    if update.message.chat.type != 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text='Esto mejor mándamelo por privado. ¿No querrás que nos copiemos de ti? 😳', reply_to_message_id=update.message.message_id)
        return ConversationHandler.END
    # Check if the user is registered
    the_user = get_full_user(update.message.from_user.id)
    if the_user is None:
        await context.bot.send_message(chat_id=update.message.chat_id, text='Tienes que estar registrado primero. Escribe /start para iniciar el proceso.')
        return ConversationHandler.END

    hist = get_P3_user_submission_metrics_df(update.message.from_user.id)
    msgs = []
    line_count = 0
    msg = 'Estas son las soluciones que has subido hasta ahora:\n'
    msg += 'N\. `Fecha:                    `🥷1️⃣1️⃣2️⃣2️⃣3️⃣3️⃣\n'
    msg += '\n'

    for i in range(len(hist)):
        line = f'{i+1}\. `{hist.iloc[i]["submission_date"]}`: '
        for c in ["J1vsN1", "N1vsJ2", "J1vsN2", "N2vsJ2", "J1vsN3", "N3vsJ2"]:
            res = hist.iloc[i][c]
            emoji_res = ""
            if res == "W":
                emoji_res = "🟢"
            elif res == "L":
                emoji_res = "🔴"
            elif res == "D":
                emoji_res = "🟠"
            elif res == "T": # (timeout)
                emoji_res = "⏰"
            elif res == "C": # (Compile error)
                emoji_res = "🛠"
            elif res == '?': # Not tested
                emoji_res = "❔"
            else:  # Error
                emoji_res = "❌"
            line += f"{emoji_res}"

        msg += line + '\n'
        line_count += 1
        if line_count % 30 == 0 or i == len(hist) - 1:
            msgs.append(msg)
            msg = ''

    # Send the message.
    for m in msgs:
        await context.bot.send_message(chat_id=update.message.chat_id, text=m, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
    # await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)

async def get_solution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if it is a user chat or a group chat
    if update.message.chat.type != 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text='Esto mejor mándamelo por privado. ¿No querrás que nos copiemos de ti? 😳', reply_to_message_id=update.message.message_id)
        return ConversationHandler.END
    # Check if the user is registered
    the_user = get_full_user(update.message.from_user.id)
    if the_user is None:
        await context.bot.send_message(chat_id=update.message.chat_id, text='Tienes que estar registrado primero. Escribe /start para iniciar el proceso.')
        return ConversationHandler.END

    if not context.args:
        await context.bot.send_message(chat_id=update.message.chat_id, text='Debes indicar la fecha de la solución que quieres obtener. Puedes consultar tu historial de soluciones con el comando /history y elegir una fecha de esa lista.')
        return
    # Get the first argument of the command.
    date = ' '.join(context.args)
    # Get the user's folder. It is a folder named with the telegram id of the user.
    user_folder = NINJA_FOLDER + str(update.message.from_user.id)
    # Check if {user_folder}/uploads/{date} exists.
    if not os.path.exists(user_folder + '/uploads/' + date):
        await context.bot.send_message(chat_id=update.message.chat_id, text='No existe ninguna solución con la fecha indicada. Puedes consultar tu historial de soluciones con el comando /history y elegir una fecha de esa lista.')
        return
    # Check if {user_folder}/uploads/{date}/jugador.cpp exists.
    if not os.path.exists(user_folder + '/uploads/' + date + '/AIPlayer.cpp'):
        await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, ha habido algún problema. He encontrado la carpeta de la solución pero no encuentro el fichero AIPlayer.cpp. Sorry 😔')
        return
    # Check if {user_folder}/uploads/{date}/jugador.hpp exists.
    if not os.path.exists(user_folder + '/uploads/' + date + '/AIPlayer.h'):
        await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, ha habido algún problema. He encontrado la carpeta de la solución pero no encuentro el fichero AIPlayer.h. Sorry 😔')
        return
    # Send the files.
    await context.bot.send_document(chat_id=update.message.chat_id, document=open(user_folder + '/uploads/' + date + '/AIPlayer.cpp', 'rb'))
    await context.bot.send_document(chat_id=update.message.chat_id, document=open(user_folder + '/uploads/' + date + '/AIPlayer.h', 'rb'))

async def get_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if it is a user chat or a group chat
    #if update.message.chat.type != 'private':
    #    await context.bot.send_message(chat_id=update.message.chat_id, text='Esto mejor mándamelo por privado. ¿No querrás que nos copiemos de ti? 😳', reply_to_message_id=update.message.message_id)
    #    return ConversationHandler.END
    # Check if the user is registered
    #the_user = get_full_user(update.message.from_user.id)
    #if the_user is None:
    #    await context.bot.send_message(chat_id=update.message.chat_id, text='Tienes que estar registrado primero. Escribe /start para iniciar el proceso.')
    #    return ConversationHandler.END

    if not context.args:
        if update.message.chat.type == 'private':
            await context.bot.send_message(chat_id=update.message.chat_id, text='No me has dicho ningún nombre de test 😅.')
        else:
            await context.bot.send_message(chat_id=update.message.chat_id, text='No me has dicho ningún nombre de test 😅.', reply_to_message_id=update.message.message_id)
        return
    # Get the first argument of the command.
    test_name = context.args[0]
    # Open the file tests.json.
    if not os.path.exists('tests.json'):
        if update.message.chat.type == 'private':
            await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, ha habido algún problema. No he encontrado los tests. Sorry 😔')
        else:
            await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, ha habido algún problema. No he encontrado los tests. Sorry 😔', reply_to_message_id=update.message.message_id)
        return
    with open('tests.json', 'r') as f:
        tests = json.load(f)
        # Check if the test exists. We have to iterate through the list of tests and fine if any item has at the key 'name' the value test_name.
        test = None
        if test_name in tests:
            test = tests[test_name]
        if test is None:
            if update.message.chat.type == 'private':
                await context.bot.send_message(chat_id=update.message.chat_id, text='😅 No existe ningún test con el nombre indicado.')
            else:
                await context.bot.send_message(chat_id=update.message.chat_id, text='😅 No existe ningún test con el nombre indicado.', reply_to_message_id=update.message.message_id)
            return
        # Send the test.
        # Prepare the message.
        msg = ""
        msg_additional = ""
        if test["type"] == "normal":
            msg += f"`{test['command']}`\n"
            msg += f"`{test['command'].replace('SG', '')}`\n"
            msg += f"`\"args\": {str(test['command'].split(' ')[1:])}`\n".replace("'", '"')
            msg += f"*Nivel:* {test['level']}\n"
            if test["level"] in [0, 1]:
                msg += f"*Instantes de simulación esperados:* {test['valid_instantes']}.\n"
                msg += f"*Posibles valores finales de batería:* {test['valid_battery']}\n_(podría haber varios óptimos con distinta batería; si la tuya no sale aquí, no lo tienes mal, solo es no tengo ese camino en mi base de datos)._\n"
            if test["level"] in [2, 3]:
                msg += f"*Nivel final de batería esperado:* {test['valid_battery']}.\n"
                msg += f"*Posibles valores finales de instantes:* {test['valid_instantes']}\n_(podría haber varios óptimos con distintos instantes; si el tuyo no sale aquí, no lo tienes mal, solo es no tengo ese camino en mi base de datos)._\n"
            
            msg += f"\n*Intervalo de tiempo razonable (usando una implementación estándar adaptando lo propuesto en el tutorial)*: {test['valid_time'][0]} - {test['valid_time'][1]}\n"
            msg += f"‼️ Que el tiempo no esté en este intervalo no implica que el algoritmo esté mal, es solo una advertencia de que puede haber algún problema.\n"
            
            msg_additional += f"\n*Información adicional:* (/infotests)\n"
            msg_additional += f"_Iteraciones:_ {test['iteraciones']}\n"
            msg_additional += f"_Abiertos:_ {test['abiertos']}\n"
            msg_additional += f"_Cerrados:_ {test['cerrados']}\n"

            msg_additional += "\nSi este test te ha dado algún problema, algunas POSIBLES (NO TODAS) causas pueden ser las siguientes:\n\n"
            for flag in test["flags"]:
                if flag == "avoid_repeated":
                    msg_additional += f" ℹ️ Asegúrate de que tu algoritmo no visita nodos repetidos. Una vez se expande un nodo, este pasa a cerrados. Asegúrate de que cuando aparezca de nuevo compruebas bien que está en cerrados para no expandirlo de nuevo.\n"
                elif flag == "use_items":
                    msg_additional += f" ℹ️ Asegúrate de que tu algoritmo utiliza los objetos que encuentra en el mapa. Si el algoritmo de búsqueda llega a una casilla con bikini o zapatillas, debe actualizar el estado del nodo correctamente para tenerlo en cuenta, ya que el objeto influye en el coste del movimiento.\n"
                elif flag == "operator<":
                    msg_additional += f" ℹ️ Asegúrate de que has extendido bien el operador< de los estados para que el algoritmo pueda buscar correctamente en el conjunto de cerrados.\n"
                elif flag == "heuristic":
                    msg_additional += f" ℹ️ Asegúrate de que la heurística que has programado es adecuada. Si no es informativa, el A\* puede ser muy lento. Si no es admisible o monótona, el algoritmo puede no encontrar el óptimo.\n"
                elif flag == "coste_current":
                    msg_additional += f" ℹ️ Recuerda que el coste de un movimiento se calcula sobre la casilla de la que se parte y no sobre la casilla a la que se llega.\n"
                elif flag == "start_bikini_jugador":
                    msg_additional += f" ℹ️ Asegúrate de que si el jugador empieza en una casilla de bikini el estado inicial para el algoritmo de búsqueda lo tiene en cuenta.\n"
                elif flag == "start_zapas_jugador":
                    msg_additional += f" ℹ️ Asegúrate de que si el jugador empieza en una casilla de zapatillas el estado inicial para el algoritmo de búsqueda lo tiene en cuenta.\n"
                elif flag == "start_bikini_sonambulo":
                    msg_additional += f" ℹ️ Asegúrate de que si el colaborador empieza en una casilla de bikini el estado inicial para el algoritmo de búsqueda lo tiene en cuenta.\n"
                elif flag == "start_zapas_sonambulo":
                    msg_additional += f" ℹ️ Asegúrate de que si el colaborador empieza en una casilla de zapatillas el estado inicial para el algoritmo de búsqueda lo tiene en cuenta.\n"
                elif flag == "start_item_both":
                    msg_additional += f" ℹ️ Asegúrate de que si ambos jugadores empiezan en una casilla con un objeto el estado inicial para el algoritmo de búsqueda lo tiene en cuenta. Recuerda que cada agente gestiona sus objetos de forma independiente.\n"
                elif flag == "items_independent":
                    msg_additional += f" ℹ️ Recuerda que jugador y colaborador tienen sus objetos de forma independiente. Si uno de ellos coge un objeto, no afecta a lo que llevara puesto el otro.\n"
                elif flag == "just_one_item":
                    msg_additional += f" ℹ️ Recuerda que cada agente solo puede llevar un objeto a la vez. Si un agente coge un objeto nuevo y llevaba puesto el otro, pierde el antiguo y se queda solo con el nuevo.\n"
                elif flag == "no_recarga":
                    msg_additional += f" ℹ️ Recuerda que se pide el camino óptimo en *consumo*, es decir, que gaste menos. No el que acabe con más batería. El efecto de la recarga de la casilla X no hay que tenerlo en cuenta en la búsqueda.\n"
                elif flag == "sonambulo_obstaculo":
                    msg_additional += f" ℹ️ Hay que considerar al colaborador como un obstáculo más cuando se mueve el jugador, y viceversa.\n"
                elif flag == "acabar_cerrados":
                    msg_additional += f" ℹ️ Recuerda que coste uniforme y A\*, a diferencia de la anchura, tienen que terminar cuando el nodo solución *pasa a cerrados*, y no cuando *entra en abiertos*. De lo contrario, podrían no encontrar el óptimo.\n"
                elif flag == "zapatillas_siguiente_casilla":
                    msg_additional += f" ℹ️ Revisa que no te estés poniendo las zapatillas de la casilla a la que te estás moviendo antes de haber calculado el coste de la casilla de la que partes.\n"
                elif flag == "bikini_siguiente_casilla":
                    msg_additional += f" ℹ️ Revisa que no te estés poniendo el bikini de la casilla a la que te estás moviendo antes de haber calculado el coste de la casilla de la que partes.\n"
                else:
                    msg_additional += f" ℹ️ {flag}\n"
            if len(test["flags"]) == 0:
                msg_additional += "Pues va a ser que no tengo ningún consejo para este test 😅\n"
        elif test["type"] == "eval":
            msg += f"_¡Anda! Has encontrado el test que caerá en la evaluación 😱_".replace("!","\!")
        elif test["type"] in ["public", "special"]:
            msg += f"`{test['command']}`\n"
            msg += f"`{test['command'].replace('SG', '')}`\n"
            msg += f"`\"args\": {str(test['command'].split(' ')[1:])}`\n".replace("'", '"')
            msg += f"*{test['name']}* (*Nivel:* {test['level']})\n"
            msg += f"*Umbral 1 pto:* {test['umbral1']}\n"
            msg += f"*Umbral 2 ptos:* {test['umbral2']}\n"
            msg += f"*Umbral 3 ptos:* {test['umbral3']}\n"
        elif test["type"] == "private":
            msg += f"Nope 😉"

        # Check if there is a file {test_name}.png inside the test_pngs folder.
        if os.path.exists('test_pngs/' + test_name + '.png'):
            msg = msg.replace('(' , '\(').replace(')', '\)').replace('.', '\.').replace('-', '\-')
            msg_additional = msg_additional.replace('(' , '\(').replace(')', '\)').replace('.', '\.').replace('-', '\-')
            if update.message.chat.type == 'private':
                await context.bot.send_photo(chat_id=update.message.chat_id, photo=open('test_pngs/' + test_name + '.png', 'rb'), caption=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
                if msg_additional:
                    await context.bot.send_message(chat_id=update.message.chat_id, text=msg_additional, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
            else:
                await context.bot.send_photo(chat_id=update.message.chat_id, photo=open('test_pngs/' + test_name + '.png', 'rb'), caption=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_to_message_id=update.message.message_id)
                if msg_additional:
                    await context.bot.send_message(chat_id=update.message.chat_id, text=msg_additional, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_to_message_id=update.message.message_id)
        else:
            msg = msg.replace('(' , '\(').replace(')', '\)').replace('.', '\.').replace('-', '\-')
            msg_additional = msg_additional.replace('(' , '\(').replace(')', '\)').replace('.', '\.').replace('-', '\-')
            if update.message.chat.type == 'private':
                await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
                if msg_additional:
                    await context.bot.send_message(chat_id=update.message.chat_id, text=msg_additional, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
            else:
                await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_to_message_id=update.message.message_id)
                if msg_additional:
                    await context.bot.send_message(chat_id=update.message.chat_id, text=msg_additional, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_to_message_id=update.message.message_id)

async def get_info_tests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """
    *Información adicional sobre los tests (niveles 0-3):*
    
    *Iteraciones:* Número de iteraciones que se han realizado para encontrar la solución óptima.
    *Abiertos:* Número de nodos abiertos en el momento de encontrar la solución óptima.
    *Cerrados:* Número de nodos cerrados en el momento de encontrar la solución óptima.

    Esta información muestra los números aproximados para una implementación estándar del algoritmo de búsqueda de cada nivel.
    Lo normal es que no te salgan valores idénticos a los que aparecen en el test. Según la implementación puede variar. Solo debes preocuparte si los valores son MUY distintos.
    Puedes comparar con los de tu algoritmo imprimiendo durante la ejecución el tamaño final de las listas de abiertos y cerrados junto con el número de iteraciones (en el while externo).
    """.replace('.', '\.').replace('-', '\-').replace('(' , '\(').replace(')', '\)')
    await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Lo siento, no he entendido tu comando. Si estabas en medio de una conversación previa tal vez deberías usar /cancel y volver a probar.")
    return START


WINDOW_SIZE = 20
async def get_leaderboard(update, context):
    await send_leaderboard(bot=context.bot,chat_id=update.message.chat_id, user_id=update.message.from_user.id, reply_to_message_id=update.message.message_id, chat_type=update.message.chat.type, user_data=context.user_data)

    
async def leaderboard_callback(update, context):
    query = update.callback_query
    reply = ''

    if 'current_window' not in context.user_data:
        context.user_data['current_window'] = (0, WINDOW_SIZE)
    if 'current_group' not in context.user_data:
        context.user_data['current_group'] = 'ALL'

    # Only the user who sent the message can interact with the buttons.
    if query.message.reply_to_message is not None and query.from_user.id != query.message.reply_to_message.from_user.id:
        await context.bot.answer_callback_query(query.id, text='Solo puede tocar los botones quien invoca la leaderboard 😅', show_alert=False)
        return
    
    # Get the current leaderboard
    leaderboard_df = get_P3_classification("current")
    leaderboard_to_show = leaderboard_df[GROUP_FILTERS[context.user_data['current_group']]]
    # Get the position of the user in the current leaderboard
    user_pos_r = leaderboard_to_show[leaderboard_to_show['player_id'] == query.from_user.id].index
    if len(user_pos_r) == 0:
        user_pos = None
    else:
        user_pos = user_pos_r[0]

    # Get the row of the user in the current leaderboard (it's not the index, just the row number!!)
    user_row_r = np.where(leaderboard_to_show['player_id'] == query.from_user.id)[0]
    if len(user_row_r) > 0:
        user_row = user_row_r[0]
    else:
        user_row = None
    # Apply the position_to_emoji function to the 'position' column elementwise.
    leaderboard_to_show['position'] = pd.Series(leaderboard_to_show.index, index=leaderboard_to_show.index).apply(position_to_emoji)
    df_size = len(leaderboard_to_show)

    

    if query.data == 'lb_prev':
        if context.user_data['current_window'][0] - WINDOW_SIZE < 0:
            context.user_data['current_window'] = (0, min(WINDOW_SIZE, df_size))
        else:
            curr_page = context.user_data['current_window'][0] // WINDOW_SIZE
            context.user_data['current_window'] = ((curr_page - 1) * WINDOW_SIZE, min(curr_page * WINDOW_SIZE, df_size))
    elif query.data == 'lb_next':
        curr_page = context.user_data['current_window'][0] // WINDOW_SIZE
        if curr_page * WINDOW_SIZE + WINDOW_SIZE >= df_size:
            context.user_data['current_window'] = (curr_page * WINDOW_SIZE, df_size)
        else:
            context.user_data['current_window'] = ((curr_page + 1) * WINDOW_SIZE, min((curr_page + 2) * WINDOW_SIZE, df_size))
    elif query.data == 'lb_me':
        
        if user_row is not None:
            curr_page = user_row // WINDOW_SIZE
            context.user_data['current_window'] = (curr_page * WINDOW_SIZE, min((curr_page + 1) * WINDOW_SIZE, df_size))
        else:
            reply = "Me temo que no sales en esa tabla. 😅"
    elif query.data.startswith('lb_'):
        context.user_data['current_group'] = query.data[3:]
        leaderboard_to_show = leaderboard_df[GROUP_FILTERS[context.user_data['current_group']]]
        df_size = len(leaderboard_to_show)
        leaderboard_to_show['position'] = pd.Series(leaderboard_to_show.index, index=leaderboard_to_show.index).apply(position_to_emoji)
        context.user_data['current_window'] = (0, min(WINDOW_SIZE, df_size))
        # Get the position of the user in the current leaderboard
        user_pos_r = leaderboard_to_show[leaderboard_to_show['player_id'] == query.from_user.id].index
        if len(user_pos_r) == 0:
            user_pos = None
        else:
            user_pos = user_pos_r[0]

        # Get the row of the user in the current leaderboard (it's not the index, just the row number!!)
        user_row_r = np.where(leaderboard_to_show['player_id'] == query.from_user.id)[0]
        if len(user_row_r) > 0:
            user_row = user_row_r[0]
        else:
            user_row = None


    leaderboard_window = leaderboard_to_show.iloc[context.user_data['current_window'][0]:context.user_data['current_window'][1], :]
    leaderboard_window = leaderboard_window[['position', 'alias', 'group_name', 'total_wins', 'total_loses', 'total_nulls']]

    msg_leaderboard = "```\n"
    msg_leaderboard += f"{'Pos.':<8}{'Alias':<16}{'Grupo':<8}{'W.':<4}{'L.':<4}{'N.':<3}\n"
    msg_leaderboard += '-'*50 + '\n'
    # print(user_row, user_pos)
    for i in range(len(leaderboard_window)):
        if leaderboard_window.iloc[i].name == user_pos:
            msg_leaderboard += f"{'‼️'+str(leaderboard_window.iloc[i]['position']):<7}{leaderboard_window.iloc[i]['alias']:<16}{leaderboard_window.iloc[i]['group_name']:<8}{leaderboard_window.iloc[i]['total_wins']:03d} {leaderboard_window.iloc[i]['total_loses']:03d} {leaderboard_window.iloc[i]['total_nulls']:02d}\n"
        else:
            msg_leaderboard += f"{str(leaderboard_window.iloc[i]['position']):<8}{leaderboard_window.iloc[i]['alias']:<16}{leaderboard_window.iloc[i]['group_name']:<8}{leaderboard_window.iloc[i]['total_wins']:03d} {leaderboard_window.iloc[i]['total_loses']:03d} {leaderboard_window.iloc[i]['total_nulls']:02d}\n"
    msg_leaderboard += "```"
    leaderboard_str = f"*Mostrando filas {context.user_data['current_window'][0]+1} a {context.user_data['current_window'][1]} de {len(leaderboard_to_show)}. GRUPO: {context.user_data['current_group']}*\n\n"
    leaderboard_str += msg_leaderboard
    leaderboard_str = leaderboard_str.replace('.', '\.').replace('(' , '\(').replace(')', '\)').replace('|', '\|')

    # Edit the message
    buttons = LB_BUTTONS
    if reply:
        await context.bot.answer_callback_query(query.id, text=reply, show_alert=False)
    await query.answer()
    await query.edit_message_text(text=leaderboard_str, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))


async def ninjabattle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, la práctica 3 ha terminado. Nos vemos muy pronto con la práctica 4 😈😱')
    # return ConversationHandler.END
    
    # Check if it is a user chat or a group chat
    if update.message.chat.type != 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text='Esto mejor mándamelo por privado. ¿No querrás que nos copiemos de ti? 😳', reply_to_message_id=update.message.message_id)
        return ConversationHandler.END
    # Check if the user is registered
    the_user = get_full_user(update.message.from_user.id)
    if the_user is None:
        await context.bot.send_message(chat_id=update.message.chat_id, text='Tienes que estar registrado para poder subir tu solución. Escribe /start para iniciar el proceso.')
        return ConversationHandler.END

    # if the_user['group'] != 'PROFES':
    #     await context.bot.send_message(chat_id=update.message.chat_id, text='A ver, tranquilidad. Aún estoy en pruebas. Ya avisarán los profesores cuando se pueda usar el bot.')
    #     return ConversationHandler.END
    # Randomly with a 1/20 probability, send a message reminding to read the instructions instead of running the upload
    if random.randint(1, 20) == 1:
        await context.bot.send_message(chat_id=update.message.chat_id, text='🚨🚨 ¡Hola! Aprovecho para recordarte que debes leer mis instrucciones y las preguntas frecuentes si no lo has hecho aún. '
                                                                            'Es importante para conocer bien cómo funciono, y evitar a los profesores responder 100 veces las mismas preguntas. '
                                                                            'Para ello, tienes los comandos /about, /help y /faq. Si no los has leído, aprovecha ahora. Después vuelve a escribirme /upload. '
                                                                            'Si ya lo habías leído todo, siento la interrupción. ¡Gracias! 🚨🚨')
        return ConversationHandler.END
    # Get the user's folder. It is a folder named with the telegram id of the user.
    user_folder = NINJA_FOLDER + str(update.message.from_user.id)
    # If the folder doesn't exist, create it.
    if not os.path.exists(user_folder):
        os.mkdir(user_folder)

    await context.bot.send_message(chat_id=update.message.chat_id, text=f'¡Hola, {the_user["alias"]}, del grupo {the_user["group"]}! ¡Ánimo, que ya queda poco!')
    # Check if arguments have been provided.
    if not context.args:
        await context.bot.send_message(chat_id=update.message.chat_id, text='¿Preparad@ para luchar contra los ninjas? Dime, separados por espacio, los números de los ninjas contra los que quieres luchar (o ALL para luchar contra los 3 ninjas de la evaluación, 1-3). Esto se lo puedes pasar también como argumentos al comando /battleninja (p.e. /battleninja ALL o /battleninja 0 3)')
        return NINJA
    else:
        return await get_ninjas(update, context, msg=' '.join(context.args))
    
async def get_ninjas(update: Update, context: ContextTypes.DEFAULT_TYPE, msg=None):
    # If message is None, get the message from the update.
    if msg is None:
        msg = update.message.text
    # Convert msg in a list.
    args = msg.split(' ')
    # Check the arguments. They must be non-empty, and all the values numeric, or ALL.
    if not args:
        await context.bot.send_message(chat_id=update.message.chat_id, text='No me has dicho ningún ninja 😅.')
        return NINJA
    if not all(arg.isnumeric() or arg == 'ALL' for arg in args):
        await context.bot.send_message(chat_id=update.message.chat_id, text='Alguno de los ninjas que me has dicho no es válido 😅.')
        return NINJA
    # If 'ALL' has been provided, get all the ninjas.
    if 'ALL' in args:
        context.user_data['ninjas'] = [1, 2, 3]
    else:
        context.user_data['ninjas'] = [int(arg) for arg in args]

    await context.bot.send_message(chat_id=update.message.chat_id, text='¡Genial! Ahora necesito tus ficheros AIPlayer.cpp y AIPlayer.h.')
    context.user_data['files'] = []
    return FILES

async def get_files_ninja(update, context):
    # Check if the user has sent the /cancel command
    if update.message.text == '/cancel':
        await context.bot.send_message(chat_id=update.message.chat_id, text='Muy bien. Si quieres subir tus ficheros más tarde, vuelve a escribirme /battleninja.')
        return ConversationHandler.END

    # Check if the message contains a file
    if not update.message.document:
        # If not, ask the user to send a file
        await context.bot.send_message(chat_id=update.message.chat_id, text='Por favor, necesito los ficheros.')
        # update.message.reply_text('Please send me a file.')
        return FILES

    # Get the file information
    file = await context.bot.get_file(update.message.document.file_id)
    file_name = update.message.document.file_name
    #file = update.message.document
    file_extension = os.path.splitext(file_name)[1].lower()

    if file_name in  ['AIPlayer.cpp', 'AIPlayer.h']:
        # Check if it was already sent.
        if file_name in context.user_data['files']:
            await context.bot.send_message(chat_id=update.message.chat_id, text='Ya me habías enviado este archivo. Si te has confundido de versión, escribe /cancel y vuelve a empezar.')
            return FILES
        else:
            # Download the file and store it in memory
            # Create a folder with the telegram id as a name.
            os.makedirs(os.path.join(os.getcwd(), NINJA_FOLDER, str(update.message.from_user.id)), exist_ok=True)
            # Create a folder inside called 'uploads'
            os.makedirs(os.path.join(os.getcwd(), NINJA_FOLDER, str(update.message.from_user.id), 'uploads'), exist_ok=True)
            # Create a folder inside with the current timestamp.
            if 'curr_timestamp' not in context.user_data:
                context.user_data['curr_timestamp'] = str(datetime.datetime.now())
            os.makedirs(os.path.join(os.getcwd(), NINJA_FOLDER, str(update.message.from_user.id), 'uploads', context.user_data['curr_timestamp']), exist_ok=True)
            # Download the file to the folder.
            await file.download_to_drive(os.path.join(os.getcwd(), NINJA_FOLDER, str(update.message.from_user.id), 'uploads', context.user_data['curr_timestamp'], file_name))
            if file_name == 'AIPlayer.h':
                is_ok = check_integrity(os.path.join(os.getcwd(), NINJA_FOLDER, str(update.message.from_user.id), 'uploads', context.user_data['curr_timestamp'], file_name))
                #is_ok = True
                if not is_ok:
                    msg = "🚨🚨🚨 La cabecera del método think tiene que ser `virtual void think(color & c_piece,  int & id_piece, int & dice) const;`\." \
                        " No se puede modificar\. Arréglalo si quieres que pueda ejecutar tu código\. 🚨🚨🚨"
                    await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
                    return ConversationHandler.END

            context.user_data['files'].append(file_name)

            remaining_files = [f for f in ['AIPlayer.cpp', 'AIPlayer.h'] if f not in context.user_data['files']]
            if len(remaining_files) == 0:
                await context.bot.send_message(chat_id=update.message.chat_id, text='¡Gracias! He recibido todos los ficheros. ¿Qué id de tus heurísticas quieres que use para la batalla?')
                # Call to sbatch and submit the job.
                return HEURISTIC
            else:
                files_str = ', '.join(remaining_files)
                await context.bot.send_message(chat_id=update.message.chat_id, text=f'Me falta(n) el/los ficheros: {files_str}.')
                return FILES
    else:
        remaining_files = [f for f in ['AIPlayer.cpp', 'AIPlayer.h'] if f not in context.user_data['files']]
        files_str = ', '.join(remaining_files)
        await context.bot.send_message(chat_id=update.message.chat_id, text=f'Lo que me has mandado no me sirve. Me falta(n) el/los ficheros: {files_str}.')
        return FILES
    
async def get_heuristic(update, context):
    # Check if the user has sent a single argument and it is a number.
    args = update.message.text.split(' ')
    if not args or not args[0].isnumeric():
        await context.bot.send_message(chat_id=update.message.chat_id, text='No me has dicho ningún id válido para la heurística 😅.')
        return HEURISTIC
    # Any number is valid. Start the script for the battle.
    context.user_data['heuristic_id'] = args[0]
    # Call to sbatch and submit the job.
    # Get a string for the ninja values list (separated by spaces).
    ninjas_str = ' '.join([str(n) for n in context.user_data['ninjas']])
    # Arguments for the script: timestamp, heuristic_id, ninjas
    #await context.bot.send_message(chat_id=update.message.chat_id, text=f'sbatch -J {update.message.from_user.id} run_executions_ninja.sh "{context.user_data["curr_timestamp"]}" {context.user_data["heuristic_id"]} {ninjas_str}')

    insert_P3_submission(update.message.from_user.id, context.user_data['curr_timestamp'], context.user_data['heuristic_id'])
    insert_P3_submission_metrics(update.message.from_user.id, context.user_data['curr_timestamp'])
    os.system(f'sbatch -J {update.message.from_user.id} run_executions_ninja.sh "{context.user_data["curr_timestamp"]}" {context.user_data["heuristic_id"]} {ninjas_str}')
    context.user_data.pop('curr_timestamp')
    await context.bot.send_message(chat_id=update.message.chat_id, text='¡Genial! Pongo a ejecutar tu solución y te aviso cuando estén los resultados.')
    await context.bot.send_message(chat_id=update.message.chat_id, text='Te mandaré un mensaje al empezar también, dentro de un minuto más o menos. Si ese mensaje no te llega, puede que haya habido un error. En tal caso, repite el proceso.')
    
    return ConversationHandler.END


async def notify(update, context):
    # Check if it is a user chat or a group chat
    if update.message.chat.type != 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text='Mejor hablamos por privado. 😅', reply_to_message_id=update.message.message_id)
        return ConversationHandler.END
    # Check if the user is registered
    the_user = get_full_user(update.message.from_user.id)
    if the_user is None:
        await context.bot.send_message(chat_id=update.message.chat_id, text='Tienes que estar registrado primero. Escribe /start para iniciar el proceso.')
        return ConversationHandler.END

    notify_mode = get_P3_user_notifications(update.message.from_user.id)

    msg = "Aquí puedes configurar las notificaciones que quieres recibir del torneo. ¿Qué quieres hacer?\n\n"
    msg += f"{'🔘' if notify_mode == 2 else '⚫️'} Avísame con el resultado de cada partida del torneo.\n\n"
    msg += f"{'🔘' if notify_mode == 1 else '⚫️'} Avísame solo cuando esté el resultado final del torneo.\n\n"
    msg += f"{'🔘' if notify_mode == 0 else '⚫️'} No me avises.\n"

    buttons = [[InlineKeyboardButton("Todas las partidas.", callback_data='notify_always')], [InlineKeyboardButton("Solo el torneo.", callback_data='notify_results')], [InlineKeyboardButton("No me avises.", callback_data='notify_never')]]

    await context.bot.send_message(chat_id=update.message.chat_id, text=msg, reply_markup=InlineKeyboardMarkup(buttons))

async def notify_callback(update, context):
    query = update.callback_query
    notify_mode = 2 if query.data == 'notify_always' else 1 if query.data == 'notify_results' else 0

    set_P3_user_notifications(update.callback_query.from_user.id, notify_mode)

    # Update the tick on the previous message
    msg = "Aquí puedes configurar las notificaciones que quieres recibir del torneo. ¿Qué quieres hacer?\n\n"
    msg += f"{'🔘' if notify_mode == 2 else '⚫️'} Avísame con el resultado de cada partida del torneo.\n\n"
    msg += f"{'🔘' if notify_mode == 1 else '⚫️'} Avísame solo cuando esté el resultado final del torneo.\n\n"
    msg += f"{'🔘' if notify_mode == 0 else '⚫️'} No me avises.\n"

    buttons = [[InlineKeyboardButton("Todas las partidas.", callback_data='notify_always')], [InlineKeyboardButton("Solo el torneo.", callback_data='notify_results')], [InlineKeyboardButton("No me avises.", callback_data='notify_never')]]

    try:
        await context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=msg, reply_markup=InlineKeyboardMarkup(buttons))
    except:
        pass

    await context.bot.answer_callback_query(query.id, text=f"¡He actualizado tus preferencias! Ahora solo recibirás notificaciones {'con el resultado de cada partida del torneo.' if notify_mode == 2 else 'cuando esté el resultado final del torneo.' if notify_mode == 1 else 'nunca.'}")
    await query.answer()

async def cuantoqueda(update, context):
    # Get the output (int) of the command echo $((`squeue -u profesia | wc -l` - 6))
    output = subprocess.check_output("echo $((`squeue -u profesia | grep tour- | wc -l`))", shell=True)
    # Convert the output to int (remove the b' and the \n' at the end)
    cuanto = int(output.decode('utf-8').replace("\\n'", ""))
    # Prepare the msg to send
    if cuanto > 10000:
        msg = f"😭 ¡Quedan {cuanto} partidas para conocer el resultado del torneo!"
    elif cuanto > 3000:
        msg = f"😴 ¡Quedan solo {cuanto} partidas para conocer el resultado del torneo!"
    elif cuanto > 1000:
        msg = f"🥱 ¡Quedan solo {cuanto} partidas para conocer el resultado del torneo!"
    elif cuanto > 500:
        msg = f"🤨 ¡Quedan solo {cuanto} partidas para conocer el resultado del torneo!"
    elif cuanto > 100:
        msg = f"😬 ¡Quedan solo {cuanto} partidas para conocer el resultado del torneo!"
    elif cuanto > 50:
        msg = f"😱 ¡Quedan solo {cuanto} partidas para conocer el resultado del torneo!"
    elif cuanto > 10:
        msg = f"🤯 ¡Quedan solo {cuanto} partidas para conocer el resultado del torneo!"
    elif cuanto > 5:
        msg = f"🤩 ¡Quedan solo {cuanto} partidas para conocer el resultado del torneo!"
    elif cuanto > 2:
        msg = f"🥳 ¡Quedan solo {cuanto} partidas para conocer el resultado del torneo!"
    elif cuanto > 1:
        msg = f"🥵 ¡QUEDAN SOLO LAS {cuanto} ÚLTIMAS PARTIDAS PARA CONOCER EL RESULTADO DEL TORNEO!"
    elif cuanto == 1:
        msg = f"🔥🚨🚨 ¡ES LA ÚLTIMA! ¡SOLO QUEDA UNA PARTIDA PARA CONOCER EL RESULTADO DEL TORNEO! 🚨🚨🔥"
    else:
        msg = f"🎉🎊🎉🎊🎉🎊 ¡YA ESTÁ! ¡YA SE HAN JUGADO TODAS LAS PARTIDAS! ¡EN BREVE CONOCEREMOS EL RESULTADO DEL TORNEO! 🎉🎊🎉🎊🎉🎊"
    # Send the message
    if update.message.chat.type == 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg)
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg, reply_to_message_id=update.message.message_id)


async def test_poda(update, context):
    buttons = [[InlineKeyboardButton('ValoracionTest vs ValoracionTest', callback_data='testpoda-00')],
               [InlineKeyboardButton('ValoracionTest vs Ninja 1', callback_data='testpoda-01'), InlineKeyboardButton('Ninja 1 vs ValoracionTest', callback_data='testpoda-10')],
               [InlineKeyboardButton('ValoracionTest vs Ninja 2', callback_data='testpoda-02'), InlineKeyboardButton('Ninja 2 vs ValoracionTest', callback_data='testpoda-20')],
               [InlineKeyboardButton('ValoracionTest vs Ninja 3', callback_data='testpoda-03'), InlineKeyboardButton('Ninja 3 vs ValoracionTest', callback_data='testpoda-30')],
               [InlineKeyboardButton('ValoracionTest vs ValoracionTest usando MiniMax', callback_data='testpoda-mm')],
               ]
    
    await context.bot.send_message(chat_id=update.message.chat_id, text='¿Qué quieres que te enseñe?', reply_markup=InlineKeyboardMarkup(buttons))


async def test_poda_callback(update, context):
    # Get the callback data
    data = update.callback_query.data
    # Check the data
    if data == 'testpoda-00':
        msg = f"Este es el resultado que debería dar una partida de ValoracionTest contra sí misma usando poda alfa-beta.\n"
        msg += f"Puedes seguir la partida completa jugando con el comando: `./build/ParchisGame --p1 Ninja 0 J1 --p2 Ninja 0 J2`"
    elif data == 'testpoda-01':
        msg = f"Este es el resultado que debería dar una partida de ValoracionTest usando poda alfa-beta contra el Ninja 1.\n"
        msg += f"Puedes seguir la partida completa jugando con el comando: `./build/ParchisGame --p1 Ninja 0 J1 --p2 Ninja 1 J2`"
    elif data == 'testpoda-10':
        msg = f"Este es el resultado que debería dar una partida del Ninja 1 contra ValoracionTest usando poda alfa-beta.\n"
        msg += f"Puedes seguir la partida completa jugando con el comando: `./build/ParchisGame --p1 Ninja 1 J1 --p2 Ninja 0 J2`"
    elif data == 'testpoda-02':
        msg = f"Este es el resultado que debería dar una partida de ValoracionTest usando poda alfa-beta contra el Ninja 2.\n"
        msg += f"Puedes seguir la partida completa jugando con el comando: `./build/ParchisGame --p1 Ninja 0 J1 --p2 Ninja 2 J2`"
    elif data == 'testpoda-20':
        msg = f"Este es el resultado que debería dar una partida del Ninja 2 contra ValoracionTest usando poda alfa-beta.\n"
        msg += f"Puedes seguir la partida completa jugando con el comando: `./build/ParchisGame --p1 Ninja 2 J1 --p2 Ninja 0 J2`"
    elif data == 'testpoda-03':
        msg = f"Este es el resultado que debería dar una partida de ValoracionTest usando poda alfa-beta contra el Ninja 3.\n"
        msg += f"Puedes seguir la partida completa jugando con el comando: `./build/ParchisGame --p1 Ninja 0 J1 --p2 Ninja 3 J2`"
    elif data == 'testpoda-30':
        msg = f"Este es el resultado que debería dar una partida del Ninja 3 contra ValoracionTest usando poda alfa-beta.\n"
        msg += f"Puedes seguir la partida completa jugando con el comando: `./build/ParchisGame --p1 Ninja 3 J1 --p2 Ninja 0 J2`"
    elif data == 'testpoda-mm':
        msg = f"Este es el resultado que debería dar una partida de ValoracionTest contra sí misma usando MiniMax.\n"
        msg += f"Según cómo lo hayas implementado podría haber dos opciones distintas válidas que llevan a estos dos resultados.\n"
        msg += f"Puedes seguir las partidas completa jugando con los comandos: `./build/ParchisGame --p1 Ninja -1 J1 --p2 Ninja -1 J2` y `./build/ParchisGame --p1 Ninja -20 J1 --p2 Ninja -20 J2`"

    msg = msg.replace('(' , '\(').replace(')', '\)').replace('.', '\.').replace('-', '\-')

     # Check if there is a file {test_name}.png inside the test_pngs folder.
    if data != 'testpoda-mm' and os.path.exists('test_pngs/' + data + '.png'):
        await context.bot.send_photo(chat_id=update.callback_query.message.chat_id, photo=open('test_pngs/' + data + '.png', 'rb'), caption=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
    elif data == 'testpoda-mm' and os.path.exists('test_pngs/testpoda-mm-a.png') and os.path.exists('test_pngs/testpoda-mm-b.png'):
        await context.bot.sendMediaGroup(chat_id=update.callback_query.message.chat_id, media=[telegram.InputMediaPhoto(open('test_pngs/testpoda-mm-a.png', 'rb')), telegram.InputMediaPhoto(open('test_pngs/testpoda-mm-b.png', 'rb'))], caption=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
    else:
        await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)

    # End the query.
    await update.callback_query.answer()


async def leave_tour(update, context):
    await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, la práctica 3 ha terminado. Nos vemos muy pronto con la práctica 4 😈😱')
    return ConversationHandler.END

    if update.message.chat.type != 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text='Mejor hablamos por privado. 😅', reply_to_message_id=update.message.message_id)
        return ConversationHandler.END
    unregister_P3_tour_player(update.message.from_user.id)

    await context.bot.send_message(chat_id=update.message.chat_id, text='¡Perfecto! Te he desapuntado del torneo. Si quieres volver a apuntarte, puedes escribirme /tourjoin.')

async def tour(update, context):
    await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, la práctica 3 ha terminado. Nos vemos muy pronto con la práctica 4 😈😱')
    return ConversationHandler.END
    # Check if it is a user chat or a group chat
    if update.message.chat.type != 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text='Esto mejor mándamelo por privado. ¿No querrás que nos copiemos de ti? 😳', reply_to_message_id=update.message.message_id)
        return ConversationHandler.END
    # Check if the user is registered
    the_user = get_full_user(update.message.from_user.id)
    if the_user is None:
        await context.bot.send_message(chat_id=update.message.chat_id, text='Tienes que estar registrado para poder subir tu solución. Escribe /start para iniciar el proceso.')
        return ConversationHandler.END
    
    # Randomly with a 1/20 probability, send a message reminding to read the instructions instead of running the upload
    if random.randint(1, 20) == 1:
        await context.bot.send_message(chat_id=update.message.chat_id, text='🚨🚨 ¡Hola! Aprovecho para recordarte que debes leer mis instrucciones y las preguntas frecuentes si no lo has hecho aún. '
                                                                            'Es importante para conocer bien cómo funciono, y evitar a los profesores responder 100 veces las mismas preguntas. '
                                                                            'Para ello, tienes los comandos /about, /help y /faq. Si no los has leído, aprovecha ahora. Después vuelve a escribirme /upload. '
                                                                            'Si ya lo habías leído todo, siento la interrupción. ¡Gracias! 🚨🚨')
        return ConversationHandler.END
    
    
    # Get the user's folder. It is a folder named with the telegram id of the user.
    user_folder = TOUR_FOLDER + str(update.message.from_user.id)
    # If the folder doesn't exist, create it.
    if not os.path.exists(user_folder):
        os.mkdir(user_folder)

    name = the_user['alias']
    group = the_user['group']

    context.user_data['name'] = name
    context.user_data['group'] = group
    # Send a message indicating that the bot already knows the name and go directly to FILES.
    await context.bot.send_message(chat_id=update.message.chat_id, text=f"¡Hola de nuevo, {name}, del grupo {group}!")
    # Ask the user for the files
    await context.bot.send_message(chat_id=update.message.chat_id, text='Cuando quieras puedes enviarme tus ficheros AIPlayer.cpp y AIPlayer.h.')
    context.user_data['files'] = []

    # Return the FILES state
    return FILES

async def get_files_tour(update, context):
    # Check if the message contains a file
    if not update.message.document:
        # If not, ask the user to send a file
        await context.bot.send_message(chat_id=update.message.chat_id, text='Por favor, necesito los ficheros.')
        # update.message.reply_text('Please send me a file.')
        return FILES

    # Get the file information
    file = await context.bot.get_file(update.message.document.file_id)
    file_name = update.message.document.file_name
    #file = update.message.document
    file_extension = os.path.splitext(file_name)[1].lower()

    if file_name in  ['AIPlayer.cpp', 'AIPlayer.h']:
        # Check if it was already sent.
        if file_name in context.user_data['files']:
            await context.bot.send_message(chat_id=update.message.chat_id, text='Ya me habías enviado este archivo. Si te has confundido de versión, escribe /cancel y vuelve a empezar.')
            return FILES
        else:
            # Download the file and store it in memory
            # Create a folder with the telegram id as a name.
            os.makedirs(os.path.join(os.getcwd(), TOUR_FOLDER, str(update.message.from_user.id)), exist_ok=True)
            
            # Download the file to the folder.
            await file.download_to_drive(os.path.join(os.getcwd(), TOUR_FOLDER, str(update.message.from_user.id), file_name))
            context.user_data['files'].append(file_name)

            remaining_files = [f for f in ['AIPlayer.cpp', 'AIPlayer.h'] if f not in context.user_data['files']]
            if len(remaining_files) == 0:
                await context.bot.send_message(chat_id=update.message.chat_id, text='¡Gracias! He recibido todos los ficheros. ¿Qué id de tus heurísticas quieres que use para la batalla?')
                # Call to sbatch and submit the job.
                return HEURISTIC
            else:
                files_str = ', '.join(remaining_files)
                await context.bot.send_message(chat_id=update.message.chat_id, text=f'Me falta(n) el/los ficheros: {files_str}.')
                return FILES
    else:
        remaining_files = [f for f in ['AIPlayer.cpp', 'AIPlayer.h'] if f not in context.user_data['files']]
        files_str = ', '.join(remaining_files)
        await context.bot.send_message(chat_id=update.message.chat_id, text=f'Lo que me has mandado no me sirve. Me falta(n) el/los ficheros: {files_str}.')
        return FILES

async def get_heuristic_tour(update, context):
    # Check if the user has sent a single argument and it is a number.
    args = update.message.text.split(' ')
    if not args or not args[0].isnumeric():
        await context.bot.send_message(chat_id=update.message.chat_id, text='No me has dicho ningún id válido para la heurística 😅.')
        return HEURISTIC
    # Any number is valid.
    heuristic_id = int(args[0])

    the_user = get_full_user(update.message.from_user.id)
    if the_user is None:
        await context.bot.send_message(chat_id=update.message.chat_id, text='Ha habido un error al recuperar tus datos. Por favor, vuelve a empezar.')
        return ConversationHandler.END
    

    register_P3_tour_player(telegram_id=the_user['telegram_id'], player_type='AI', heuristic=heuristic_id)
    
    await context.bot.send_message(chat_id=update.message.chat_id, text='¡Perfecto! Ya estás dentro del torneo. ¡Mucha suerte! 🍀')
    msg_tour_info = """
    El torneo se realizará todas las noches desde las 00:00 hasta que se ejecuten todas las partidas. El torneo definitivo será la noche de la entrega.
    Puedes actualizar o retirar tu código siempre que quieras. El código se utilizará en el torneo siempre que se envíe antes de las 00:00.
    Importante: termina la conversación conmigo siempre que actualices tu código, si no la heurística que se utilizará será la que tenías la última vez que terminaste la conversación.
    El formato del torneo será, en principio, todos contra todos, aunque puede cambiar en función del número de participantes.

    Por defecto, recibirás un mensaje con el resultado de cada partida. Si quieres cambiar esto, cambia tu configuración con el comando /notify.
    """
    await context.bot.send_message(chat_id=update.message.chat_id, text=msg_tour_info)
    return ConversationHandler.END

async def cancel(update, context):
    # End the conversation if the user cancels
    await context.bot.send_message(chat_id=update.message.chat_id, text='Muy bien. Puedes repetir este proceso más tarde volviendo a utilizar el comando anterior.')
    if 'curr_timestamp' in context.user_data:
        context.user_data.pop('curr_timestamp')
    return ConversationHandler.END

async def stop_solution(update, context):
    # Cancel the current solution
    os.system(f'scancel -n {update.message.from_user.id}')
    # Remove the 'software' folder inside the user folder (if it exists)
    if os.path.exists(os.path.join(os.getcwd(), DB_FOLDER, str(update.message.from_user.id), 'software')):
        shutil.rmtree(os.path.join(os.getcwd(), DB_FOLDER, str(update.message.from_user.id), 'software'))
    await context.bot.send_message(chat_id=update.message.chat_id, text='La solución que tenías en ejecución ha sido cancelada. Puedes volver a enviar una nueva solución cuando quieras.')

async def faq(update, context):
    msg = """
    - *El programa me compila en local pero no cuando se lo paso al bot:* Revisa que no hayas modificado ficheros más allá del AIPlayer.cpp y AIPlayer.h. Además, cuidado si has incluido en tu código caracteres extraños o directivas "ilegales" en el C++ estándar de las que funcionan con -fpermissive. Revisa también los warnings que produce el código tuyo propio al compilar.
    
    - *Los resultados me salen bien pero el bot dice que no.* Asegúrate de tener el software actualizado y comprueba que el método think en AIPlayer.h sigue siendo virtual. Yo ejecuto siempre con la última versión del código. Si no, seguramente tienes alguna variable sin inicializar o algún acceso ilegal a memoria. Comprueba si en la versión sin gráfica también te dan los mismos resultados. También prueba a pasarle algún programa como valgrind y analizar su salida.
    
    - *El bot no termina.* El bot pone un timeout de 1 hora. De todas formas una partida debería durar bastante menos. Revisa tu código y comprueba que en local funciona bien.
    
    - *El bot no termina pero a mí en local sí.* Lo más posible es que sea una situación como la del segundo caso.
    
    - *¿Qué es `valgrind`?* `valgrind` es una herramienta que te permite analizar tu programa para ver si hay errores de memoria (invalid reads, invalid writes, leaks, etc.) o variables sin inicializar (uninitialized values). Puedes usarlo para ver si hay errores en tu programa que no se estén manifestando en tus ejecuciones. No siempre estos errores resultan en error, depende del entorno de ejecución y del sistema operativo que una ejecución con errores provoque o no fallos de segmentación. Puedes usarlo con el comando `valgrind ./practica1(SG) <argumentos del programa>`. Recomiendo probarlo tanto con gráfica como sin gráfica.
    
    - *¿Mi nota en la práctica depende de la leaderboard?* No, la leaderboard es solo un entretenimiento para quien quiera picarse con sus compañeros. La nota de la práctica no depende de la posición ni de haber participado en ella.

    """

    msg = msg.replace('.', '\.').replace('(' , '\(').replace(')', '\)').replace('+', '\+').replace('-', '\-')

    if update.message.chat.type == 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_to_message_id=update.message.message_id)

async def about(update, context):
    msg = """
        ¡Hola! Soy el bot de la práctica 3 de IA. Estoy aquí para ayudarte a evaluar tus soluciones y darte una estimación de cómo vas con la práctica.

        Tengo tres funciones principales que podéis utilizar:
        - Comprobar los resultados que produce vuestro algoritmo de búsqueda, y ver si coinciden con lo que debería proporcionar el algoritmo MiniMax o la poda.
        - Ejecutar partidas contra los ninjas en remoto y en paralelo, todas a la vez, para acelerar el proceso.
        - Participar en el torneo definitivo de parchís. ¿Quién se alzará con la victoria? (Daremos más detalles sobre el torneo en breve pero ya podéis subir vuestros códigos para participar).
        Podéis consultar cómo acceder a cada funcionalidad escribiéndole el comando /help al bot. Recordad que, si no lo habéis hecho en las otras prácticas, tenéis que registraros primero con /start. 
        Si tenéis cualquier problema de FUNCIONAMIENTO O ERRORES EN EL BOT, podéis escribirnos al canal SOPORTE BOT del grupo, donde trataremos de solucionarlo.

        *IMPORTANTE: EL BOT ES UNA AYUDA, PERO NO DEBÉIS DEPENDER DE ÉL PARA TODO. ES FUNDAMENTAL TAMBIÉN PROBAR LAS PARTIDAS EN LOCAL EN VUESTRO SOFTWARE Y ANALIZAR EL COMPORTAMIENTO DE VUESTRA HEURÍSTICA EN EL SOFTWARE PRIMERO*

        Esperamos que el bot os facilite un poco las cosas y que además de aprender los algoritmos, disfrutéis con la práctica jugando al parchís. Ánimo, que ya queda poco!

    """.replace('.', '\.').replace('-', '\-').replace('(' , '\(').replace(')', '\)').replace('!', '\!')

    if update.message.chat.type == 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg, reply_to_message_id=update.message.message_id, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)

async def normal(update, context):
    # Check if it is a user chat or a group chat
    if update.message.chat.type == 'private':
        # BEHAVIOUR FOR PRIVATE CHATS
        # Check if the user message contains sentences like "Hola" or "Buenos días"
        # if update.message.text.lower() in ['hola', 'buenos días', 'buenos dias', 'buenas tardes', 'buenas noches', 'buenas']:
        if RE_HELLO.search(unidecode.unidecode(update.message.text)):
            answer_choices = ['¡Hola, bienvenid@! Utiliza el comando /help para ver qué puedo hacer por ti.',
                            '¡Buenas! ¿En qué puedo ayudarte? Utiliza el comando /help si necesitas información.',
                            '¡Hola! ¿Qué tal? Utiliza el comando /help si necesitas ayuda.']
            await context.bot.send_message(chat_id=update.message.chat_id, text=random.choice(answer_choices))

        # Check if the user message contains sentences like "Adiós" or "Hasta luego"
        # elif update.message.text.lower() in ['adiós', 'hasta luego', 'hasta pronto', 'hasta mañana', 'adios']:
        elif RE_GOODBYE.search(unidecode.unidecode(update.message.text)):
            answer_choices = ['¡Hasta luego! Gracias por utilizarme.',
                            '¡Nos vemos! Cuando necesites subir una solución aquí estoy.',
                            '¡Adiós! Nos vemos pronto.']
            await context.bot.send_message(chat_id=update.message.chat_id, text=random.choice(answer_choices))

        # Check if the user message contains sentences like "Gracias" or "Muchas gracias"
        elif RE_THANKS.search(unidecode.unidecode(update.message.text)):
            answer_choices = ['¡De nada! ¡Es un placer ayudarte! ¡Hasta pronto!',
                            '¡No hay de qué! ¡Espero haberte ayudado! Aquí estoy para lo que necesites.',
                            '¡A ti por participar! Cuando necesites subir una solución aquí estoy.']
            await context.bot.send_message(chat_id=update.message.chat_id, text=random.choice(answer_choices))

    # BEHAVIOUR ON ALL CHATS
            
    # Check if the user message sentences meaning "resultados diferentes" or "resultados distintos"
    if RE_DIFFERENT_RESULTS.search(unidecode.unidecode(update.message.text)):
        await context.bot.send_message(chat_id=update.message.chat_id, text='Si el bot te da resultados diferentes a lo que te sale ejecutando tú, o directamente no termina pero a ti en local sí, '
                                                                            'asegúrate antes de nada de tener el software en su versión más reciente. Si no, '
                                                                            'es posible que tengas alguna variable sin inicializar o algún acceso ilegal a memoria. '
                                                                            'Comprueba si en la versión sin gráfica también te dan los mismos resultados. '
                                                                            'También prueba a pasarle algún programa como `valgrind` y analizar su salida '
                                                                            'para ver si hay errores de memoria. '
                                                                            'Puedes usar el comando /faq para ver más preguntas frecuentes.'
                                                                            .replace('.', '\.').replace('-', '\-'),
                                       parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
                                       reply_to_message_id=update.message.message_id)

    elif RE_VALGRIND.search(unidecode.unidecode(update.message.text)):
        await context.bot.send_message(chat_id=update.message.chat_id, text='`valgrind` es una herramienta que te permite analizar tu programa para ver si hay errores de memoria (invalid reads, invalid writes, leaks, etc.) o variables sin inicializar (uninitialized values). '
                                                                            'Puedes usarlo para ver si hay errores en tu programa que no se estén manifestando en tus ejecuciones. '
                                                                            'No siempre estos errores resultan en error, depende del entorno de ejecución y del sistema operativo que una ejecución con errores provoque o no fallos de segmentación.'
                                                                            'Puedes usarlo con el comando `valgrind ./practica1(SG) <argumentos del programa>`. '
                                                                            'Recomiendo probarlo tanto con gráfica como sin gráfica. '
                                                                            'Puedes usar el comando /faq para ver más preguntas frecuentes.'
                                                                            .replace('.', '\.').replace('-', '\-'),
                                       parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
                                       reply_to_message_id=update.message.message_id)
    
    elif RE_NOTABOT.search(unidecode.unidecode(update.message.text)):
        await context.bot.send_message(chat_id=update.message.chat_id, text='No, para la evaluación se usarán unos mapas de evaluación similares a los de la práctica pero podrían ser diferentes. '
                                                                            'Yo solo te doy una estimación de cómo vas con la práctica. Pero lo normal es que la estimación no se aleje demasiado de la realidad, '
                                                                            'y en general, mi estimación debería ser pesimista, ya que ejecuto en muchos mapas diferentes y algunos de ellos son bastante difíciles. '
                                                                            'No creo que los profesores sean tan duros como yo 😈. '
                                                                            'Puedes usar el comando /faq para ver más preguntas frecuentes.'
                                                                            .replace('.', '\.').replace('-', '\-'),
                                        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
                                        reply_to_message_id=update.message.message_id)

    elif RE_NOTALB.search(unidecode.unidecode(update.message.text)):
        await context.bot.send_message(chat_id=update.message.chat_id, text='No, la leaderboard es solo un entretenimiento para quien quiera picarse con sus compañeros. La nota de la práctica no depende de la posición ni de haber participado en ella.'
                                                                            'Puedes usar el comando /faq para ver más preguntas frecuentes.'
                                                                            .replace('.', '\.').replace('-', '\-'),
                                        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
                                        reply_to_message_id=update.message.message_id)

    elif RE_NOCOMPILA.search(unidecode.unidecode(update.message.text)):
        await context.bot.send_message(chat_id=update.message.chat_id, text='Revisa que no hayas modificado ficheros más allá del jugador.cpp y jugador.hpp. '
                                                                            'Además, cuidado si has incluido en tu código caracteres extraños o directivas "ilegales" en el C++ estándar de las que funcionan con -fpermissive. '
                                                                            'Revisa también los warnings que produce el código tuyo propio al compilar.'
                                                                            'Puedes usar el comando /faq para ver más preguntas frecuentes.'
                                                                            .replace('.', '\.').replace('-', '\-').replace('+', '\+'),
                                        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
                                        reply_to_message_id=update.message.message_id)
        
    elif RE_CUANDO.search(unidecode.unidecode(update.message.text)):
        msg = f"La entrega está prevista para el {FECHA_ENTREGA.strftime('%d/%m/%Y')} a las {FECHA_ENTREGA.strftime('%H:%M')}.\n" \
              f"Después, se abrirá el cuestionario de autoevaluación, cuya entrega está prevista para el {FECHA_ENTREGA_CUESTIONARIO.strftime('%d/%m/%Y')} a las {FECHA_ENTREGA_CUESTIONARIO.strftime('%H:%M')}."
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg, reply_to_message_id=update.message.message_id)


async def maintenance(update, context):
    await context.bot.send_message(chat_id=update.message.chat_id, text='⚠️⚠️ ¡Hola! Ahora mismo estoy en mantenimiento. Estaré de vuelta en unos minutos. ⚠️⚠️')

async def evaluate(update, context):
    # Check if it is a user chat or a group chat
    if update.message.chat.type != 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text='No sé de qué me hablas xd', reply_to_message_id=update.message.message_id)
        return ConversationHandler.END
    # Check if the user is registered
    the_user = get_full_user(update.message.from_user.id)
    if the_user is None:
        await context.bot.send_message(chat_id=update.message.chat_id, text='No sé de qué me hablas xd')
        return ConversationHandler.END
    # Check if the user belongs to the group "PROFES"
    if the_user['group'] != 'PROFES':
        await context.bot.send_message(chat_id=update.message.chat_id, text='No sé de qué me hablas xd')
        return ConversationHandler.END
    
    # Get the first argument of the command
    if not context.args:
        context.user_data['eval_name'] = 'eval'
    else:
        # check that context.args[0] is doesn't containas a substring words result, upload or metadata.
        if any(x in context.args[0].lower() for x in ['result', 'upload', 'metadata']):
            context.user_data['eval_name'] = 'eval'
        else:
            context.user_data['eval_name'] = context.args[0].lower()
        
    await context.bot.send_message(chat_id=update.message.chat_id, text='Mándame el zip con las prácticas tal cual se descarga de PRADO.')
    return FILES

async def get_eval_files(update, context):
    if update.message.document:
        file = await context.bot.get_file(update.message.document.file_id)
        eval_folder = context.user_data['eval_name']
        # Check if it is a zip.
        if not update.message.document.file_name.endswith('.zip'):
            await context.bot.send_message(chat_id=update.message.chat_id, text='Necesito el zip con todas las prácticas tal cual se descarga de PRADO.')
            return FILES
        # Create a "eval" folder inside the user folder (if it doesn't exist)
        if not os.path.exists(os.path.join(os.getcwd(), EVAL_FOLDER, str(update.message.from_user.id), eval_folder)):
            os.makedirs(os.path.join(os.getcwd(), EVAL_FOLDER, str(update.message.from_user.id), eval_folder))
        await file.download_to_drive(os.path.join(os.getcwd(), EVAL_FOLDER, str(update.message.from_user.id), eval_folder, update.message.document.file_name))
        await context.bot.send_message(chat_id=update.message.chat_id, text=f'Recibido, comienzo la evaluación de las prácticas. Te iré informando 🫡')
        # Call the evaluation script
        os.system(f'sbatch -J {update.message.from_user.id} evaluate.sh {eval_folder}')
        return ConversationHandler.END
        
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text='No me has mandado nada.')
        return FILES


async def remind_entrega(context: ContextTypes.DEFAULT_TYPE):
    # Get the current date and time
    now = datetime.datetime.now().replace(tzinfo=pytz.timezone('Europe/Madrid'))
    # Get the time remaining until FECHA_ENTREGA (avoid the naive vs aware error)
    remaining = FECHA_ENTREGA - now
    # Get the number of remaining days.
    remaining_days = remaining.days
    print("Remaining: ", remaining)
    print("Remaining days: ", remaining_days)

    msg = ''
    # If the remaining days is multiple of 7, send a message.
    if remaining_days % 7 == 0 and remaining_days > 0:
        remaining_weeks = remaining_days // 7
        if remaining_weeks > 1:
            msg = f'¡Buenos días! Os recuerdo que quedan {remaining_weeks} semanas para la entrega de la práctica. ¡Ánimo!\n' + \
                  f'Recordad que la entrega está prevista para el {FECHA_ENTREGA.strftime("%d/%m/%Y")} a las {FECHA_ENTREGA.strftime("%H:%M")}.\n'
        else:
            msg = f'¡Buenos días! Entramos en la última semana para la entrega de la práctica. ¡No lo dejéis para el último día!!\n' + \
                  f'Recordad que la entrega está prevista para el {FECHA_ENTREGA.strftime("%d/%m/%Y")} a las {FECHA_ENTREGA.strftime("%H:%M")}.\n'
        
    else:
        # Remind when there are 3, 2, 1 and 0 days left.
        if remaining_days in [3, 2]:
            msg = f'¡Buenos días! Os recuerdo que quedan {remaining_days} días para la entrega de la práctica. ¡Ánimo!\n' + \
                  f'Recordad que la entrega está prevista para el {FECHA_ENTREGA.strftime("%d/%m/%Y")} a las {FECHA_ENTREGA.strftime("%H:%M")}.\n'
        elif remaining_days == 1:
            msg = f'¡Buenos días! Os recuerdo que mañana es el último día para la entrega de la práctica. ¡Ánimo, que ya queda poco!\n' + \
                  f'Recordad que la entrega está prevista para el {FECHA_ENTREGA.strftime("%d/%m/%Y")} a las {FECHA_ENTREGA.strftime("%H:%M")}.\n'
        elif remaining_days == 0:
            msg = f'¡Buenos días! Os recuerdo que hoy es el último día para la entrega de la práctica. ¡Que no se os olvide!\n' + \
                  f'Recordad que podéis entregarla hasta las {FECHA_ENTREGA.strftime("%H:%M")}.\n'
    
    if not msg and now > FECHA_ENTREGA:
        # Look for entrega cuestionario.
        remaining_cuestionario = FECHA_ENTREGA_CUESTIONARIO - now
        remaining_cuestionario_days = remaining_cuestionario.days

        if remaining_cuestionario_days == 1:
            msg = f'¡Buenos días! Os recuerdo que tenéis hasta mañana para entregar el cuestionario de la práctica. ¡Que no se os olvide!\n' + \
                  f'Recordad que la entrega está prevista para el {FECHA_ENTREGA_CUESTIONARIO.strftime("%d/%m/%Y")} a las {FECHA_ENTREGA_CUESTIONARIO.strftime("%H:%M")}.\n'
        elif remaining_cuestionario_days == 0:
            msg = f'¡Buenos días! Os recuerdo que hoy es el último día para entregar el cuestionario de la práctica. ¡Que no se os olvide! Se rellena en un momento.\n' + \
                  f'Recordad que podéis entregarlo hasta las {FECHA_ENTREGA_CUESTIONARIO.strftime("%H:%M")}.\n'

    print(msg)
    if msg:
        # Send the message to the groups.
        keys = ["PROFES", "DG-P1", "GR-P1", "PRUEBA"]
        for key in keys:
            chat_id, thread_id = GROUP_CHATS[key]
            print("Sending message to chat_id: ", chat_id, " and thread_id: ", thread_id)
            await context.bot.send_message(chat_id=chat_id, text=msg, message_thread_id=thread_id)

    

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'maintenance':
        application = ApplicationBuilder().token(__BOT_TOKEN__).build()
        maintenance_handler = MessageHandler(filters.ALL, maintenance)
        application.add_handler(maintenance_handler)
        application.run_polling()
        sys.exit(0)

    application = ApplicationBuilder().token(__BOT_TOKEN__).build()

    #start_handler = CommandHandler('start', start)
    #application.add_handler(start_handler)

    register_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EXPECTING_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_token)],
            EXPECTING_ALIAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    # Add the conversation handler
    # Define the conversation handler
    # Add the conversation handler
    # Define the conversation handler
    ninja_handler = ConversationHandler(
        entry_points=[CommandHandler('battleninja', ninjabattle)],
        states={
            #START: [MessageHandler(filters.COMMAND, parse_command)],
            NINJA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ninjas)],
            FILES: [MessageHandler(filters.ALL & ~filters.COMMAND, get_files_ninja)],
            HEURISTIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_heuristic)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    tour_handler = ConversationHandler(
        entry_points=[CommandHandler('tourjoin', tour)],
        states={
            #START: [MessageHandler(filters.COMMAND, parse_command)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            FILES: [MessageHandler(filters.ALL & ~filters.COMMAND, get_files_tour)],
            HEURISTIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_heuristic_tour)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    tourleave_handler = CommandHandler('tourleave', leave_tour)

    eval_handler = ConversationHandler(
        entry_points=[CommandHandler('eval', evaluate)],
        states={
            FILES: [MessageHandler(filters.ALL & ~filters.COMMAND, get_eval_files)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(register_handler)
    # application.add_handler(upload_handler)
    application.add_handler(eval_handler)

    application.add_handler(ninja_handler)
    application.add_handler(tour_handler)

    application.add_handler(tourleave_handler)

    test_poda_handler = CommandHandler('testpoda', test_poda)
    application.add_handler(test_poda_handler)

    test_poda_callback_handler = CallbackQueryHandler(test_poda_callback, pattern='testpoda-.*')
    application.add_handler(test_poda_callback_handler)

    cuantoqueda_handler = CommandHandler('cuantoqueda', cuantoqueda)
    application.add_handler(cuantoqueda_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)


    changename_handler = ConversationHandler(
        entry_points=[CommandHandler('changename', changename)],
        states={
            EXPECTING_ALIAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(changename_handler)

    history_handler = CommandHandler('history', history)
    application.add_handler(history_handler)

    get_solution_handler = CommandHandler('get', get_solution)
    application.add_handler(get_solution_handler)

    get_test_handler = CommandHandler('test', get_test)
    application.add_handler(get_test_handler)

    get_info_tests_handler = CommandHandler('infotests', get_info_tests)
    application.add_handler(get_info_tests_handler)

    get_leaderboard_handler = CommandHandler('leaderboard', get_leaderboard)
    application.add_handler(get_leaderboard_handler)

    leaderboard_callback_handler = CallbackQueryHandler(leaderboard_callback, pattern='^lb_.*')
    application.add_handler(leaderboard_callback_handler)

    stop_solution_handler = CommandHandler('stop', stop_solution)
    application.add_handler(stop_solution_handler)

    normal_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, normal)
    application.add_handler(normal_handler)

    faq_handler = CommandHandler('faq', faq)
    application.add_handler(faq_handler)

    notify_handler = CommandHandler('notify', notify)
    application.add_handler(notify_handler)

    notify_callback_handler = CallbackQueryHandler(notify_callback, pattern='^notify_.*')
    application.add_handler(notify_callback_handler)

    about_handler = CommandHandler('about', about)
    application.add_handler(about_handler)


    daily_reminder_time = datetime.time(8, 0, 0, tzinfo=pytz.timezone('Europe/Madrid'))
    application.job_queue.run_daily(remind_entrega, daily_reminder_time)

    # Other handlers
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()

