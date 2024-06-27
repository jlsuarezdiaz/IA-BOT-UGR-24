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

def get_ok_warn_fail(txt):
    if txt == "ok":
        return "✅"
    elif txt == "warning":
        return "⚠️"
    else:
        return "❌"
    

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
        msg = """¡Hola! Soy el bot de la práctica 2. Estos son los comandos que puedes usar:
        /start: Si no te has registrado todavía, inicia el proceso de registro con este comando.
        /upload: Evalua tu trabajo actual EN TODOS LOS NIVELES. Si quieres evaluar solo en niveles concretos, mira los comandos siguientes.
        /upload {niv1, niv2, ...}: Evalua tu trabajo actual en los niveles que le indiques. Ejemplo: "/upload 1 3" 
        /upload3: Evalua tu trabajo actual en los niveles del 0 al 3 (equivalente a "upload 0 1 2 3")
        /upload4: Sube tu solución para el nivel 4 a la leaderboard (equivalente a "upload 4")
        /notify: Cambia tu configuración de notificaciones.
        /changename: Cambia tu alias.
        /cancel: Cancela el proceso de subir tu solución.
        /stop: Si tienes alguna solución subida y ejecutándose, este comando la detendrá. Solo se puede tener una solución ejecutándose a la vez.
        /leaderboard: Muestra el enlace a la leaderboard.
        /history: Muestra el historial de subidas de tu solución.
        /get <fecha>: Te devuelvo el código la solución que subiste en la fecha indicada. El formato de la fecha es el mismo que el que aparece al usar /history.
        /test <test_name>: Te doy la información del test que me escribas.
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
    # if not stealth:
    #     await context.bot.send_message(chat_id=update.message.chat_id, text='Lo siento, la práctica 2 ha terminado. ¡Nos vemos pronto con la práctica 3! 😊 🔴🟡🟢🔵🎲💣🧨💥', reply_to_message_id=update.message.message_id)
    #     return ConversationHandler.END

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
    if the_user['group'] != 'PROFES':
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
    msg += 'N\. `Fecha:                    ` 0️⃣1️⃣2️⃣3️⃣ \| Estimación Niv4\n'
    msg += '\n'
    for i in range(len(dates)):
        line = f'{i+1}\. `{dates[i]}`: '
        # Append to the line the results of the tests. They are stored in a file called final_results.json in the folder of the date.
        with open(user_folder + '/results/' + dates[i] + '/results.json', 'r') as f:
            results = json.load(f)
            rf = results['final']
            lvl0_result = get_ok_warn_fail(rf['0']['avg']) if '0' in rf else '❔'
            lvl1_result = get_ok_warn_fail(rf['1']['avg']) if '1' in rf else '❔'
            lvl2_result = get_ok_warn_fail(rf['2']['avg']) if '2' in rf else '❔'
            lvl3_result = get_ok_warn_fail(rf['3']['avg']) if '3' in rf else '❔'
            lvl4_result = f"{rf['4']['avg']:.3f}" if '4' in rf else '???'
            lvl4_blob = get_level4_blob(rf['4']['avg']) if '4' in rf else '❔'
            line += f"{lvl0_result}{lvl1_result}{lvl2_result}{lvl3_result} | {lvl4_result} / 3 {lvl4_blob}".replace('-', '\-').replace('.', '\.').replace('|', '\|')
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
    LEADERBOARD_URL = "http://hercules.ugr.es/IA/P2/"

    #await context.bot.send_message(chat_id=update.message.chat_id, text='🚧 Aún no disponible.')
    #return

    leaderboard_df = get_P2_detailed_classification()
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
            msg_leaderboard += f"{'‼️'+leaderboard_window.iloc[i]['position']:<7}{leaderboard_window.iloc[i]['alias']:<16}{leaderboard_window.iloc[i]['group_name']:<8}{leaderboard_window.iloc[i]['leaderboard_score']:5.3f}\n"
        else:
            msg_leaderboard += f"{leaderboard_window.iloc[i]['position']:<8}{leaderboard_window.iloc[i]['alias']:<16}{leaderboard_window.iloc[i]['group_name']:<8}{leaderboard_window.iloc[i]['leaderboard_score']:5.3f}\n"
    msg_leaderboard += "```"
    leaderboard_str = f"*Mostrando filas {context.user_data['current_window'][0]+1} a {context.user_data['current_window'][1]} de {len(leaderboard_to_show)}. GRUPO: {context.user_data['current_group']}*\n\n"
    leaderboard_str += msg_leaderboard
    leaderboard_str = leaderboard_str.replace('.', '\.').replace('(' , '\(').replace(')', '\)').replace('|', '\|')

    buttons = LB_BUTTONS

    msg_intro = f'Puedes ver la clasificación detallada en {LEADERBOARD_URL} 🆕‼️. ¡Mucha suerte! Necesitarás estar conectado a la red de la UGR para poder acceder.'
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
    leaderboard_df = get_P2_detailed_classification()
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
            msg_leaderboard += f"{'‼️'+leaderboard_window.iloc[i]['position']:<7}{leaderboard_window.iloc[i]['alias']:<16}{leaderboard_window.iloc[i]['group_name']:<8}{leaderboard_window.iloc[i]['leaderboard_score']:5.3f}\n"
        else:
            msg_leaderboard += f"{leaderboard_window.iloc[i]['position']:<8}{leaderboard_window.iloc[i]['alias']:<16}{leaderboard_window.iloc[i]['group_name']:<8}{leaderboard_window.iloc[i]['leaderboard_score']:5.3f}\n"
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

    notify_mode = get_P2_user_notifications(update.message.from_user.id)

    msg = "Aquí puedes configurar las notificaciones que quieres recibir durante las ejecuciones. ¿Qué quieres hacer?\n\n"
    msg += f"{'🔘' if notify_mode == 1 else '⚫️'} Avísame por cada test que vaya ejecutando. (Puedo ser un poco pesado pero sabrás en todo momento por dónde voy).\n\n"
    msg += f"{'🔘' if notify_mode == 0 else '⚫️'} Avísame solo cuando estén los resultados.\n"

    buttons = [[InlineKeyboardButton("Cada test", callback_data='notify_test'), InlineKeyboardButton("Solo resultados", callback_data='notify_results')]]

    await context.bot.send_message(chat_id=update.message.chat_id, text=msg, reply_markup=InlineKeyboardMarkup(buttons))

async def notify_callback(update, context):
    query = update.callback_query
    notify_mode = 1 if query.data == 'notify_test' else 0

    set_P2_user_notifications(update.callback_query.from_user.id, notify_mode)

    # Update the tick on the previous message
    msg = "Aquí puedes configurar las notificaciones que quieres recibir durante las ejecuciones. ¿Qué quieres hacer?\n\n"
    msg += f"{'🔘' if notify_mode == 1 else '⚫️'} Avísame por cada test que vaya ejecutando. (Puedo ser un poco pesado pero sabrás en todo momento por dónde voy).\n\n"
    msg += f"{'🔘' if notify_mode == 0 else '⚫️'} Avísame solo cuando estén los resultados.\n"

    buttons = [[InlineKeyboardButton("Cada test", callback_data='notify_test'), InlineKeyboardButton("Solo resultados", callback_data='notify_results')]]

    try:
        await context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=msg, reply_markup=InlineKeyboardMarkup(buttons))
    except:
        pass

    await context.bot.answer_callback_query(query.id, text=f"¡He actualizado tus preferencias! Ahora solo recibirás notificaciones cuando {'estén los resultados' if notify_mode == 0 else 'vaya ejecutando cada test'}.", show_alert=False)
    await query.answer()

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
    
    - *Los resultados me salen bien pero el bot dice que no.* Asegúrate de tener el software actualizado. Yo ejecuto siempre con la última versión del código. Si no, seguramente tienes alguna variable sin inicializar o algún acceso ilegal a memoria. Comprueba si en la versión sin gráfica también te dan los mismos resultados. También prueba a pasarle algún programa como valgrind y analizar su salida.
    
    - *El bot no termina.* El bot realiza muchos tests, si los algoritmos no están implementados de forma eficiente es normal que las ejecuciones tarden mucho. El bot pone un timeout de 5 minutos de todas formas, pero aun así el tiempo se dispara con la cantidad de tests. Revisa que la gestión de nodos repetidos en los algoritmos de búsqueda la haces de forma adecuada.
    
    - *El bot no termina pero a mí en local sí.* Lo más posible es que sea una situación como la del segundo caso.
    
    - *¿Qué es `valgrind`?* `valgrind` es una herramienta que te permite analizar tu programa para ver si hay errores de memoria (invalid reads, invalid writes, leaks, etc.) o variables sin inicializar (uninitialized values). Puedes usarlo para ver si hay errores en tu programa que no se estén manifestando en tus ejecuciones. No siempre estos errores resultan en error, depende del entorno de ejecución y del sistema operativo que una ejecución con errores provoque o no fallos de segmentación. Puedes usarlo con el comando `valgrind ./practica1(SG) <argumentos del programa>`. Recomiendo probarlo tanto con gráfica como sin gráfica.
    
    - *¿Mi nota en la práctica depende de la leaderboard?* No, la leaderboard es solo un entretenimiento para quien quiera picarse con sus compañeros. La nota de la práctica no depende de la posición ni de haber participado en ella.

    - *¿Mi nota en la práctica será la que me dice el bot en los test?* Para los niveles del 0 al 3 asegúrate de pasar todos los tests. Si no, está claro que tu algoritmo de búsqueda tiene fallos. Para la evaluación del nivel 4 se usarán unos mapas de evaluación similares a los míos. Yo solo te doy una estimación de cómo vas con la práctica. Pero lo normal es que la estimación no se aleje demasiado de la realidad, y en general, mi estimación debería ser pesimista, ya que ejecuto en muchos mapas diferentes y algunos de ellos son bastante difíciles. No creo que los profesores sean tan duros como yo 😈
    
    - *Me sale la batería correcta (en los niveles 2 y 3) o los instantes correctos (en los niveles 0 y 1) pero el bot no me dice que ✅.* En este caso lo más posible es que hayas encontrado otro camino óptimo que el bot no contemple, pero mientras sea óptimo es correcto. En este caso podéis comentarnos el plan que os ha salido para que lo verifiquemos y lo añadamos como válido al bot.
    
    - *Me sale más batería final (en los niveles 2 y 3) o más instantes (en los niveles 0 y 1) que al bot, y el camino lleva al objetivo.* En el caso de la batería, si has pisado alguna casilla de recarga puede ser otro camino óptimo no contemplado en la base de datos. Recuerda que buscamos el camino de menor consumo, no el de mayor batería. Ambas soluciones serían válidas si consumen lo mismo. Si no es el caso, o si te pasa con los instantes en los niveles 0 y 1, puede que haya cometido yo un error. Avisa lo antes posible por el canal de SOPORTE BOT para que lo corrijamos.
    """

    msg = msg.replace('.', '\.').replace('(' , '\(').replace(')', '\)').replace('+', '\+').replace('-', '\-')

    if update.message.chat.type == 'private':
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_to_message_id=update.message.message_id)

async def about(update, context):
    msg = """
        ¡Hola! Soy el bot de la práctica 2 de IA. Estoy aquí para ayudarte a evaluar tus soluciones y darte una estimación de cómo vas con la práctica.

        De momento está toda la funcionalidad disponible para que podáis trabajar con los niveles desde el 0 hasta el 3. Para el nivel 4 tenéis algunos problemas para probar, aunque el resto de la funcionalidad y la leaderboard vendrán en unos días. Si os registrasteis en la primera práctica no necesitáis hacerlo de nuevo, podéis ejecutar directamente. Si no, tendréis que registraros antes.

        *IMPORTANTE: leed bien las instrucciones del bot. Tenéis los comandos /help, /about y /faq con toda la información y preguntas frecuentes. Para cualquier problema con el bot podéis consultar a los profesores por el canal SOPORTE BOT, pero no van a estar respondiendo todo el rato a lo que venga ya respondido en mi información.*

        Para los niveles del 0 al 3 el bot realiza una serie de tests para comprobar que el algoritmo de búsqueda está bien implementado. Los tests pueden llevar su tiempo. Así que ahora el comando /upload permite elegir los niveles en los que queréis que se ejecute vuestro código. Leed la ayuda del bot (/help) para consultar todas las posibilidades, y también otros nuevos comandos que se han incluido para esta práctica. Os daremos el resto de detalles del funcionamiento del bot cuando esté toda la funcionalidad para el nivel 4.
    
        *SOBRE EL NIVEL 4*

        Los umbrales definen las puntuaciones a alcanzar en distintos problemas para obtener 1, 2 o 3 puntos en el nivel 4 sobre ese problema. Hay muchas estrategias para abordar este nivel que iremos discutiendo en clase. Estos umbrales buscan valorar la cantidad y calidad de trabajo que se ha realizado en el nivel 4, intentando a la vez ser generosos con respecto a lo exigente que sabemos que es esta práctica.

        En el bot tenéis un total de 24 problemas para evaluar el nivel 4. 10 de ellos son problemas públicos (los tipo P) y otros 10 privados (los tipo H). De nuevo, hay 4 problemas más desafiantes (tipo S), en el que se os plantean desafíos más allá de lo que se os pedirá en la evaluación, como ser capaz de detectar que el colaborador es inalcanzable para decidir no usarlo, objetivos solo al alcance de uno de los jugadores cada vez, o mapas de mayor complejidad. Como siempre, el bot os devuelve la puntuación en los distintos problemas. Valorad bien cada problema individualmente, no os quedéis solo con la media, e intentad solucionar los posibles fallos de comportamiento que os vaya indicando el bot en los problemas públicos.

        Junto con el bot para el nivel 4, viene también una /leaderboard. ¿Quién ganará esta vez? La leaderboard usa como puntuación la nota media del bot en todos los problemas, sin truncar. A partir del 3, cada vez que multipliquéis el umbral del nivel 3 (si podéis) será un punto más. Entre los distintos umbrales que tenéis (los podéis consultar en los /test del bot), la puntuación se reparte de forma lineal según vuestros objetivos (también más allá del 3 con la regla anterior).
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
        entry_points=[CommandHandler('upload', upload), CommandHandler('stealth', stealth), CommandHandler('upload3', upload3), CommandHandler('upload4', upload4)],
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

