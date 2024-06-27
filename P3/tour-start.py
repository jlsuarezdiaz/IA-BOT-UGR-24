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
import pandas as pd
import time
from filelock import FileLock
from db_functions import *
import asyncio
import sys

async def main():
    bot = Bot(__BOT_TOKEN__)
    notify_groups = {
        "GRADO": (-1002094212883, 2118),
        "DOBLE": (-1002135484699, 698)
    }

    # Create a table with the tournament results.
    current_date = sys.argv[1]
    create_P3_tournament_table(current_date, db_path="../../IA_DB.db")
    copy_P3_tour_players(current_date, db_path="../../IA_DB.db")
    all_players = get_P3_tour_players_date(current_date, "../../IA_DB.db")

     # Notify all the players that the tournament has started.
    async with bot:
        try:
            msg = f"🏆 ¡EL TORNEO DEFINITIVO HA COMENZADO! 🏆 [{current_date}]"
            msg2 = f"🛠 Fase de compilación iniciada 🛠"
            for player_id in all_players.keys():
                if all_players[player_id]["notify"] in [1, 2] and all_players[player_id]['type'] != 'LNINJA':
                    await bot.send_message(chat_id=player_id, text=msg)
                    await bot.send_message(chat_id=player_id, text=msg2)

            for _, (group_id, thread_id) in notify_groups.items():
                await bot.send_message(chat_id=group_id, text=msg, message_thread_id=thread_id)
                await bot.send_message(chat_id=group_id, text=msg2, message_thread_id=thread_id)
        except Exception as e:
            print(f"Error sending message to {player_id}. {e}")

if __name__ == "__main__":
    asyncio.run(main())