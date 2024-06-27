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

# Define the different states of the conversation
START, NAME, GROUP, FILES = range(4)

# ConversationHandler states for registration.
NEW_USER, EXPECTING_TOKEN, EXPECTING_ALIAS = range(3)

DB_FOLDER = 'db/'

START_COUNT = 100

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

# La fecha de entrega es el 7 de abril de 2024 a las 23:00 (UTC+2)
FECHA_ENTREGA = datetime.datetime(2024, 4, 7, 23, 0, 0, 0, pytz.timezone('Europe/Madrid'))
FECHA_ENTREGA_CUESTIONARIO = datetime.datetime(2024, 4, 10, 23, 0, 0, 0, pytz.timezone('Europe/Madrid'))

GROUP_CHATS = {
    "DG-GENERAL": (-1002135484699, 1),
    "DG-IMPORTANTE": (-1002135484699, 2),
    "DG-P1": (-1002135484699, 124),
    "GR-GENERAL": (-1002094212883, 1),
    "GR-IMPORTANTE": (-1002094212883, 2),
    "GR-INSTALACION": (-1002094212883, 4),
    "GR-RP1": (-1002094212883, 6),
    "GR-P1": (-1002094212883, 5),
    "GR-OFFTOPIC": (-1002094212883, 3),
    "PROFES": (-996409867, None),
    "PRUEBA": (-1002140728057, 1)
}

GROUP_FILTERS = {
    "ALL": lambda df: df['group_name'] != "",
    "A1D": lambda df: df['group_name'] == "A1D",
    "A2D": lambda df: df['group_name'] == "A2D",
    "A3D": lambda df: df['group_name'] == "A3D",
    "DG": lambda df: df['group_name'].str[-1] == "D",
    "A1": lambda df: df['group_name'] == "A1",
    "A2": lambda df: df['group_name'] == "A2",
    "A3": lambda df: df['group_name'] == "A3",
    "A": lambda df: (df['group_name'].str[0] == "A") & (df['group_name'].str.len() == 2),
    "B1": lambda df: df['group_name'] == "B1",
    "B2": lambda df: df['group_name'] == "B2",
    "B3": lambda df: df['group_name'] == "B3",
    "B": lambda df: (df['group_name'].str[0] == "B") & (df['group_name'].str.len() == 2),
    "C1": lambda df: df['group_name'] == "C1",
    "C2": lambda df: df['group_name'] == "C2",
    "C": lambda df: (df['group_name'].str[0] == "C") & (df['group_name'].str.len() == 2),
    "D1": lambda df: df['group_name'] == "D1",
    "D2": lambda df: df['group_name'] == "D2",
    "D3": lambda df: df['group_name'] == "D3",
    "D": lambda df: (df['group_name'].str[0] == "D") & (df['group_name'].str.len() == 2),
    "PROFES": lambda df: df['group_name'] == "PROFES"
}

LB_BUTTONS = [[InlineKeyboardButton("⬅️", callback_data='lb_prev'), InlineKeyboardButton("🔎", callback_data="lb_me"), InlineKeyboardButton("➡️", callback_data='lb_next')],
               [InlineKeyboardButton("A1", callback_data='lb_A1'), InlineKeyboardButton("A2", callback_data='lb_A2'), InlineKeyboardButton("A3", callback_data='lb_A3'), InlineKeyboardButton("A", callback_data='lb_A')],
                [InlineKeyboardButton("B1", callback_data='lb_B1'), InlineKeyboardButton("B2", callback_data='lb_B2'), InlineKeyboardButton("B3", callback_data='lb_B3'), InlineKeyboardButton("B", callback_data='lb_B')],
                [InlineKeyboardButton("C1", callback_data='lb_C1'), InlineKeyboardButton("C2", callback_data='lb_C2'), InlineKeyboardButton("C", callback_data='lb_C')],
                [InlineKeyboardButton("D1", callback_data='lb_D1'), InlineKeyboardButton("D2", callback_data='lb_D2'), InlineKeyboardButton("D3", callback_data='lb_D3'), InlineKeyboardButton("D", callback_data='lb_D')],
                [InlineKeyboardButton("A1D", callback_data='lb_A1D'), InlineKeyboardButton("A2D", callback_data='lb_A2D'), InlineKeyboardButton("A3D", callback_data='lb_A3D'), InlineKeyboardButton("DG", callback_data='lb_DG')],
                [InlineKeyboardButton("TODOS LOS GRUPOS", callback_data='lb_ALL'), InlineKeyboardButton("PROFES", callback_data='lb_PROFES')]]
                                

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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
    
def get_ok_warn_fail(txt):
    if txt == "OK":
        return "✅"
    elif txt == "WARN":
        return "⚠️"
    else:
        return "❌"

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

def position_to_emoji(pos):
    if pos == 1:
        return "🏆🥇"
    elif pos == 2:
        return "🏆🥈"
    elif pos == 3:
        return "🏆🥉"
    elif pos == 4:
        return "🎖4️⃣"
    elif pos == 5:
        return "🎖5️⃣"
    elif pos == 6:
        return "🔝6️⃣"
    elif pos == 7:
        return "🔝7️⃣"
    elif pos == 8:
        return "🔝8️⃣"
    elif pos == 9:
        return "🔝9️⃣"
    elif pos == 10:
        return "🔝🔟"

    else:
        return f"{pos}."
    

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if it is a user chat or a group chat
    if update.message.chat.type == 'private':
        if find_user_in_db(update.message.from_user.id) is not None:
            await context.bot.send_message(chat_id=update.message.chat_id, text='¡Hola! ¡Bienvenid@ al bot de la práctica 1! Si quieres subir tu solución actual a la leaderboard, escribe /upload. Si quieres información sobre el resto de comandos del bot, escribe /help.')
        else:
            await context.bot.send_message(chat_id=update.message.chat_id, text='¡Hola! ¡Bienvenido al bot de la práctica 1! Antes de comenzar, debes registrarte. Por favor, introduce tu token. '
                                                                                'Si eres estudiante del curso, tu token es tu número de DNI o NIE. Si no consigues acceder, contacta con '
                                                                                'tus profesores para que te faciliten tu token. Si quieres salir, escribe /cancel.')

            return EXPECTING_TOKEN


    else:
        # await context.bot.send_message(chat_id=update.message.chat_id, text='Mejor hablamos en privado. 😅', reply_to_message_id=update.message.message_id)
        global START_COUNT
        await context.bot.send_message(chat_id=update.message.chat_id, text=f'¡Enhorabuena! Eres el/la usuari@ número {START_COUNT} en usar este comando sin leerse las instrucciones 🎉🎉🎉\nComo premio tendrás un punto menos en la evaluación 😈', reply_to_message_id=update.message.message_id)
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
        msg = """¡Hola! Soy el bot de la práctica 1. Estos son los comandos que puedes usar:
        /start: Si no te has registrado todavía, inicia el proceso de registro con este comando.
        /upload: Sube tu solución actual a la leaderboard.
        /help: Muestra esta ayuda.
        /changename: Cambia tu alias.
        /cancel: Cancela el proceso de subir tu solución.
        /stop: Si tienes alguna solución subida y ejecutándose, este comando la detendrá. Solo se puede tener una solución ejecutándose a la vez.
        /leaderboard: Muestra el enlace a la leaderboard.
        /history: Muestra el historial de subidas de tu solución.
        /get <fecha>: Te devuelvo el código la solución que subiste en la fecha indicada. El formato de la fecha es el mismo que el que aparece al usar /history.
        /test <test_name>: Te doy la información del test que me escribas.
        /faq: Muestra las preguntas frecuentes.

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

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Uncomment this message when the leaderboard date is due.
    # await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, la práctica 1 ha terminado. ¡Nos vemos pronto con la práctica 2! 😊')
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
    context.user_data['files'] = []
    context.user_data['stealth'] = False
    # Return the FILES state
    return FILES

async def stealth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if it is a user chat or a group chat
    if update.message.chat.type != 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text='Esto mejor mándamelo por privado. ¿No querrás que nos copiemos de ti? 😳', reply_to_message_id=update.message.message_id)
        return ConversationHandler.END
    # Check if the user is registered
    the_user = get_full_user(update.message.from_user.id)
    if the_user is None:
        await context.bot.send_message(chat_id=update.message.chat_id, text='Tienes que estar registrado para poder subir tu solución. Escribe /start para iniciar el proceso.')
        return ConversationHandler.END
    if the_user['group'] != 'PROFES':
        await context.bot.send_message(chat_id=update.message.chat_id, text='No autorizado.')
        return ConversationHandler.END
    
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
    context.user_data['files'] = []
    context.user_data['stealth'] = True
    # Return the FILES state
    return FILES

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
                await context.bot.send_message(chat_id=update.message.chat_id, text='¡Gracias! He recibido todos los ficheros. Ahora voy a compilarlos y ejecutarlos. Si todo va bien, te enviaré un mensaje cuando tu resultado esté disponible.')
                # Call to sbatch and submit the job.
                os.system(f'sbatch -J {update.message.from_user.id} run_executions.sh "{context.user_data["curr_timestamp"]}" {1 if context.user_data["stealth"] else 0}')
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
    
    # Get the user's folder. It is a folder named with the telegram id of the user.
    user_folder = DB_FOLDER + str(update.message.from_user.id)
    # If the folder doesn't exist, create it.
    if not os.path.exists(user_folder):
        await context.bot.send_message(chat_id=update.message.chat_id, text='No has subido ninguna solución todavía.')
        return
    # Check if there is inside the folder a subfolder called uploads.
    if not os.path.exists(user_folder + '/results'):
        await context.bot.send_message(chat_id=update.message.chat_id, text='No has subido ninguna solución todavía.')
        return
    # Iterate over the files in the uploads folder. Get the folder names (the dates) and sort them.
    dates = sorted([f for f in os.listdir(user_folder + '/results') if os.path.isdir(os.path.join(user_folder + '/results', f))])
    # If there are no dates, send a message indicating that the user hasn't uploaded any solution yet.
    if not dates:
        await context.bot.send_message(chat_id=update.message.chat_id, text='No has subido ninguna solución todavía.')
        return
    # Create a string with the history.
    msgs = []
    line_count = 0
    msg = 'Estas son las soluciones que has subido hasta ahora:\n'
    msg += 'N\. `Fecha:                    ` 0️⃣1️⃣2️⃣3️⃣ \| Estimación\n'
    msg += '\n'
    for i in range(len(dates)):
        line = f'{i+1}\. `{dates[i]}`: '
        # Append to the line the results of the tests. They are stored in a file called final_results.json in the folder of the date.
        with open(user_folder + '/results/' + dates[i] + '/results.json', 'r') as f:
            results = json.load(f)
            global_avg = results['final']['global']['avg']
            line += f"{get_perc_blob(100 * results['final']['0']['avg'])}{get_perc_blob(100 * results['final']['1']['avg'])}{get_perc_blob(100 * results['final']['2']['avg'])}{get_perc_blob(100 * results['final']['3']['avg'])} | {results['final']['global']['avg']:.2f} / 10 {get_perc_blob(global_avg * 10)}".replace('-', '\-').replace('.', '\.').replace('|', '\|')
        # Append to the line the results of the tests (not implemented yet but we use a placeholder message right now).
        # The placeholder message is ✅✅⚠️❌ - Nivel 4: 2.89 / 3 🟢 (use the unicode characters for the emojis).
        # line += u'✅✅⚠️❌ \- 2\.89 / 3 🟢'
        # line += '\N{check mark button} \N{CHECK MARK BUTTON} \N{WARNING} \N{CROSS MARK} - Nivel 4: 2.89 / 3 \N{GREEN CIRCLE}'
        msg += line + '\n'
        line_count += 1
        if line_count % 30 == 0 or i == len(dates) - 1:
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
    user_folder = DB_FOLDER + str(update.message.from_user.id)
    # Check if {user_folder}/uploads/{date} exists.
    if not os.path.exists(user_folder + '/uploads/' + date):
        await context.bot.send_message(chat_id=update.message.chat_id, text='No existe ninguna solución con la fecha indicada. Puedes consultar tu historial de soluciones con el comando /history y elegir una fecha de esa lista.')
        return
    # Check if {user_folder}/uploads/{date}/jugador.cpp exists.
    if not os.path.exists(user_folder + '/uploads/' + date + '/jugador.cpp'):
        await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, ha habido algún problema. He encontrado la carpeta de la solución pero no encuentro el fichero jugador.cpp. Sorry 😔')
        return
    # Check if {user_folder}/uploads/{date}/jugador.hpp exists.
    if not os.path.exists(user_folder + '/uploads/' + date + '/jugador.hpp'):
        await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, ha habido algún problema. He encontrado la carpeta de la solución pero no encuentro el fichero jugador.hpp. Sorry 😔')
        return
    # Send the files.
    await context.bot.send_document(chat_id=update.message.chat_id, document=open(user_folder + '/uploads/' + date + '/jugador.cpp', 'rb'))
    await context.bot.send_document(chat_id=update.message.chat_id, document=open(user_folder + '/uploads/' + date + '/jugador.hpp', 'rb'))

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
        if test["type"] != "private":
            msg += f"`{test['command']}`\n"
            msg += f"`{test['command'].replace('SG', '')}`\n"
            msg += f"`\"args\": {str(test['command'].split(' ')[1:])}`\n".replace("'", '"')
            msg += f"*Nivel:* {test['level']}\n"
            msg += f"*Tamaño del mapa:* {test['map_size']}\n"
            
            if test["type"] == "tutorial":
                msg += f"_Este es uno de los problemas propuestos en el tutorial._"
            if test["type"] == "normal":
                msg += f"_Este es un mapa típico, un problema normal en las condiciones que podrían caer en la evaluación_"
            if test["type"] == "random":
                msg += f"_Estos problemas (R) son siempre en la misma posición inicial, pero van variando la semilla. Si los resultados varían mucho entre distintas semillas, tal vez deberías reducir la dependencia de tu código del azar._"
            if test["type"] == "special":
                msg += f"_Este es un problema especial. Es de una dificultad considerable y no verás un mapa parecido en la evaluación. Antes de ponerte con este problema, céntrate en los problemas normales. Si después sigues con ganas, aquí tienes un desafío._"
            if test["type"] == "eval":
                msg += f"_¡Anda! Has encontrado el test que caerá en la evaluación 😱_".replace("!","\!")
        elif test["type"] == "private":
            msg += f"Nope 😉"

        # Check if there is a file {test_name}.png inside the test_pngs folder.
        if os.path.exists('test_pngs/' + test_name + '.png'):
            msg = msg.replace('(' , '\(').replace(')', '\)').replace('.', '\.').replace('-', '\-')
            if update.message.chat.type == 'private':
                await context.bot.send_photo(chat_id=update.message.chat_id, photo=open('test_pngs/' + test_name + '.png', 'rb'), caption=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
            else:
                await context.bot.send_photo(chat_id=update.message.chat_id, photo=open('test_pngs/' + test_name + '.png', 'rb'), caption=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_to_message_id=update.message.message_id)
        else:
            msg = msg.replace('(' , '\(').replace(')', '\)').replace('.', '\.').replace('-', '\-')
            if update.message.chat.type == 'private':
                await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
            else:
                await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_to_message_id=update.message.message_id)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")
    return START


WINDOW_SIZE = 20
async def get_leaderboard(update, context):
    LEADERBOARD_URL = "http://hercules.ugr.es/IA/P1/"

    leaderboard_df = get_detailed_classification()
    leaderboard_df['position'] = pd.Series(leaderboard_df.index, index=leaderboard_df.index).apply(position_to_emoji)
    leaderboard_to_show = leaderboard_df[['id', 'alias', 'group_name', 'leaderboard_score', 'position']]
    user_pos = leaderboard_to_show[leaderboard_to_show['id'] == update.message.from_user.id].index
    # Apply the position_to_emoji function to the 'position' column elementwise.
    #leaderboard_to_show['position'] = pd.Series(leaderboard_to_show.index, index=leaderboard_to_show.index).apply(position_to_emoji)

    context.user_data['current_window'] = (0, min(WINDOW_SIZE, len(leaderboard_to_show)))
    context.user_data['current_group'] = 'ALL'

    leaderboard_window = leaderboard_to_show[GROUP_FILTERS[context.user_data['current_group']]].iloc[context.user_data['current_window'][0]:context.user_data['current_window'][1], :]
    leaderboard_window = leaderboard_window[['position', 'alias', 'group_name', 'leaderboard_score']]

    msg_leaderboard = "```\n"
    msg_leaderboard += f"{'Pos.':<8}{'Alias':<16}{'Grupo':<8}{'Pts.':<6}\n"
    msg_leaderboard += '-'*50 + '\n'
    for i in range(len(leaderboard_window)):
        if leaderboard_window.iloc[i].name == user_pos:
            msg_leaderboard += f"{'‼️'+leaderboard_window.iloc[i]['position']:<7}{leaderboard_window.iloc[i]['alias']:<16}{leaderboard_window.iloc[i]['group_name']:<8}{leaderboard_window.iloc[i]['leaderboard_score']:05.2f}\n"
        else:
            msg_leaderboard += f"{leaderboard_window.iloc[i]['position']:<8}{leaderboard_window.iloc[i]['alias']:<16}{leaderboard_window.iloc[i]['group_name']:<8}{leaderboard_window.iloc[i]['leaderboard_score']:05.2f}\n"
    msg_leaderboard += "```"
    leaderboard_str = f"*Mostrando filas {context.user_data['current_window'][0]+1} a {context.user_data['current_window'][1]} de {len(leaderboard_to_show)}. GRUPO: {context.user_data['current_group']}*\n\n"
    leaderboard_str += msg_leaderboard
    leaderboard_str = leaderboard_str.replace('.', '\.').replace('(' , '\(').replace(')', '\)').replace('|', '\|')

    buttons = LB_BUTTONS

    msg_intro = f'Puedes ver la clasificación detallada en {LEADERBOARD_URL}. ¡Mucha suerte! Necesitarás estar conectado a la red de la UGR para poder acceder.'
    if update.message.chat.type == 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg_intro)
        await context.bot.send_message(chat_id=update.message.chat_id, text=leaderboard_str, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg_intro, reply_to_message_id=update.message.message_id)
        await context.bot.send_message(chat_id=update.message.chat_id, text=leaderboard_str, reply_to_message_id=update.message.message_id, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))


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
    leaderboard_df = get_detailed_classification()
    leaderboard_df['position'] = pd.Series(leaderboard_df.index, index=leaderboard_df.index).apply(position_to_emoji)
    leaderboard_to_show = leaderboard_df[GROUP_FILTERS[context.user_data['current_group']]]
    # Get the position of the user in the current leaderboard
    user_pos_r = leaderboard_to_show[leaderboard_to_show['id'] == query.from_user.id].index
    if len(user_pos_r) == 0:
        user_pos = None
    else:
        user_pos = user_pos_r[0]

    # Get the row of the user in the current leaderboard (it's not the index, just the row number!!)
    user_row_r = np.where(leaderboard_to_show['id'] == query.from_user.id)[0]
    if len(user_row_r) > 0:
        user_row = user_row_r[0]
    else:
        user_row = None
    # Apply the position_to_emoji function to the 'position' column elementwise.
    #leaderboard_to_show['position'] = pd.Series(leaderboard_to_show.index, index=leaderboard_to_show.index).apply(position_to_emoji)
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
        #leaderboard_to_show['position'] = pd.Series(leaderboard_to_show.index, index=leaderboard_to_show.index).apply(position_to_emoji)
        context.user_data['current_window'] = (0, min(WINDOW_SIZE, df_size))
        # Get the position of the user in the current leaderboard
        user_pos_r = leaderboard_to_show[leaderboard_to_show['id'] == query.from_user.id].index
        if len(user_pos_r) == 0:
            user_pos = None
        else:
            user_pos = user_pos_r[0]

        # Get the row of the user in the current leaderboard (it's not the index, just the row number!!)
        user_row_r = np.where(leaderboard_to_show['id'] == query.from_user.id)[0]
        if len(user_row_r) > 0:
            user_row = user_row_r[0]
        else:
            user_row = None


    leaderboard_window = leaderboard_to_show.iloc[context.user_data['current_window'][0]:context.user_data['current_window'][1], :]
    leaderboard_window = leaderboard_window[['position', 'alias', 'group_name', 'leaderboard_score']]

    msg_leaderboard = "```\n"
    msg_leaderboard += f"{'Pos.':<8}{'Alias':<16}{'Grupo':<8}{'Pts.':<6}\n"
    msg_leaderboard += '-'*50 + '\n'
    # print(user_row, user_pos)
    for i in range(len(leaderboard_window)):
        if leaderboard_window.iloc[i].name == user_pos:
            msg_leaderboard += f"{'‼️'+leaderboard_window.iloc[i]['position']:<7}{leaderboard_window.iloc[i]['alias']:<16}{leaderboard_window.iloc[i]['group_name']:<8}{leaderboard_window.iloc[i]['leaderboard_score']:05.2f}\n"
        else:
            msg_leaderboard += f"{leaderboard_window.iloc[i]['position']:<8}{leaderboard_window.iloc[i]['alias']:<16}{leaderboard_window.iloc[i]['group_name']:<8}{leaderboard_window.iloc[i]['leaderboard_score']:05.2f}\n"
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
    - *El programa me compila en local pero no cuando se lo paso al bot:* Revisa que no hayas modificado ficheros más allá del jugador.cpp y jugador.hpp. Además, cuidado si has incluido en tu código caracteres extraños o directivas "ilegales" en el C++ estándar de las que funcionan con -fpermissive. Revisa también los warnings que produce el código tuyo propio al compilar.
    
    - *Los resultados me salen bien pero el bot dice que no.* Seguramente tienes alguna variable sin inicializar o algún acceso ilegal a memoria. Comprueba si en la versión sin gráfica también te dan los mismos resultados. También prueba a pasarle algún programa como valgrind y analizar su salida.
    
    - *El bot no termina.* El bot realiza muchos tests, si los algoritmos no están implementados de forma eficiente es normal que las ejecuciones tarden mucho. El bot pone un timeout de 5 minutos de todas formas, pero aun así el tiempo se dispara con la cantidad de tests. ~Revisa que la gestión de nodos repetidos en los algoritmos de búsqueda la haces de forma adecuada~.
    
    - *El bot no termina pero a mí en local sí.* Lo más posible es que sea una situación como la del segundo caso.
    
    - *¿Qué es `valgrind`?* `valgrind` es una herramienta que te permite analizar tu programa para ver si hay errores de memoria (invalid reads, invalid writes, leaks, etc.) o variables sin inicializar (uninitialized values). Puedes usarlo para ver si hay errores en tu programa que no se estén manifestando en tus ejecuciones. No siempre estos errores resultan en error, depende del entorno de ejecución y del sistema operativo que una ejecución con errores provoque o no fallos de segmentación. Puedes usarlo con el comando `valgrind ./practica1(SG) <argumentos del programa>`. Recomiendo probarlo tanto con gráfica como sin gráfica.
    
    - *¿Mi nota en la práctica depende de la leaderboard?* No, la leaderboard es solo un entretenimiento para quien quiera picarse con sus compañeros. La nota de la práctica no depende de la posición ni de haber participado en ella.

    - *¿Mi nota en la práctica será la que me dice el bot en los test?* No, para la evaluación se usarán unos mapas de evaluación similares a los de la práctica pero podrían ser diferentes. Yo solo te doy una estimación de cómo vas con la práctica. Pero lo normal es que la estimación no se aleje demasiado de la realidad, y en general, mi estimación debería ser pesimista, ya que ejecuto en muchos mapas diferentes y algunos de ellos son bastante difíciles. No creo que los profesores sean tan duros como yo 😈
    """

    msg_for_other_practicas = """
    - *Me sale la batería correcta (en los niveles 2 y 3) o los instantes correctos (en los niveles 0 y 1) pero el bot no me lo da por bueno.* En este caso lo más posible es que hayas encontrado otro camino óptimo que el bot no contemple. En este caso podéis comentarnos el plan que os ha salido para que lo verifiquemos y lo añadamos como válido al bot.
    """

    msg = msg.replace('.', '\.').replace('(' , '\(').replace(')', '\)').replace('+', '\+').replace('-', '\-')

    if update.message.chat.type == 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_to_message_id=update.message.message_id)

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
        if not os.path.exists(os.path.join(os.getcwd(), DB_FOLDER, str(update.message.from_user.id), eval_folder)):
            os.makedirs(os.path.join(os.getcwd(), DB_FOLDER, str(update.message.from_user.id), eval_folder))
        await file.download_to_drive(os.path.join(os.getcwd(), DB_FOLDER, str(update.message.from_user.id), eval_folder, update.message.document.file_name))
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
    upload_handler = ConversationHandler(
        entry_points=[CommandHandler('upload', upload), CommandHandler('stealth', stealth)],
        states={
            #START: [MessageHandler(filters.COMMAND, parse_command)],
            #NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            #GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_group)],
            FILES: [MessageHandler(filters.ALL & ~filters.COMMAND, get_files)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    eval_handler = ConversationHandler(
        entry_points=[CommandHandler('eval', evaluate)],
        states={
            FILES: [MessageHandler(filters.ALL & ~filters.COMMAND, get_eval_files)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(register_handler)
    application.add_handler(upload_handler)
    application.add_handler(eval_handler)

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

    get_leaderboard_handler = CommandHandler('leaderboard', get_leaderboard)
    application.add_handler(get_leaderboard_handler)

    leaderboard_callback_handler = CallbackQueryHandler(leaderboard_callback)
    application.add_handler(leaderboard_callback_handler)

    stop_solution_handler = CommandHandler('stop', stop_solution)
    application.add_handler(stop_solution_handler)

    normal_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, normal)
    application.add_handler(normal_handler)

    faq_handler = CommandHandler('faq', faq)
    application.add_handler(faq_handler)

    daily_reminder_time = datetime.time(8, 0, 0, tzinfo=pytz.timezone('Europe/Madrid'))
    application.job_queue.run_daily(remind_entrega, daily_reminder_time)

    # Other handlers
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()

