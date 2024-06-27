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

def get_ok_emoji(str):
    if str == "ok" or str == "info":
        return "✅"
    elif str == "almost_ok":
        return "🆗"
    elif str == "warning":
        return "⚠️"
    elif str == "error" or str == "fail":
        return "❌"
    else:
        return "❓"
    
def get_alert_emoji(l):
    if len(l) == 0:
        return "✅"
    str = ""
    for i in l:
        if i == "NEWPATH":
            str += "ℹ️"
        elif i == "TIME+":
            str += "🕰"
        elif i == "TIME-":
            str += "💨"
        elif i == "INST" or i == "BAT":
            str += "❌"
        elif i == "OBJ":
            str += "🚫"
        elif i == "RESET":
            str += "☠️"
        elif i == "COL":
            str += "🤕"
    return str

def get_end_emoji(str):
    if str == "ERR":
        return "❌"
    elif str == "BAT":
        return "🪫"
    elif str == "INST":
        return "⏳"
    elif str == "TIME":
        return "⏱"
    elif str == "OBJ":
        return "🎯"
    elif str == "RESET":
        return "☠️"


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

    # Sort alphabetically the all_results dict by the key.
    all_results = dict(sorted(all_results.items()))

    # Write the all_results dict to a json file.
    with open("all_results.json", "w") as f:
        json.dump(all_results, f)

    with open("tests.json", "r") as f:
        tests = json.load(f)

    level03_details = ["OK", "DETAILS", "END", "MENSAJES DE ERROR"]

    level03_columns = [t for t,v in tests.items() if v["level"] in [0,1,2,3] and v["type"] != "eval"]
    level03_columns_prod_details = [f"{t}-{d}" for t,d in product(level03_columns, level03_details)]

    level03_eval_columns = [t for t,v in tests.items() if v["level"] in [0,1,2,3] and v["type"] == "eval"]
    level03_eval_columns_prod_details = [f"{t}-{d}" for t,d in product(level03_eval_columns, level03_details)]

    level4_details = ["PUNTOS", "NOTA", "END", "MENSAJES DE ERROR"]

    level4_columns = [t for t,v in tests.items() if v["level"] == 4 and v["type"] != "eval"]
    level4_columns_prod_details = [f"{t}-{d}" for t,d in product(level4_columns, level4_details)]

    level4_eval_columns = [t for t,v in tests.items() if v["level"] == 4 and v["type"] == "eval"]
    level4_eval_columns_prod_details = [f"{t}-{d}" for t,d in product(level4_eval_columns, level4_details)]

    all_test_keys = list(tests.keys())

    bot_df = pd.DataFrame(index=all_results.keys(), columns=["name", "surname", "compiled"] + level03_columns + level4_columns)
    detailed_bot_df = pd.DataFrame(index=all_results.keys(), columns=["name", "surname", "compiled"] + level03_columns_prod_details + level4_columns_prod_details)

    eval_columns = level03_eval_columns + level4_eval_columns
    eval_columns_prod_details = level03_eval_columns_prod_details + level4_eval_columns_prod_details

    eval_df = pd.DataFrame(index=all_results.keys(), columns=["name", "surname", "compiled"] + eval_columns)
    eval_detailed_df = pd.DataFrame(index=all_results.keys(), columns=["name", "surname", "compiled"] + eval_columns_prod_details)

    final_df_empty = pd.DataFrame(index=all_results.keys(), columns=["Nombre", "Apellidos", "Compila", "Tests N0", "Tests N1", "Tests N2", "Tests N3", "Errores N0", "Errores N1", "Errores N2", "Errores N3", "Nivel 0", "Nivel 1", "Nivel 2", "Nivel 3", "Nivel 4", "NOTA FINAL", "Anotaciones", "Comentarios PRADO"])

    detail_to_key = {
        "OK": "test_points",
        "DETAILS": "level_alerts",
        "PUNTOS": "points",
        "NOTA": "test_points",
        "END": "end",
    }

    d2f = {
        "OK": get_ok_emoji,
        "DETAILS": get_alert_emoji,
        "PUNTOS": lambda x: x,
        "NOTA": lambda x: x,
        "END": get_end_emoji
    }


    # Iterate through the all_results dict.
    for key, student_res in all_results.items():
        # Add the name and surname to the dataframe.
        bot_df.loc[key, "name"] = student_res["name"]
        bot_df.loc[key, "surname"] = student_res["surname"]
        detailed_bot_df.loc[key, "name"] = student_res["name"]
        detailed_bot_df.loc[key, "surname"] = student_res["surname"]
        eval_df.loc[key, "name"] = student_res["name"]
        eval_df.loc[key, "surname"] = student_res["surname"]
        eval_detailed_df.loc[key, "name"] = student_res["name"]
        eval_detailed_df.loc[key, "surname"] = student_res["surname"]
        final_df_empty.loc[key, "Nombre"] = student_res["name"]
        final_df_empty.loc[key, "Apellidos"] = student_res["surname"]
        # Add the compiled field to the dataframe.
        bot_df.loc[key, "compiled"] = student_res["compiled"]
        detailed_bot_df.loc[key, "compiled"] = student_res["compiled"]
        eval_df.loc[key, "compiled"] = student_res["compiled"]
        eval_detailed_df.loc[key, "compiled"] = student_res["compiled"]
        final_df_empty.loc[key, "Compila"] = student_res["compiled"]

        try:
            for level in [0, 1, 2, 3]:
                level_res = student_res[str(level)]
                for test in level_res:
                    if tests[test]["type"] == "eval":
                        eval_df.loc[key, test] = get_ok_emoji(level_res[test]["summary"]["test_points"])
                        for detail in level03_details:
                            if detail == "MENSAJES DE ERROR":
                                eval_detailed_df.loc[key, f"{test}-{detail}"] = level_res[test]['error'] if 'error' in level_res[test] else ''
                            else:
                                eval_detailed_df.loc[key, f"{test}-{detail}"] = d2f[detail](level_res[test]['summary'][detail_to_key[detail]])
                    
                    else:
                        bot_df.loc[key, test] = get_ok_emoji(level_res[test]["summary"]["test_points"])
                        for detail in level03_details:
                            if detail == "MENSAJES DE ERROR":
                                detailed_bot_df.loc[key, f"{test}-{detail}"] = level_res[test]['error'] if 'error' in level_res[test] else ''
                            else:
                                detailed_bot_df.loc[key, f"{test}-{detail}"] = d2f[detail](level_res[test]['summary'][detail_to_key[detail]])
                
                final_df_empty.loc[key, f"Tests N{level}"] = get_ok_emoji(student_res["final"][str(level)]["avg"])

            for level in [4]:
                level_res = student_res[str(level)]
                for test in level_res:
                    if tests[test]["type"] == "eval":
                        eval_df.loc[key, test] = level_res[test]["summary"]["test_points"]
                        for detail in level4_details:
                            if detail == "MENSAJES DE ERROR":
                                eval_detailed_df.loc[key, f"{test}-{detail}"] = level_res[test]['error'] if 'error' in level_res[test] else ''
                            else:
                                eval_detailed_df.loc[key, f"{test}-{detail}"] = d2f[detail](level_res[test]['summary'][detail_to_key[detail]])
                    
                    else:
                        bot_df.loc[key, test] = level_res[test]["summary"]["test_points"]
                        for detail in level4_details:
                            if detail == "MENSAJES DE ERROR":
                                detailed_bot_df.loc[key, f"{test}-{detail}"] = level_res[test]['error'] if 'error' in level_res[test] else ''
                            else:
                                detailed_bot_df.loc[key, f"{test}-{detail}"] = d2f[detail](level_res[test]['summary'][detail_to_key[detail]])
                

        except Exception as e:
            print(f"Error: {e}")

    # Write the dataframe to a csv file.
    bot_df.to_csv("bot.csv")
    detailed_bot_df.to_csv("detailed_bot.csv")

    # Also save as excel file (import all the libraries needed)
    if len(sys.argv) > 2:
        eval = sys.argv[2]
    else:
        eval = ""
    with pd.ExcelWriter("results.xlsx") as writer:
        final_df_empty.to_excel(writer, sheet_name=f"{eval} Calificaciones finales")
        bot_df.to_excel(writer, sheet_name=f"{eval} Resultados Globales")
        detailed_bot_df.to_excel(writer, sheet_name=f"{eval} Resultados Detallados")
        eval_df.to_excel(writer, sheet_name=f"{eval} Resultados Globales Cuestionario")
        eval_detailed_df.to_excel(writer, sheet_name=f"{eval} Resultados Detallados Cuestionario")
    #results_df.to_excel("results.xlsx")

    # Send the csv and xlsx files to the user.
    async with bot:
        await bot.send_document(
            chat_id=CHAT_ID,
            document=open(os.path.join(os.getcwd(), 'all_results.json'), 'rb')
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

        message_legend = """Leyenda:
            ℹ️ - Hay varias hojas de cálculo, conteniendo todos los tests del bot, los test del cuestionario, solo resultados, o con detalles de los resultados.
            ℹ️ - Los distintos resultados o detalles se muestran con diferentes iconos, que se describen a continuación.
            ℹ️ - El excel se recomienda visualizar con Google Sheets.
            ℹ️ - La primera hoja de cálculo es una posible plantilla a rellenar con las notas finales. Está vacía a posta.

            🏁 - Motivos de finalización (Columnas END)
                - 🪫: Batería agotada.
                - ⏳: Instantes de simulación agotados.
                - ⏱: Tiempo agotado.
                - ❌: Error.
                - 🎯: Casilla objetivo alcanzada.
                - ☠️: Agente caído por un precipicio.
            
            🔎 - Análisis del problema (hasta nivel 3) (Columnas DETAILS):
                ✅ - Todo correcto.
                ℹ️ - También correcto. Este símbolo solo indica que el camino es diferente al que está en el bot.
                💨 - Advertencia de que el algoritmo ha tardado demasiado poco tiempo. Quizás no desarrolla todos los nodos.
                🕰 - Advertencia de que el algoritmo ha tardado demasiado. Quizás hay problemas de eficiencia o de revisión de nodos repetidos.
                ❌ - La ejecución no termina con el número de acciones (nivel 0-1,) o el nivel de batería (nivel 2-3) correcto, o ha terminado con error.
                🚫 - No se ha llegado a la casilla objetivo.
                🤕 - El agente se choca durante el camino.
                ☠️ - El agente se cae por un precipicio.
    
            💯 - En el nivel 4, se muestra la puntuación en el juego (PUNTOS) y la puntuación sobre 3 (NOTA). También, el motivo de finalización.
            💯 - En los tests de los niveles 0-3, se pueden sacar los siguientes 3 valores:
                ✅ - El test está correcto.
                ⚠️ - El test está correcto, pero quizás hay algún problema (posiblemente demasiado lento). Se puede consultar en la columna DETAILS.
                ❌ - El test ha fallado.
            💯 - Valoración global del nivel (0-3):
                ✅ - Todos los tests se han pasado correctamente.
                🆗 - Se han pasado todos los tests, pero alguno ha dado advertencias (posiblemente demasiado lento).
                ⚠️ - Han fallado algunos tests.
                ❌ - Han fallado demasiados tests.
            ⚠️ - Cuando se produce un mensaje de error, se indica en la columna MENSAJES DE ERROR. Si el programa no termina bien y no hay mensaje de error, principalmente se debe a un core.
            """
        
        await bot.send_message(chat_id=CHAT_ID, text=message_legend)

    # Sleep a little to avoid the program closes before the files are sent.
    await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())