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

def create_P1_submissions_table(db_path='../IA_DB.db'):
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

def insert_P1_submission(telegram_id, submission_date, json_file, public=True, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submissions (telegram_id, submission_date, json_file, public) VALUES (?, ?, ?, ?)
    ''', (telegram_id, submission_date, json_file, public))
    conn.commit()

def create_P1_submission_metrics_table(db_path='../IA_DB.db'):
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

def insert_P1_submission_metrics(telegram_id, submission_date, leaderboard_score, lvl0_score, lvl1_score, lvl2_score, lvl3_score, until30_score, until50_score, until75_score, until100_score, real_score, lvl0_real, lvl1_real, lvl2_real, lvl3_real, until30_real, until50_real, until75_real, until100_real, db_path='../IA_DB.db'):
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
                    
def compute_P1_metrics(results, tests):
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
           
def get_P1_user_submissions(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions WHERE telegram_id = ?', (user_id,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    return rows

def get_P1_classification(db_path='../IA_DB.db'):
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

def get_P1_user_classification(user_id, db_path='../IA_DB.db'):
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

def reset_P1_leaderboard(backup_suffix=None, db_path='../IA_DB.db'):
    # If None suffix, we use the current date (in the format YYYYMMDD_HHMMSS)
    if backup_suffix is None:
        backup_suffix = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Rename the submission_metrics table as submission_metrics_{backup_suffix}
    cursor.execute(f'ALTER TABLE submission_metrics RENAME TO submission_metrics_{backup_suffix}')
    conn.commit()
    # Create a new submission_metrics table
    create_P1_submission_metrics_table(db_path=db_path)

    
def get_P1_detailed_classification(db_path='../IA_DB.db'):
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

# ------------------------------------------------------------------------------ #

def create_P2_notifications_table(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS P2_notifications (
            telegram_id INTEGER PRIMARY KEY NOT NULL,
            notify_mode INTEGER NOT NULL DEFAULT 1
        )
    ''')
    conn.commit()

def get_P2_user_notifications(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM P2_notifications WHERE telegram_id = ?', (user_id,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    if len(rows) == 0:
        return 1
    else:
        # Return only the notify_mode
        return rows[0][1]

def set_P2_user_notifications(user_id, notify_mode, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO P2_notifications (telegram_id, notify_mode) VALUES (?, ?)
    ''', (user_id, notify_mode))
    conn.commit()

def create_P2_submissions_table(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # (telegram_id, submission_date) is the primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissionsP2 (
            telegram_id INTEGER NOT NULL,
            submission_date TEXT NOT NULL,
            json_file TEXT NOT NULL,
            public BOOLEAN NOT NULL DEFAULT 1,
            PRIMARY KEY (telegram_id, submission_date)
        )
    ''')
    conn.commit()

def insert_P2_submission(telegram_id, submission_date, json_file, public=True, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submissionsP2 (telegram_id, submission_date, json_file, public) VALUES (?, ?, ?, ?)
    ''', (telegram_id, submission_date, json_file, public))
    conn.commit()

def create_P2_submission_metrics3_table(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submission_metrics3P2 (
            telegram_id INTEGER NOT NULL,
            submission_date TEXT NOT NULL,
            lvl0_status TEXT DEFAULT NULL,
            lvl1_status TEXT DEFAULT NULL,
            lvl2_status TEXT DEFAULT NULL,
            lvl3_status TEXT DEFAULT NULL,
            PRIMARY KEY (telegram_id, submission_date)
        )
    ''')
    conn.commit()

def create_P2_submission_metrics4_table(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submission_metrics4P2 (
            telegram_id INTEGER NOT NULL,
            submission_date TEXT NOT NULL,
            lvl4_points REAL DEFAULT NULL,
            P1_points REAL DEFAULT NULL,
            P2_points REAL DEFAULT NULL,
            P3_points REAL DEFAULT NULL,
            P4_points REAL DEFAULT NULL,
            P5_points REAL DEFAULT NULL,
            P6_points REAL DEFAULT NULL,
            P7_points REAL DEFAULT NULL,
            P8_points REAL DEFAULT NULL,
            P9_points REAL DEFAULT NULL,
            P10_points REAL DEFAULT NULL,
            H1_points REAL DEFAULT NULL,
            H2_points REAL DEFAULT NULL,
            H3_points REAL DEFAULT NULL,
            H4_points REAL DEFAULT NULL,
            H5_points REAL DEFAULT NULL,
            H6_points REAL DEFAULT NULL,
            H7_points REAL DEFAULT NULL,
            H8_points REAL DEFAULT NULL,
            H9_points REAL DEFAULT NULL,
            H10_points REAL DEFAULT NULL,
            S1_points REAL DEFAULT NULL,
            S2_points REAL DEFAULT NULL,
            S3_points REAL DEFAULT NULL,
            S4_points REAL DEFAULT NULL,
            P1_objs INTEGER DEFAULT NULL,
            P2_objs INTEGER DEFAULT NULL,
            P3_objs INTEGER DEFAULT NULL,
            P4_objs INTEGER DEFAULT NULL,
            P5_objs INTEGER DEFAULT NULL,
            P6_objs INTEGER DEFAULT NULL,
            P7_objs INTEGER DEFAULT NULL,
            P8_objs INTEGER DEFAULT NULL,
            P9_objs INTEGER DEFAULT NULL,
            P10_objs INTEGER DEFAULT NULL,
            H1_objs INTEGER DEFAULT NULL,
            H2_objs INTEGER DEFAULT NULL,
            H3_objs INTEGER DEFAULT NULL,
            H4_objs INTEGER DEFAULT NULL,
            H5_objs INTEGER DEFAULT NULL,
            H6_objs INTEGER DEFAULT NULL,
            H7_objs INTEGER DEFAULT NULL,
            H8_objs INTEGER DEFAULT NULL,
            H9_objs INTEGER DEFAULT NULL,
            H10_objs INTEGER DEFAULT NULL,
            S1_objs INTEGER DEFAULT NULL,
            S2_objs INTEGER DEFAULT NULL,
            S3_objs INTEGER DEFAULT NULL,
            S4_objs INTEGER DEFAULT NULL,
            PRIMARY KEY (telegram_id, submission_date)
        )
    ''')
    conn.commit()

def insert_P2_submission_metrics3(telegram_id, submission_date, lvl0_status, lvl1_status, lvl2_status, lvl3_status, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submission_metrics3P2 (telegram_id, submission_date,
                   lvl0_status, lvl1_status, lvl2_status, lvl3_status)
        VALUES (?,?,?,?,?,?)
    ''', (telegram_id, submission_date, lvl0_status, lvl1_status, lvl2_status, lvl3_status))
    conn.commit()

def insert_P2_submission_metrics4(telegram_id, submission_date, lvl4_points, P1_points, P2_points, P3_points, P4_points, P5_points, P6_points, P7_points, P8_points, P9_points, P10_points, H1_points, H2_points, H3_points, H4_points, H5_points, H6_points, H7_points, H8_points, H9_points, H10_points, S1_points, S2_points, S3_points, S4_points, P1_objs, P2_objs, P3_objs, P4_objs, P5_objs, P6_objs, P7_objs, P8_objs, P9_objs, P10_objs, H1_objs, H2_objs, H3_objs, H4_objs, H5_objs, H6_objs, H7_objs, H8_objs, H9_objs, H10_objs, S1_objs, S2_objs, S3_objs, S4_objs, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submission_metrics4P2 (telegram_id, submission_date,
                   lvl4_points, P1_points, P2_points, P3_points, P4_points, P5_points, P6_points, P7_points, P8_points, P9_points, P10_points,
                   H1_points, H2_points, H3_points, H4_points, H5_points, H6_points, H7_points, H8_points, H9_points, H10_points,
                   S1_points, S2_points, S3_points, S4_points,
                   P1_objs, P2_objs, P3_objs, P4_objs, P5_objs, P6_objs, P7_objs, P8_objs, P9_objs, P10_objs,
                   H1_objs, H2_objs, H3_objs, H4_objs, H5_objs, H6_objs, H7_objs, H8_objs, H9_objs, H10_objs,
                   S1_objs, S2_objs, S3_objs, S4_objs)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (telegram_id, submission_date,
              lvl4_points, P1_points, P2_points, P3_points, P4_points, P5_points, P6_points, P7_points, P8_points, P9_points, P10_points,
              H1_points, H2_points, H3_points, H4_points, H5_points, H6_points, H7_points, H8_points, H9_points, H10_points,
              S1_points, S2_points, S3_points, S4_points,
              P1_objs, P2_objs, P3_objs, P4_objs, P5_objs, P6_objs, P7_objs, P8_objs, P9_objs, P10_objs,
              H1_objs, H2_objs, H3_objs, H4_objs, H5_objs, H6_objs, H7_objs, H8_objs, H9_objs, H10_objs,
              S1_objs, S2_objs, S3_objs, S4_objs))
    conn.commit()
                    
def compute_P2_metrics3(results, tests):
    lvl0_status = '?'
    lvl1_status = '?'
    lvl2_status = '?'
    lvl3_status = '?'

    res2db = {"ok": "OK", "warning": "WARN", "fail": "FAIL"}

    print(results["final"])
    for key, result in results["final"].items():
        if key == 0:
            lvl0_status = res2db[result['avg']]
        elif key == 1:
            lvl1_status = res2db[result['avg']]
        elif key == 2:
            lvl2_status = res2db[result['avg']]
        elif key == 3:
            lvl3_status = res2db[result['avg']]

    return lvl0_status, lvl1_status, lvl2_status, lvl3_status

def compute_P2_metrics4(results, tests):
    lvl4_points = results["final"][4]["avg"]
    for problem, result in results[4].items():
        if problem == "P1":
            P1_points = result["summary"]["test_points"]
            P1_objs = result["summary"]["points"]
        elif problem == "P2":
            P2_points = result["summary"]["test_points"]
            P2_objs = result["summary"]["points"]
        elif problem == "P3":
            P3_points = result["summary"]["test_points"]
            P3_objs = result["summary"]["points"]
        elif problem == "P4":
            P4_points = result["summary"]["test_points"]
            P4_objs = result["summary"]["points"]
        elif problem == "P5":
            P5_points = result["summary"]["test_points"]
            P5_objs = result["summary"]["points"]
        elif problem == "P6":
            P6_points = result["summary"]["test_points"]
            P6_objs = result["summary"]["points"]
        elif problem == "P7":
            P7_points = result["summary"]["test_points"]
            P7_objs = result["summary"]["points"]
        elif problem == "P8":
            P8_points = result["summary"]["test_points"]
            P8_objs = result["summary"]["points"]
        elif problem == "P9":
            P9_points = result["summary"]["test_points"]
            P9_objs = result["summary"]["points"]
        elif problem == "P10":
            P10_points = result["summary"]["test_points"]
            P10_objs = result["summary"]["points"]
        elif problem == "H1":
            H1_points = result["summary"]["test_points"]
            H1_objs = result["summary"]["points"]
        elif problem == "H2":
            H2_points = result["summary"]["test_points"]
            H2_objs = result["summary"]["points"]
        elif problem == "H3":
            H3_points = result["summary"]["test_points"]
            H3_objs = result["summary"]["points"]
        elif problem == "H4":
            H4_points = result["summary"]["test_points"]
            H4_objs = result["summary"]["points"]
        elif problem == "H5":
            H5_points = result["summary"]["test_points"]
            H5_objs = result["summary"]["points"]
        elif problem == "H6":
            H6_points = result["summary"]["test_points"]
            H6_objs = result["summary"]["points"]
        elif problem == "H7":
            H7_points = result["summary"]["test_points"]
            H7_objs = result["summary"]["points"]
        elif problem == "H8":
            H8_points = result["summary"]["test_points"]
            H8_objs = result["summary"]["points"]
        elif problem == "H9":
            H9_points = result["summary"]["test_points"]
            H9_objs = result["summary"]["points"]
        elif problem == "H10":
            H10_points = result["summary"]["test_points"]
            H10_objs = result["summary"]["points"]
        elif problem == "S1":
            S1_points = result["summary"]["test_points"]
            S1_objs = result["summary"]["points"]
        elif problem == "S2":
            S2_points = result["summary"]["test_points"]
            S2_objs = result["summary"]["points"]
        elif problem == "S3":
            S3_points = result["summary"]["test_points"]
            S3_objs = result["summary"]["points"]
        elif problem == "S4":
            S4_points = result["summary"]["test_points"]
            S4_objs = result["summary"]["points"]

    return lvl4_points, P1_points, P2_points, P3_points, P4_points, P5_points, P6_points, P7_points, P8_points, P9_points, P10_points, H1_points, H2_points, H3_points, H4_points, H5_points, H6_points, H7_points, H8_points, H9_points, H10_points, S1_points, S2_points, S3_points, S4_points, P1_objs, P2_objs, P3_objs, P4_objs, P5_objs, P6_objs, P7_objs, P8_objs, P9_objs, P10_objs, H1_objs, H2_objs, H3_objs, H4_objs, H5_objs, H6_objs, H7_objs, H8_objs, H9_objs, H10_objs, S1_objs, S2_objs, S3_objs, S4_objs
           
def get_P2_user_submissions(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissionsP2 WHERE telegram_id = ?', (user_id,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    return rows

def get_P2_user_submissions3(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM submissionsP2, submission_metrics3P2 
            WHERE submissionsP2.telegram_id = ? AND submissionsP2.telegram_id = submission_metrics3P2.telegram_id 
                  AND submissionsP2.submission_date = submission_metrics3P2.submission_date
                ''', (user_id,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    return rows

def get_P2_user_submissions4(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM submissionsP2, submission_metrics4P2 
            WHERE submissionsP2.telegram_id = ? AND submissionsP2.telegram_id = submission_metrics4P2.telegram_id 
                  AND submissionsP2.submission_date = submission_metrics4P2.submission_date
                ''', (user_id,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    return rows

def get_P2_classification(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT id, alias, group_name, leaderboard_score, best_submission, last_submission,
            P1_points, P2_points, P3_points, P4_points, P5_points, P6_points, P7_points, P8_points, P9_points, P10_points,
            H1_points, H2_points, H3_points, H4_points, H5_points, H6_points, H7_points, H8_points, H9_points, H10_points,
            S1_points, S2_points, S3_points, S4_points,
            P1_objs, P2_objs, P3_objs, P4_objs, P5_objs, P6_objs, P7_objs, P8_objs, P9_objs, P10_objs,
            H1_objs, H2_objs, H3_objs, H4_objs, H5_objs, H6_objs, H7_objs, H8_objs, H9_objs, H10_objs,
            S1_objs, S2_objs, S3_objs, S4_objs
    FROM(
        SELECT registered.telegram_id as id, alias, group_name,
                        lvl4_points AS leaderboard_score, 
                        submissionsP2.submission_date AS best_submission,
                        MAX(submissionsP2.submission_date) OVER (PARTITION BY registered.telegram_id) AS last_submission,
                        ROW_NUMBER() OVER (PARTITION BY registered.telegram_id ORDER BY lvl4_points DESC) AS r,
                        P1_points, P2_points, P3_points, P4_points, P5_points, P6_points, P7_points, P8_points, P9_points, P10_points,
                        H1_points, H2_points, H3_points, H4_points, H5_points, H6_points, H7_points, H8_points, H9_points, H10_points,
                        S1_points, S2_points, S3_points, S4_points,
                        P1_objs, P2_objs, P3_objs, P4_objs, P5_objs, P6_objs, P7_objs, P8_objs, P9_objs, P10_objs,
                        H1_objs, H2_objs, H3_objs, H4_objs, H5_objs, H6_objs, H7_objs, H8_objs, H9_objs, H10_objs,
                        S1_objs, S2_objs, S3_objs, S4_objs
        FROM registered
        JOIN tokens ON registered.token = tokens.token
        JOIN submissionsP2 ON registered.telegram_id = submissionsP2.telegram_id
        JOIN submission_metrics4P2 ON registered.telegram_id = submission_metrics4P2.telegram_id AND submissionsP2.submission_date = submission_metrics4P2.submission_date
        WHERE submissionsP2.public = 1
        ORDER BY leaderboard_score DESC
    ) AS ranked_results
    WHERE r = 1
    ''')
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    return rows

def get_P2_user_classification(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM(
    SELECT id, alias, group_name, leaderboard_score, 
            RANK() OVER (ORDER BY leaderboard_score DESC) AS position, 
            best_submission, last_submission,
            P1_points, P2_points, P3_points, P4_points, P5_points, P6_points, P7_points, P8_points, P9_points, P10_points,
            H1_points, H2_points, H3_points, H4_points, H5_points, H6_points, H7_points, H8_points, H9_points, H10_points,
            S1_points, S2_points, S3_points, S4_points,
            P1_objs, P2_objs, P3_objs, P4_objs, P5_objs, P6_objs, P7_objs, P8_objs, P9_objs, P10_objs,
            H1_objs, H2_objs, H3_objs, H4_objs, H5_objs, H6_objs, H7_objs, H8_objs, H9_objs, H10_objs,
            S1_objs, S2_objs, S3_objs, S4_objs, id_submission, total_submissions
    FROM(
        SELECT registered.telegram_id as id, alias, group_name,
                        lvl4_points AS leaderboard_score, 
                        submissionsP2.submission_date AS best_submission,
                        MAX(submissionsP2.submission_date) OVER (PARTITION BY registered.telegram_id) AS last_submission,
                        ROW_NUMBER() OVER (PARTITION BY registered.telegram_id ORDER BY lvl4_points DESC) AS r,
                        P1_points, P2_points, P3_points, P4_points, P5_points, P6_points, P7_points, P8_points, P9_points, P10_points,
                        H1_points, H2_points, H3_points, H4_points, H5_points, H6_points, H7_points, H8_points, H9_points, H10_points,
                        S1_points, S2_points, S3_points, S4_points,
                        P1_objs, P2_objs, P3_objs, P4_objs, P5_objs, P6_objs, P7_objs, P8_objs, P9_objs, P10_objs,
                        H1_objs, H2_objs, H3_objs, H4_objs, H5_objs, H6_objs, H7_objs, H8_objs, H9_objs, H10_objs,
                        S1_objs, S2_objs, S3_objs, S4_objs,
                        ROW_NUMBER() OVER (ORDER BY lvl4_points DESC) AS position,
                        ROW_NUMBER() OVER (PARTITION BY registered.telegram_id ORDER BY submissionsP2.submission_date ASC) AS id_submission,
                        COUNT(submission_metrics4P2.submission_date) OVER (PARTITION BY registered.telegram_id) AS total_submissions
        FROM registered
        JOIN tokens ON registered.token = tokens.token
        JOIN submissionsP2 ON registered.telegram_id = submissionsP2.telegram_id
        JOIN submission_metrics4P2 ON registered.telegram_id = submission_metrics4P2.telegram_id AND submissionsP2.submission_date = submission_metrics4P2.submission_date
        WHERE submissionsP2.public = 1
        ORDER BY leaderboard_score DESC
    ) AS ranked_results
    WHERE r = 1) AS user_results
    WHERE id = ?
    ''', (user_id,))
    
    # Get the number of rows in the result
    row = cursor.fetchone()
    if row is None:
        return None

    rowdict = {
        'id': row[0],
        'alias': row[1],
        'group_name': row[2],
        'leaderboard_score': row[3],
        'position': row[4],
        'best_submission': row[5],
        'last_submission': row[6],
        'P1_points': row[7],
        'P2_points': row[8],
        'P3_points': row[9],
        'P4_points': row[10],
        'P5_points': row[11],
        'P6_points': row[12],
        'P7_points': row[13],
        'P8_points': row[14],
        'P9_points': row[15],
        'P10_points': row[16],
        'H1_points': row[17],
        'H2_points': row[18],
        'H3_points': row[19],
        'H4_points': row[20],
        'H5_points': row[21],
        'H6_points': row[22],
        'H7_points': row[23],
        'H8_points': row[24],
        'H9_points': row[25],
        'H10_points': row[26],
        'S1_points': row[27],
        'S2_points': row[28],
        'S3_points': row[29],
        'S4_points': row[30],
        'P1_objs': row[31],
        'P2_objs': row[32],
        'P3_objs': row[33],
        'P4_objs': row[34],
        'P5_objs': row[35],
        'P6_objs': row[36],
        'P7_objs': row[37],
        'P8_objs': row[38],
        'P9_objs': row[39],
        'P10_objs': row[40],
        'H1_objs': row[41],
        'H2_objs': row[42],
        'H3_objs': row[43],
        'H4_objs': row[44],
        'H5_objs': row[45],
        'H6_objs': row[46],
        'H7_objs': row[47],
        'H8_objs': row[48],
        'H9_objs': row[49],
        'H10_objs': row[50],
        'S1_objs': row[51],
        'S2_objs': row[52],
        'S3_objs': row[53],
        'S4_objs': row[54],
        'id_submission': row[55],
        'total_submissions': row[56]
    }
    return rowdict

def reset_P2_leaderboard(backup_suffix=None, db_path='../IA_DB.db'):
    # If None suffix, we use the current date (in the format YYYYMMDD_HHMMSS)
    if backup_suffix is None:
        backup_suffix = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Rename the submission_metrics table as submission_metrics_{backup_suffix}
    cursor.execute(f'ALTER TABLE submission_metrics4P2 RENAME TO submission_metrics4P2_{backup_suffix}')
    conn.commit()
    # Create a new submission_metrics table
    create_P2_submission_metrics4_table(db_path=db_path)

def get_P2_detailed_classification(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT id, alias, name, surname, group_name, leaderboard_score, best_submission, last_submission,
            P1_points, P2_points, P3_points, P4_points, P5_points, P6_points, P7_points, P8_points, P9_points, P10_points,
            H1_points, H2_points, H3_points, H4_points, H5_points, H6_points, H7_points, H8_points, H9_points, H10_points,
            S1_points, S2_points, S3_points, S4_points,
            P1_objs, P2_objs, P3_objs, P4_objs, P5_objs, P6_objs, P7_objs, P8_objs, P9_objs, P10_objs,
            H1_objs, H2_objs, H3_objs, H4_objs, H5_objs, H6_objs, H7_objs, H8_objs, H9_objs, H10_objs,
            S1_objs, S2_objs, S3_objs, S4_objs,
            total_submissions
    FROM(
        SELECT registered.telegram_id as id, alias, name, surname, group_name,
                        lvl4_points AS leaderboard_score, 
                        submissionsP2.submission_date AS best_submission,
                        MAX(submissionsP2.submission_date) OVER (PARTITION BY registered.telegram_id) AS last_submission,
                        ROW_NUMBER() OVER (PARTITION BY registered.telegram_id ORDER BY lvl4_points DESC) AS r,
                        P1_points, P2_points, P3_points, P4_points, P5_points, P6_points, P7_points, P8_points, P9_points, P10_points,
                        H1_points, H2_points, H3_points, H4_points, H5_points, H6_points, H7_points, H8_points, H9_points, H10_points,
                        S1_points, S2_points, S3_points, S4_points,
                        P1_objs, P2_objs, P3_objs, P4_objs, P5_objs, P6_objs, P7_objs, P8_objs, P9_objs, P10_objs,
                        H1_objs, H2_objs, H3_objs, H4_objs, H5_objs, H6_objs, H7_objs, H8_objs, H9_objs, H10_objs,
                        S1_objs, S2_objs, S3_objs, S4_objs,
                        COUNT(submission_metrics4P2.submission_date) OVER (PARTITION BY registered.telegram_id) AS total_submissions
        FROM registered
        JOIN tokens ON registered.token = tokens.token
        JOIN submissionsP2 ON registered.telegram_id = submissionsP2.telegram_id
        JOIN submission_metrics4P2 ON registered.telegram_id = submission_metrics4P2.telegram_id AND submissionsP2.submission_date = submission_metrics4P2.submission_date
        WHERE submissionsP2.public = 1
        ORDER BY leaderboard_score DESC
    ) AS ranked_results
    WHERE r = 1
    ''')

    # Get the number of rows in the result
    rows = cursor.fetchall()
    # Convert to pandas dataframe
    df = pandas.DataFrame(rows, columns=['id', 'alias', 'name', 'surname', 'group_name', 'leaderboard_score', 'best_submission', 'last_submission',
                                         'P1_points', 'P2_points', 'P3_points', 'P4_points', 'P5_points', 'P6_points', 'P7_points', 'P8_points', 'P9_points', 'P10_points',
                                         'H1_points', 'H2_points', 'H3_points', 'H4_points', 'H5_points', 'H6_points', 'H7_points', 'H8_points', 'H9_points', 'H10_points',
                                         'S1_points', 'S2_points', 'S3_points', 'S4_points',
                                         'P1_objs', 'P2_objs', 'P3_objs', 'P4_objs', 'P5_objs', 'P6_objs', 'P7_objs', 'P8_objs', 'P9_objs', 'P10_objs',
                                         'H1_objs', 'H2_objs', 'H3_objs', 'H4_objs', 'H5_objs', 'H6_objs', 'H7_objs', 'H8_objs', 'H9_objs', 'H10_objs',
                                         'S1_objs', 'S2_objs', 'S3_objs', 'S4_objs',
                                         'total_submissions'])
    df.index = df.index + 1
    return df
# ------------------------------------------------------------------------------ #

def create_P3_notifications_table(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS P3_notifications (
            telegram_id INTEGER PRIMARY KEY NOT NULL,
            notify_mode INTEGER NOT NULL DEFAULT 2
        )
    ''')
    conn.commit()

def get_P3_user_notifications(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM P3_notifications WHERE telegram_id = ?', (user_id,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    if len(rows) == 0:
        return 2
    else:
        # Return only the notify_mode
        return rows[0][1]

def set_P3_user_notifications(user_id, notify_mode, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO P3_notifications (telegram_id, notify_mode) VALUES (?, ?)
    ''', (user_id, notify_mode))
    conn.commit()

def create_P3_submissions_table(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # (telegram_id, submission_date) is the primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissionsP3 (
            telegram_id INTEGER NOT NULL,
            submission_date TEXT NOT NULL,
            heuristic_id INTEGER NOT NULL DEFAULT 0,
            public BOOLEAN NOT NULL DEFAULT 1,
            PRIMARY KEY (telegram_id, submission_date)
        )
    ''')
    conn.commit()

def insert_P3_submission(telegram_id, submission_date, heuristic, public=True, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submissionsP3 (telegram_id, submission_date, heuristic_id, public) VALUES (?, ?, ?, ?)
    ''', (telegram_id, submission_date, heuristic, public))
    conn.commit()

def create_P3_submission_metrics_table(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submission_metricsP3 (
            telegram_id INTEGER NOT NULL,
            submission_date TEXT NOT NULL,
            J1vsN1 CHAR(1) DEFAULT '?',
            N1vsJ2 CHAR(1) DEFAULT '?',
            J1vsN2 CHAR(1) DEFAULT '?',
            N2vsJ2 CHAR(1) DEFAULT '?',
            J1vsN3 CHAR(1) DEFAULT '?',
            N3vsJ2 CHAR(1) DEFAULT '?',     
            PRIMARY KEY (telegram_id, submission_date)
        )
    ''')
    conn.commit()

def insert_P3_submission_metrics(telegram_id, submission_date, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submission_metricsP3 (telegram_id, submission_date) VALUES (?, ?)
    ''', (telegram_id, submission_date))
    conn.commit()

def update_P3_submission_metrics(telegram_id, submission_date, key, value, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f'''
        UPDATE submission_metricsP3
        SET {key} = ?
        WHERE telegram_id = ? AND submission_date = ?
    ''', (value, telegram_id, submission_date))
    conn.commit()

def get_P3_user_submissions(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissionsP3 WHERE telegram_id = ?', (user_id,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    return rows

def get_P3_user_submission_metrics(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submission_metricsP3 WHERE telegram_id = ?', (user_id,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    return rows

def get_P3_user_submission_metrics_df(user_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submission_metricsP3 WHERE telegram_id = ?', (user_id,))
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    # Convert to pandas dataframe
    df = pandas.DataFrame(rows, columns=['telegram_id', 'submission_date', 'J1vsN1', 'N1vsJ2', 'J1vsN2', 'N2vsJ2', 'J1vsN3', 'N3vsJ2'])
    return df

def create_P3_tournament_players_table(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS P3_tournament_players (
            telegram_id INTEGER PRIMARY KEY NOT NULL,
            type TEXT NOT NULL DEFAULT 'AI',
            heuristic INTEGER NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()

def register_P3_tour_player(telegram_id, player_type, heuristic, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # If the player is already registered, update the type and heuristic
    cursor.execute('''
        INSERT OR REPLACE INTO P3_tournament_players (telegram_id, type, heuristic) VALUES (?, ?, ?)
    ''', (telegram_id, player_type, heuristic))

    conn.commit()

def unregister_P3_tour_player(telegram_id, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM P3_tournament_players WHERE telegram_id = ?
    ''', (telegram_id,))
    conn.commit()

def unregister_P3_tour_player_date(telegram_id, date, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f'''
        DELETE FROM P3_tournament_players_{date} WHERE telegram_id = ?
    ''', (telegram_id,))
    conn.commit()

def copy_P3_tour_players(date=None, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if date is None:
        date = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    # Copy the P3_tournament_players table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS P3_tournament_players_{date} AS
        SELECT * FROM P3_tournament_players
    ''')
    conn.commit()

def get_P3_tour_players(db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT P3_tournament_players.telegram_id, type, heuristic, alias, group_name, name, surname, 
        COALESCE(notify_mode, 2) AS notify_mode FROM P3_tournament_players
        JOIN registered ON P3_tournament_players.telegram_id = registered.telegram_id
        JOIN tokens ON registered.token = tokens.token
        LEFT JOIN P3_notifications ON P3_tournament_players.telegram_id = P3_notifications.telegram_id
    ''')
    rows = cursor.fetchall()
    # Return a dict of dictionaries
    players = dict()
    for row in rows:
        players[row[0]] = {
            'type': row[1],
            'heuristic': row[2],
            'alias': row[3],
            'group': row[4],
            'name': row[5],
            'surname': row[6],
            'notify': row[7]
        }

    return players

def get_P3_tour_players_date(date, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT P3_tournament_players_{date}.telegram_id, type, heuristic, alias, group_name, name, surname, 
        COALESCE(notify_mode, 0) AS notify_mode FROM P3_tournament_players_{date}
        JOIN registered ON P3_tournament_players_{date}.telegram_id = registered.telegram_id
        JOIN tokens ON registered.token = tokens.token
        LEFT JOIN P3_notifications ON P3_tournament_players_{date}.telegram_id = P3_notifications.telegram_id
    ''')
    rows = cursor.fetchall()
    # Return a dict of dictionaries
    players = dict()
    for row in rows:
        players[row[0]] = {
            'type': row[1],
            'heuristic': row[2],
            'alias': row[3],
            'group': row[4],
            'name': row[5],
            'surname': row[6],
            'notify': row[7]
        }

    return players


def create_P3_tournament_table(date=None, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if date is None:
        date = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    # This table contains the battles between the players
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS P3_tournament_{date} (
            player1 INTEGER NOT NULL,
            player2 INTEGER NOT NULL,
            winner INTEGER NOT NULL,
            p1_error BOOLEAN NOT NULL DEFAULT 0,
            p2_error BOOLEAN NOT NULL DEFAULT 0,
            timeout BOOLEAN NOT NULL DEFAULT 0,
            PRIMARY KEY (player1, player2)
        )
    ''')
    conn.commit()

def insert_P3_tournament_battle(date, player1, player2, winner, p1_error=False,  p2_error=False, timeout=False, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f'''
        INSERT INTO P3_tournament_{date} (player1, player2, winner, p1_error, p2_error, timeout) VALUES (?, ?, ?, ?, ?, ?)
    ''', (player1, player2, winner, p1_error, p2_error, timeout))
    conn.commit()

def get_P3_tournament_battles(date, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM P3_tournament_{date}')
    rows = cursor.fetchall()
    battles = []
    for row in rows:
        battles.append({
            'player1': row[0],
            'player2': row[1],
            'winner': row[2],
            'p1_error': row[3],
            'p2_error': row[4],
            'timeout': row[5]
        })

    return battles

def get_P3_total_battles(date, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT COUNT(*) FROM P3_tournament_{date}
    ''')
    row = cursor.fetchone()
    return row[0]

def get_P3_detailed_battles(date, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT t.player1 as P1_id, p1.alias as P1_alias, tk1.name as P1_name, tk1.surname as P1_surname, tk1.group_name as P1_group,
                t.player2 as P2_id, p2.alias as P2_alias, tk2.name as P2_name, tk2.surname as P2_surname, tk2.group_name as P2_group,
                t.winner, t.P1_error, t.P2_error, t.timeout
        FROM P3_tournament_{date} t
        JOIN registered p1 ON t.player1 = p1.telegram_id
        JOIN tokens tk1 ON p1.token = tk1.token
        JOIN registered p2 ON t.player2 = p2.telegram_id
        JOIN tokens tk2 ON p2.token = tk2.token
    ''')

    rows = cursor.fetchall()
    battles = []

    for row in rows:
        battles.append({
            'P1_id': row[0],
            'P1_alias': row[1],
            'P1_name': row[2],
            'P1_surname': row[3],
            'P1_group': row[4],
            'P2_id': row[5],
            'P2_alias': row[6],
            'P2_name': row[7],
            'P2_surname': row[8],
            'P2_group': row[9],
            'winner': row[10],
            'P1_error': row[11],
            'P2_error': row[12],
            'timeout': row[13]
        })
    
    return battles

def get_P3_detailed_battles_df(date, db_path='../IA_DB.db'):
    return pandas.DataFrame(get_P3_detailed_battles(date, db_path))

def update_P3_current_battles_table(date, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Delete P3_tournament_prev if it exists.
    cursor.execute('DROP TABLE IF EXISTS P3_tournament_prev')
    # Move P3_tournament_current (if it exists) to P3_tournament_prev
    cursor.execute('ALTER TABLE P3_tournament_current RENAME TO P3_tournament_prev')
    # Copy P3_tournament_{date} to P3_tournament_current
    cursor.execute(f'CREATE TABLE P3_tournament_current AS SELECT * FROM P3_tournament_{date}')
    conn.commit()

def get_P3_classification(date, db_path='../IA_DB.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f'''
    WITH player_stats AS (
    SELECT
        player1 AS player_id,
        SUM(CASE WHEN winner = 1 THEN 2 ELSE 0 END) AS points,
        COUNT(*) AS total_games,
        SUM(CASE WHEN winner = 1 THEN 1 ELSE 0 END) AS total_wins,
        SUM(CASE WHEN winner = 2 THEN 1 ELSE 0 END) AS total_loses,
        SUM(CASE WHEN winner = 0 THEN 1 ELSE 0 END) AS total_nulls,
        COUNT(*) AS games_as_p1,
        SUM(CASE WHEN winner = 1 THEN 1 ELSE 0 END) AS wins_as_p1,
        SUM(CASE WHEN winner = 2 THEN 1 ELSE 0 END) AS loses_as_p1,
        SUM(CASE WHEN winner = 0 THEN 1 ELSE 0 END) AS nulls_as_p1,
        0 AS games_as_p2,
        0 AS wins_as_p2,
        0 AS loses_as_p2,
        0 AS nulls_as_p2,
        SUM(CASE WHEN p1_error = 1 THEN 1 ELSE 0 END) AS total_errors,
        SUM(CASE WHEN p1_error = 1 THEN 1 ELSE 0 END) AS errors_as_p1,
        0 AS errors_as_p2,
        SUM(CASE WHEN timeout = 1 THEN 1 ELSE 0 END) AS timeouts
    FROM P3_tournament_{date}
    GROUP BY player1

    UNION ALL

    SELECT
        player2 AS player_id,
        SUM(CASE WHEN winner = 2 THEN 2 ELSE 0 END) AS points,
        COUNT(*) AS total_games,
        SUM(CASE WHEN winner = 2 THEN 1 ELSE 0 END) AS total_wins,
        SUM(CASE WHEN winner = 1 THEN 1 ELSE 0 END) AS total_loses,
        SUM(CASE WHEN winner = 0 THEN 1 ELSE 0 END) AS total_nulls,
        0 AS games_as_p1,
        0 AS wins_as_p1,
        0 AS loses_as_p1,
        0 AS nulls_as_p1,
        COUNT(*) AS games_as_p2,
        SUM(CASE WHEN winner = 2 THEN 1 ELSE 0 END) AS wins_as_p2,
        SUM(CASE WHEN winner = 1 THEN 1 ELSE 0 END) AS loses_as_p2,
        SUM(CASE WHEN winner = 0 THEN 1 ELSE 0 END) AS nulls_as_p2,
        SUM(CASE WHEN p2_error = 1 THEN 1 ELSE 0 END) AS total_errors,
        0 AS errors_as_p1,
        SUM(CASE WHEN p2_error = 1 THEN 1 ELSE 0 END) AS errors_as_p2,
        SUM(CASE WHEN timeout = 1 THEN 1 ELSE 0 END) AS timeouts
    FROM P3_tournament_{date}
    GROUP BY player2
),

aggregated_stats AS (
    SELECT
        player_id,
        SUM(points) AS points,
        SUM(total_games) AS total_games,
        SUM(total_wins) AS total_wins,
        SUM(total_loses) AS total_loses,
        SUM(total_nulls) AS total_nulls,
        SUM(games_as_p1) AS games_as_p1,
        SUM(wins_as_p1) AS wins_as_p1,
        SUM(loses_as_p1) AS loses_as_p1,
        SUM(nulls_as_p1) AS nulls_as_p1,
        SUM(games_as_p2) AS games_as_p2,
        SUM(wins_as_p2) AS wins_as_p2,
        SUM(loses_as_p2) AS loses_as_p2,
        SUM(nulls_as_p2) AS nulls_as_p2,
        SUM(total_errors) AS total_errors,
        SUM(errors_as_p1) AS errors_as_p1,
        SUM(errors_as_p2) AS errors_as_p2,
        SUM(timeouts) AS timeouts
    FROM player_stats
    GROUP BY player_id
)

SELECT
    ROW_NUMBER() OVER (ORDER BY points DESC) AS position,
    player_id,
    name,
    surname,
    alias,
    group_name,
    points,
    total_games,
    total_wins,
    total_loses,
    total_nulls,
    games_as_p1,
    wins_as_p1,
    loses_as_p1,
    nulls_as_p1,
    games_as_p2,
    wins_as_p2,
    loses_as_p2,
    nulls_as_p2,
    total_errors,
    errors_as_p1,
    errors_as_p2,
    timeouts
FROM aggregated_stats
JOIN registered ON player_id = registered.telegram_id
JOIN tokens ON registered.token = tokens.token
ORDER BY points DESC;
    ''')
    
    # Get the number of rows in the result
    rows = cursor.fetchall()
    
    # Convert to pandas dataframe
    df = pandas.DataFrame(rows, columns=['position', 
                                         'player_id', 
                                         'name', 
                                         'surname', 
                                         'alias', 
                                         'group_name', 
                                         'points', 
                                         'total_games', 
                                         'total_wins', 
                                         'total_loses', 
                                         'total_nulls', 
                                         'games_as_p1', 
                                         'wins_as_p1', 
                                         'loses_as_p1', 
                                         'nulls_as_p1', 
                                         'games_as_p2', 
                                         'wins_as_p2', 
                                         'loses_as_p2', 
                                         'nulls_as_p2', 
                                         'total_errors', 
                                         'errors_as_p1', 
                                         'errors_as_p2', 
                                         'timeouts'])
    df.index = df.index + 1
    return df

def get_full_stats(db_path="../IA_DB.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT name, surname, alias, group_name, prado_id, mail, registered.telegram_id, total_p1_submissions, total_p2_submissions, total_p3_submissions
    FROM registered
    JOIN tokens ON registered.token = tokens.token
    LEFT JOIN (
        SELECT telegram_id, COUNT(*) AS total_p1_submissions
        FROM submissions
        GROUP BY telegram_id
    ) AS p1 ON registered.telegram_id = p1.telegram_id
    LEFT JOIN (
        SELECT telegram_id, COUNT(*) AS total_p2_submissions
        FROM submissionsP2
        GROUP BY telegram_id
    ) AS p2 ON registered.telegram_id = p2.telegram_id
    LEFT JOIN (
        SELECT telegram_id, COUNT(*) AS total_p3_submissions
        FROM submissionsP3
        GROUP BY telegram_id
    ) AS p3 ON registered.telegram_id = p3.telegram_id
    ''')

    rows = cursor.fetchall()

    df = pandas.DataFrame(rows, columns=['name', 'surname', 'alias', 'group', 'prado_id', 'email', 'telegram_id', 'total_p1_submissions', 'total_p2_submissions', 'total_p3_submissions'])
    df.index = df.index + 1
    return df