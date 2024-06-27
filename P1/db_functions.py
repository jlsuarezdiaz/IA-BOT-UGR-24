import sqlite3
import csv
from collections import defaultdict
import numpy as np
import datetime
import pandas

def create_token_table(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY NOT NULL,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            group_name TEXT NOT NULL,
            prado_id TEXT NOT NULL,
            mail TEXT DEFAULT NULL
        )
    ''')
    conn.commit()

def create_registered_table(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registered (
            telegram_id INTEGER PRIMARY KEY NOT NULL,
            token TEXT NOT NULL,
            alias TEXT NOT NULL
        )
    ''')
    conn.commit()

def insert_data_to_token_table(data, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if len(data) == 5:
        cursor.execute('''
            INSERT INTO tokens (token, name, surname, group_name, prado_id) VALUES (?, ?, ?, ?, ?)
        ''', data)
    else:
        cursor.execute('''
            INSERT INTO tokens (token, name, surname, group_name, prado_id, mail) VALUES (?, ?, ?, ?, ?, ?)
        ''', data)
    conn.commit()

def read_csv_and_insert_to_token_table(csv_file, db_path='../IA_DB.db'):
    # The csv has a header. The header names have to match with the table columns
    with open(csv_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 'mail' not in row or row['mail'] == '':
                data = (row['token'], row['name'], row['surname'], row['group_name'], row['prado_id'])
            else:
                data = (row['token'], row['name'], row['surname'], row['group_name'], row['prado_id'], row['mail'])

            insert_data_to_token_table(data, db_path=db_path)

def update_group_name_in_token_table(token, group_name, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tokens SET group_name = ? WHERE token = ?
    ''', (group_name, token))
    conn.commit()

def read_csv_and_update_group_name(csv_file, db_path='../IA_DB.db'):
    # The csv has a header. The header names have to match with the table columns
    with open(csv_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            update_group_name_in_token_table(row['token'], row['group_name'], db_path=db_path)
    
def find_user_in_db(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM registered WHERE telegram_id = ?', (user_id,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None
    else:
        return rows[0]


def find_token_in_db(token, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tokens WHERE token = ?', (token,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None
    else:
        return rows[0]
    
def find_token_in_registered(token, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM registered WHERE token = ?', (token,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None
    else:
        return rows[0]
    
def get_full_user(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tokens, registered WHERE registered.telegram_id = ? AND tokens.token = registered.token', (user_id,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None
    else:
        the_user = rows[0]
        user_dict = {
            'name': the_user[1],
            'surname': the_user[2],
            'group': the_user[3],
            'prado_id': the_user[4],
            'mail': the_user[5],
            'telegram_id': the_user[6],
            'token': the_user[7],
            'alias': the_user[8],
        }
        return user_dict
    
def register_user(user_id, token, alias, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO registered (telegram_id, token, alias) VALUES (?, ?, ?)
    ''', (user_id, token, alias))
    conn.commit()

def update_user_alias(user_id, alias, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE registered SET alias = ? WHERE telegram_id = ?
    ''', (alias, user_id))
    conn.commit()

def create_submissions_table(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # (telegram_id, submission_date) is the primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            telegram_id INTEGER NOT NULL,
            submission_date TEXT NOT NULL,
            json_file TEXT NOT NULL,
            public BOOLEAN NOT NULL DEFAULT 1,
            PRIMARY KEY (telegram_id, submission_date)
        )
    ''')
    conn.commit()

def insert_submission(telegram_id, submission_date, json_file, public=True, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submissions (telegram_id, submission_date, json_file, public) VALUES (?, ?, ?, ?)
    ''', (telegram_id, submission_date, json_file, public))
    conn.commit()

def create_submission_metrics_table(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submission_metrics (
            telegram_id INTEGER NOT NULL,
            submission_date TEXT NOT NULL,
            leaderboard_score REAL NOT NULL,
            lvl0_score REAL NOT NULL,
            lvl1_score REAL NOT NULL,
            lvl2_score REAL NOT NULL,
            lvl3_score REAL NOT NULL,
            until30_score REAL NOT NULL,
            until50_score REAL NOT NULL,
            until75_score REAL NOT NULL,
            until100_score REAL NOT NULL,
            real_score REAL NOT NULL,
            lvl0_real REAL NOT NULL,
            lvl1_real REAL NOT NULL,
            lvl2_real REAL NOT NULL,
            lvl3_real REAL NOT NULL,
            until30_real REAL NOT NULL,
            until50_real REAL NOT NULL,
            until75_real REAL NOT NULL,
            until100_real REAL NOT NULL,
            PRIMARY KEY (telegram_id, submission_date)
        )
    ''')
    conn.commit()

def insert_submission_metrics(telegram_id, submission_date, leaderboard_score, lvl0_score, lvl1_score, lvl2_score, lvl3_score, until30_score, until50_score, until75_score, until100_score, real_score, lvl0_real, lvl1_real, lvl2_real, lvl3_real, until30_real, until50_real, until75_real, until100_real, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submission_metrics (telegram_id, submission_date, leaderboard_score,
                    lvl0_score, lvl1_score, lvl2_score, lvl3_score, 
                    until30_score, until50_score, until75_score, until100_score,
                    real_score, lvl0_real, lvl1_real, lvl2_real, lvl3_real, 
                    until30_real, until50_real, until75_real, until100_real)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (telegram_id, submission_date, leaderboard_score, lvl0_score, lvl1_score, lvl2_score, lvl3_score,
          until30_score, until50_score, until75_score, until100_score, real_score,
          lvl0_real, lvl1_real, lvl2_real, lvl3_real, until30_real, until50_real, until75_real, until100_real))
    conn.commit()
                    
def compute_metrics(results, tests):
    lscores_by_level = defaultdict(list)

    lscores_by_size = defaultdict(list)
    rscores_by_size = defaultdict(list)

    all_lscores = []

    for key, test in tests.items():
        level = test["level"]
        result = results[level][key]
        lscores_by_level[level].append(result["summary"]["netos"] * 100)
        size = test["map_size"]
        area = size[0] * size[1]
        if area <= 30 * 30:
            lscores_by_size[30].append(result["summary"]["netos"] * 100)
            rscores_by_size[30].append(result["summary"]["s"])
        elif area <= 50 * 50:
            lscores_by_size[50].append(result["summary"]["netos"] * 100)
            rscores_by_size[50].append(result["summary"]["s"])
        elif area <= 75 * 75:
            lscores_by_size[75].append(result["summary"]["netos"] * 100)
            rscores_by_size[75].append(result["summary"]["s"])
        else:
            lscores_by_size[100].append(result["summary"]["netos"] * 100)
            rscores_by_size[100].append(result["summary"]["s"])
        all_lscores.append(result["summary"]["netos"] * 100)

    # Compute the final score
    leaderboard_score = np.mean(all_lscores)
    real_score = results["final"]["global"]["avg"]

    lvl0_score = np.mean(lscores_by_level[0]) if len(lscores_by_level[0]) > 0 else 0
    lvl1_score = np.mean(lscores_by_level[1]) if len(lscores_by_level[1]) > 0 else 0
    lvl2_score = np.mean(lscores_by_level[2]) if len(lscores_by_level[2]) > 0 else 0
    lvl3_score = np.mean(lscores_by_level[3]) if len(lscores_by_level[3]) > 0 else 0

    until30_score = np.mean(lscores_by_size[30]) if len(lscores_by_size[30]) > 0 else 0
    until50_score = np.mean(lscores_by_size[50]) if len(lscores_by_size[50]) > 0 else 0
    until75_score = np.mean(lscores_by_size[75]) if len(lscores_by_size[75]) > 0 else 0
    until100_score = np.mean(lscores_by_size[100]) if len(lscores_by_size[100]) > 0 else 0

    lvl0_real = np.mean(results["final"][0]["avg"])
    lvl1_real = np.mean(results["final"][1]["avg"])
    lvl2_real = np.mean(results["final"][2]["avg"])
    lvl3_real = np.mean(results["final"][3]["avg"])

    until30_real = np.mean(rscores_by_size[30]) if len(rscores_by_size[30]) > 0 else 0
    until50_real = np.mean(rscores_by_size[50]) if len(rscores_by_size[50]) > 0 else 0
    until75_real = np.mean(rscores_by_size[75]) if len(rscores_by_size[75]) > 0 else 0
    until100_real = np.mean(rscores_by_size[100]) if len(rscores_by_size[100]) > 0 else 0

    return leaderboard_score, lvl0_score, lvl1_score, lvl2_score, lvl3_score, \
           until30_score, until50_score, until75_score, until100_score, \
           real_score, lvl0_real, lvl1_real, lvl2_real, lvl3_real, \
           until30_real, until50_real, until75_real, until100_real \
           
def get_user_submissions(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions WHERE telegram_id = ?', (user_id,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    return rows

def get_classification(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT id, alias, group_name, leaderboard_score, best_submission, last_submission,
            lvl0_score, lvl1_score, lvl2_score, lvl3_score,
            until30_score, until50_score, until75_score, until100_score
    FROM(
        SELECT registered.telegram_id as id, alias, group_name,
                        leaderboard_score, 
                        submissions.submission_date AS best_submission,
                        MAX(submissions.submission_date) OVER (PARTITION BY registered.telegram_id) AS last_submission,
                        ROW_NUMBER() OVER (PARTITION BY registered.telegram_id ORDER BY leaderboard_score DESC) AS r,
                        lvl0_score, lvl1_score, lvl2_score, lvl3_score,
                        until30_score, until50_score, until75_score, until100_score
        FROM registered
        JOIN tokens ON registered.token = tokens.token
        JOIN submissions ON registered.telegram_id = submissions.telegram_id
        JOIN submission_metrics ON registered.telegram_id = submission_metrics.telegram_id AND submissions.submission_date = submission_metrics.submission_date
        WHERE submissions.public = 1
        ORDER BY leaderboard_score DESC
    ) AS ranked_results
    WHERE r = 1
    ''')
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    return rows

def get_user_classification(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM(
    SELECT id, alias, group_name, leaderboard_score, 
            RANK() OVER (ORDER BY leaderboard_score DESC) AS position, 
            best_submission, last_submission,
            lvl0_score, lvl1_score, lvl2_score, lvl3_score,
            until30_score, until50_score, until75_score, until100_score, id_submission, total_submissions
    FROM(
        SELECT registered.telegram_id as id, alias, group_name,
                        leaderboard_score, 
                        submissions.submission_date AS best_submission,
                        MAX(submissions.submission_date) OVER (PARTITION BY registered.telegram_id) AS last_submission,
                        ROW_NUMBER() OVER (PARTITION BY registered.telegram_id ORDER BY leaderboard_score DESC) AS r,
                        lvl0_score, lvl1_score, lvl2_score, lvl3_score,
                        until30_score, until50_score, until75_score, until100_score,
                        ROW_NUMBER() OVER (ORDER BY leaderboard_score DESC) AS position,
                        ROW_NUMBER() OVER (PARTITION BY registered.telegram_id ORDER BY submissions.submission_date ASC) AS id_submission,
                        COUNT(submissions.submission_date) OVER (PARTITION BY registered.telegram_id) AS total_submissions
        FROM registered
        JOIN tokens ON registered.token = tokens.token
        JOIN submissions ON registered.telegram_id = submissions.telegram_id
        JOIN submission_metrics ON registered.telegram_id = submission_metrics.telegram_id AND submissions.submission_date = submission_metrics.submission_date
        WHERE submissions.public = 1
        ORDER BY leaderboard_score DESC
    ) AS ranked_results
    WHERE r = 1) AS user_results
    WHERE id = ?
    ''', (user_id,))
    
    # Get the number of rows in the result
    row = cursor.fetchone()

    rowdict = {
        'id': row[0],
        'alias': row[1],
        'group_name': row[2],
        'leaderboard_score': row[3],
        'position': row[4],
        'best_submission': row[5],
        'last_submission': row[6],
        'lvl0_score': row[7],
        'lvl1_score': row[8],
        'lvl2_score': row[9],
        'lvl3_score': row[10],
        'until30_score': row[11],
        'until50_score': row[12],
        'until75_score': row[13],
        'until100_score': row[14],
        'id_submission': row[15],
        'total_submissions': row[16]
    }
    return rowdict

def print_tablerows(rows):
    for row in rows:
        print(row)

def reset_leaderboard(backup_suffix=None, db_path='../IA_DB.db'):
    # If None suffix, we use the current date (in the format YYYYMMDD_HHMMSS)
    if backup_suffix is None:
        backup_suffix = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Rename the submission_metrics table as submission_metrics_{backup_suffix}
    cursor.execute(f'ALTER TABLE submission_metrics RENAME TO submission_metrics_{backup_suffix}')
    conn.commit()
    # Create a new submission_metrics table
    create_submission_metrics_table(db_path=db_path)

    
def get_detailed_classification(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT id, alias, name, surname, group_name, leaderboard_score, best_submission, last_submission,
            lvl0_score, lvl1_score, lvl2_score, lvl3_score,
            until30_score, until50_score, until75_score, until100_score,
            lvl0_real, lvl1_real, lvl2_real, lvl3_real,
            until30_real, until50_real, until75_real, until100_real
    FROM(
        SELECT registered.telegram_id as id, alias, name, surname, group_name,
                        leaderboard_score, 
                        submissions.submission_date AS best_submission,
                        MAX(submissions.submission_date) OVER (PARTITION BY registered.telegram_id) AS last_submission,
                        ROW_NUMBER() OVER (PARTITION BY registered.telegram_id ORDER BY leaderboard_score DESC) AS r,
                        lvl0_score, lvl1_score, lvl2_score, lvl3_score,
                        until30_score, until50_score, until75_score, until100_score,
                        lvl0_real, lvl1_real, lvl2_real, lvl3_real,
                        until30_real, until50_real, until75_real, until100_real
        FROM registered
        JOIN tokens ON registered.token = tokens.token
        JOIN submissions ON registered.telegram_id = submissions.telegram_id
        JOIN submission_metrics ON registered.telegram_id = submission_metrics.telegram_id AND submissions.submission_date = submission_metrics.submission_date
        WHERE submissions.public = 1
        ORDER BY leaderboard_score DESC
    ) AS ranked_results
    WHERE r = 1
    ''')
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    # Convert to pandas dataframe
    df = pandas.DataFrame(rows, columns=['id', 'alias', 'name', 'surname', 'group_name', 'leaderboard_score', 'best_submission', 'last_submission',
                                         'lvl0_score', 'lvl1_score', 'lvl2_score', 'lvl3_score',
                                         'until30_score', 'until50_score', 'until75_score', 'until100_score',
                                         'lvl0_real', 'lvl1_real', 'lvl2_real', 'lvl3_real',
                                         'until30_real', 'until50_real', 'until75_real', 'until100_real'])
    df.index = df.index + 1
    return df
