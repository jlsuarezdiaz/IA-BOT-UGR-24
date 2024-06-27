__BOT_TOKEN__="__INSERT_BOT_TOKEN_HERE__"

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, filters, CommandHandler, ConversationHandler, ApplicationBuilder, ContextTypes, CallbackQueryHandler
import sys
import os
from db_functions import *

import asyncio

async def main():
    bot = Bot(__BOT_TOKEN__)

    user_id = sys.argv[1]
    date = sys.argv[2]

    unregister_P3_tour_player(user_id, db_path="../../IA_DB.db")
    unregister_P3_tour_player_date(user_id, date, db_path="../../IA_DB.db")

    await bot.send_message(chat_id=user_id, text="❌ Lo siento, he tenido que retirarte del torneo. Tu código ha fallado (seguramente por error de compilación o por haberlo subido mientras ya había comenzado a ejecutar el torneo). Antes de apuntarte al próximo torneo, asegúrate de que tu código funciona correctamente. Puedes testearlo con /battleninja primero.")


if __name__ == '__main__':
    asyncio.run(main())
