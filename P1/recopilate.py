# This scripts waits until in the results/ folder there are files x.json for each x in the entregas/ folder.
# When this happens, it groups the result in a single file.
__BOT_TOKEN__="__INSERT_BOT_TOKEN_HERE__"

import os
import json
import shutil
import sys
import requests
import json
from telegram import Bot
import asyncio
import pandas as pd
from itertools import product

user_id = sys.argv[1]

TOKEN=__BOT_TOKEN__
CHAT_ID=user_id

# results/ folder will always exist, no need to check.
# entregas/ folder will always exist, no need to check.


async def main():
    # Get all the folder names in entregas/
    entregas = os.listdir("entregas")
    results = os.listdir("results")

    bot = Bot(TOKEN)

    # While there are folders in entregas/ without a json file in results/, wait.
    while len(entregas) != len(results):
        new_results = os.listdir("results")
        # print(len(entregas), len(results), len(new_results))
        if len(new_results) > len(results):
            results = new_results
            message = "🟢" * len(results) + "🕖" * (len(entregas) - len(results))
            message += f"\n{len(results)}/{len(entregas)} entregas corregidas"
            async with bot:
                await bot.send_message(chat_id=CHAT_ID, text=message)

    message = "🎉🎊🎉🎊🎉🎊 SE ACABÓ 🎉🎊🎉🎊🎉🎊"
    async with bot:
        await bot.send_message(chat_id=CHAT_ID, text=message)

    # Iterate through the results file.
    all_results = {}
    for result in results:
        result_name = result[:-5]
        # Open the json file.
        with open(os.path.join("results", result), "r") as f:
            data = json.load(f)
            # Add to all_results the key (the file name) and the value (the result).
            all_results[result_name] = data
            # Add the fields name and surname. Surname is everything until the ',' and name is everything after until the '_'.
            try:
                all_results[result_name]["name"] = result_name.split(",")[1].split("_")[0]
                all_results[result_name]["surname"] = result_name.split(",")[0]
            except:
                all_results[result_name]["name"] = result_name
                all_results[result_name]["surname"] = ""

    # Write the all_results dict to a json file.
    with open("all_results.json", "w") as f:
        json.dump(all_results, f)

    with open("tests.json", "r") as f:
        tests = json.load(f)

    eval_columns = [t for t, v in tests.items() if v["type"] == "eval"]
    all_test_keys = list(tests.keys())
    all_details = ["TOTAL", "TOTAL SIN ERRORES", "ERROR", "PUNTOS", "MENSAJES DE ERROR"]

    eval_columns_prod_details = [f"{t}-{d}" for t, d in product(eval_columns, all_details)]
    all_columns_prod_details = [f"{t}-{d}" for t, d in product(all_test_keys, all_details)]

    eval_df = pd.DataFrame(index=all_results.keys(), columns=["name", "surname"] + eval_columns)
    detailed_eval_df = pd.DataFrame(index=all_results.keys(), columns=["name", "surname"] + eval_columns_prod_details)
    bot_df = pd.DataFrame(index=all_results.keys(), columns=["name", "surname"] + all_test_keys)
    detailed_bot_df = pd.DataFrame(index=all_results.keys(), columns=["name", "surname"] + all_columns_prod_details)

    detail_to_key = {
        "TOTAL": "discovered",
        "TOTAL SIN ERRORES": "discovered_abs",
        "ERROR": "error",
        "PUNTOS": "s",

    }

    # Iterate through the all_results dict.
    for key, student_res in all_results.items():
        # Add the name and surname to the dataframe.
        eval_df.loc[key, "name"] = student_res["name"]
        eval_df.loc[key, "surname"] = student_res["surname"]
        detailed_eval_df.loc[key, "name"] = student_res["name"]
        detailed_eval_df.loc[key, "surname"] = student_res["surname"]
        bot_df.loc[key, "name"] = student_res["name"]
        bot_df.loc[key, "surname"] = student_res["surname"]
        detailed_bot_df.loc[key, "name"] = student_res["name"]
        detailed_bot_df.loc[key, "surname"] = student_res["surname"]

        try:
            for level in [0, 1, 2, 3]:
                level_res = student_res[str(level)]
                for test in level_res:
                    if tests[test]["type"] == "eval":
                        eval_df.loc[key, test] = level_res[test]["summary"]["s"]
                        for detail in all_details:
                            if detail == "MENSAJES DE ERROR":
                                detailed_eval_df.loc[key, f"{test}-{detail}"] = level_res[test]['error'] if 'error' in level_res[test] else ''
                            else:
                                detailed_eval_df.loc[key, f"{test}-{detail}"] = level_res[test]['summary'][detail_to_key[detail]]
                    bot_df.loc[key, test] = level_res[test]["summary"]["s"]
                    for detail in all_details:
                        if detail == "MENSAJES DE ERROR":
                            detailed_bot_df.loc[key, f"{test}-{detail}"] = level_res[test]['error'] if 'error' in level_res[test] else ''
                        else:
                            detailed_bot_df.loc[key, f"{test}-{detail}"] = level_res[test]['summary'][detail_to_key[detail]]
            
        except Exception as e:
            print(f"Error: {e}")
            eval_df.loc[key, "0E1"] = "❌"
            detailed_eval_df.loc[key, "0E1-TOTAL"] = "❌"
            bot_df.loc[key, "0T1"] = "❌"
            detailed_bot_df.loc[key, "0T1-TOTAL"] = "❌"
    # Write the dataframe to a csv file.
    eval_df.to_csv("eval.csv")
    detailed_eval_df.to_csv("detailed_eval.csv")
    bot_df.to_csv("bot.csv")
    detailed_bot_df.to_csv("detailed_bot.csv")

    # Also save as excel file (import all the libraries needed)
    with pd.ExcelWriter("results.xlsx") as writer:
        eval_df.to_excel(writer, sheet_name="Mapas Evaluación")
        detailed_eval_df.to_excel(writer, sheet_name="Detalles Evaluación")
        bot_df.to_excel(writer, sheet_name="Mapas Bot")
        detailed_bot_df.to_excel(writer, sheet_name="Detalles bot")
    #results_df.to_excel("results.xlsx")

    # Send the csv and xlsx files to the user.
    async with bot:
        await bot.send_document(
            chat_id=CHAT_ID,
            document=open(os.path.join(os.getcwd(), 'all_results.json'), 'rb')
        )
        await bot.send_document(
            chat_id=CHAT_ID,
            document=open(os.path.join(os.getcwd(), 'eval.csv'), 'rb')
        )
        await bot.send_document(
            chat_id=CHAT_ID,
            document=open(os.path.join(os.getcwd(), 'detailed_eval.csv'), 'rb')
        )
        await bot.send_document(
            chat_id=CHAT_ID,
            document=open(os.path.join(os.getcwd(), 'bot.csv'), 'rb')
        )
        await bot.send_document(
            chat_id=CHAT_ID,
            document=open(os.path.join(os.getcwd(), 'detailed_bot.csv'), 'rb')
        )
        await bot.send_document(
            chat_id=CHAT_ID,
            document=open(os.path.join(os.getcwd(), 'results.xlsx'), 'rb')
        )
        await bot.send_message(chat_id=CHAT_ID, text="El último es el importante. El resto contienen toda la información pero menos procesada.")

    # Sleep a little to avoid the program closes before the files are sent.
    await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())