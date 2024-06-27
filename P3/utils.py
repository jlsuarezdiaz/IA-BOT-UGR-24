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

WINDOW_SIZE = 20
LEADERBOARD_URL = "http://hercules.ugr.es/IA/P3/"
STANDINGS_URL = "http://hercules.ugr.es/IA/P3/standings.html"

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



def get_ok_warn_fail(txt):
    if txt == "ok":
        return "✅"
    elif txt == "warning":
        return "⚠️"
    else:
        return "❌"

async def send_leaderboard(bot, chat_id, user_id, chat_type='private', message_thread_id=None, reply_to_message_id=None, current_date="current", user_data=None):
    LEADERBOARD_URL = "http://hercules.ugr.es/IA/P3/"
    STANDINGS_URL = "http://hercules.ugr.es/IA/P3/standings.html"

    #await context.bot.send_message(chat_id=update.message.chat_id, text='🚧 Aún no disponible.')
    #return

    leaderboard_df = get_P3_classification(current_date)
    leaderboard_to_show = leaderboard_df[['player_id', 'alias', 'group_name', 'position', 'total_wins', 'total_loses', 'total_nulls']]
    user_pos = leaderboard_to_show[leaderboard_to_show['player_id'] == user_id].index
    # Apply the position_to_emoji function to the 'position' column elementwise.
    leaderboard_to_show['position'] = pd.Series(leaderboard_to_show.index, index=leaderboard_to_show.index).apply(position_to_emoji)

    if user_data is None:
        user_data = dict()


    user_data['current_window'] = (0, min(WINDOW_SIZE, len(leaderboard_to_show)))
    user_data['current_group'] = 'ALL'

    leaderboard_window = leaderboard_to_show[GROUP_FILTERS[user_data['current_group']]].iloc[user_data['current_window'][0]:user_data['current_window'][1], :]
    leaderboard_window = leaderboard_window[['position', 'alias', 'group_name', 'total_wins', 'total_loses', 'total_nulls']]

    msg_leaderboard = "```\n"
    msg_leaderboard += f"{'Pos.':<8}{'Alias':<16}{'Grupo':<8}{'W.':<4}{'L.':<4}{'N.':<3}\n"
    msg_leaderboard += '-'*50 + '\n'
    for i in range(len(leaderboard_window)):
        if leaderboard_window.iloc[i].name == user_pos:
            msg_leaderboard += f"{'‼️'+str(leaderboard_window.iloc[i]['position']):<7}{leaderboard_window.iloc[i]['alias']:<16}{leaderboard_window.iloc[i]['group_name']:<8}{leaderboard_window.iloc[i]['total_wins']:03d} {leaderboard_window.iloc[i]['total_loses']:03d} {leaderboard_window.iloc[i]['total_nulls']:02d}\n"
        else:
            msg_leaderboard += f"{str(leaderboard_window.iloc[i]['position']):<8}{leaderboard_window.iloc[i]['alias']:<16}{leaderboard_window.iloc[i]['group_name']:<8}{leaderboard_window.iloc[i]['total_wins']:03d} {leaderboard_window.iloc[i]['total_loses']:03d} {leaderboard_window.iloc[i]['total_nulls']:02d}\n"
    msg_leaderboard += "```"
    leaderboard_str = f"*Mostrando filas {user_data['current_window'][0]+1} a {user_data['current_window'][1]} de {len(leaderboard_to_show)}. GRUPO: {user_data['current_group']}*\n\n"
    leaderboard_str += msg_leaderboard
    leaderboard_str = leaderboard_str.replace('.', '\.').replace('(' , '\(').replace(')', '\)').replace('|', '\|')

    buttons = LB_BUTTONS

    msg_intro = f'Puedes ver la clasificación detallada en {LEADERBOARD_URL}.\n' \
        f'Los resultados de todas las partidas los puedes consultar en {STANDINGS_URL}.\n\n' \
        '¡Mucha suerte! Necesitarás estar conectado a la red de la UGR para poder acceder.'
    if chat_type == 'private':
        await bot.send_message(chat_id=chat_id, text=msg_intro)
        await bot.send_message(chat_id=chat_id, text=leaderboard_str, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await bot.send_message(chat_id=chat_id, text=msg_intro, reply_to_message_id=reply_to_message_id, message_thread_id=message_thread_id)
        await bot.send_message(chat_id=chat_id, text=leaderboard_str, reply_to_message_id=reply_to_message_id, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons), message_thread_id=message_thread_id)