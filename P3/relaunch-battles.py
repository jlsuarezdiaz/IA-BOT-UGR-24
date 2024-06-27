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

def relaunch_battles():
    current_date = sys.argv[1]

    all_players = get_P3_tour_players_date(current_date, "../IA_DB.db")


    done_battles = get_P3_tournament_battles(current_date, "../IA_DB.db")

    done_pairs = [(b['player1'], b['player2']) for b in done_battles]
    print(len(all_players), len(done_pairs))

    if len(all_players) < 300:
        all_pairings = []

        for player1 in all_players:
            for player2 in all_players:
                if player1 != player2:
                    all_pairings.append((player1, player2))
        print(all_pairings)
   
        for p1, p2 in all_pairings:
            if not (p1, p2) in done_pairs:
                print(f"Relaunching battle between {p1} and {p2}")
                # For each pair of battles submit a slurm job
                os.system(f'sbatch -J tour-{p1}-{p2} tour_battle.sh {p1} {p2} {current_date}')
            else:
                print(f"Battle between {p1} and {p2} already done")

if __name__ == "__main__":
    relaunch_battles()