import sqlite3

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT,
            correct INTEGER DEFAULT 0,
            wrong INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def set_language(user_id, language):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, language)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET language=excluded.language
    ''', (user_id, language))
    conn.commit()
    conn.close()

def add_result(user_id, correct_increment=0, wrong_increment=0):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, correct, wrong)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
        correct = correct + ?,
        wrong = wrong + ?
    ''', (user_id, correct_increment, wrong_increment, correct_increment, wrong_increment))
    conn.commit()
    conn.close()

def get_stats(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT correct, wrong FROM users WHERE user_id=?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"correct": result[0], "wrong": result[1]}
    else:
        return {"correct": 0, "wrong": 0}

def get_language(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM users WHERE user_id=?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None