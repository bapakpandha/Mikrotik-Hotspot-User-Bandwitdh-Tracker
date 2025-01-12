import mysql.connector
from app import read_settings

def get_db():
    try:
        db = mysql.connector.connect(
            host=read_settings("DB_HOST"),
            user=read_settings("DB_USER"),
            password=read_settings("DB_PASSWORD"),
            database=read_settings("DB_NAME")
        )
        # print("Koneksi ke DB berhasil")
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        db = None
    except Exception as e:
        print(f"Unexpected Error: {e}")
        db = None
    return db

def init():
    try:
        get_db()
        db = get_db()
        cursor = db.cursor()
        cursor.execute(\
        'CREATE TABLE IF NOT EXISTS users (\
        user_id INT AUTO_INCREMENT PRIMARY KEY,\
        username VARCHAR(255) NOT NULL UNIQUE\
        );'\
        )
        cursor.execute('INSERT INTO users VALUES (1,"TOTAL") ON DUPLICATE KEY UPDATE username="TOTAL";')
        cursor.execute('\
        CREATE TABLE IF NOT EXISTS raw_bandwidth_logs (\
        log_id BIGINT AUTO_INCREMENT PRIMARY KEY,\
        user_id INT NOT NULL,\
        source_ip VARCHAR(45) NULL,\
        destination_ip VARCHAR(45) NULL,\
        tx_bytes BIGINT UNSIGNED NOT NULL,\
        rx_bytes BIGINT UNSIGNED NOT NULL,\
        timestamp DATETIME NOT NULL,\
        FOREIGN KEY (user_id) REFERENCES users(user_id) \
            ON DELETE CASCADE\
            ON UPDATE CASCADE,\
        INDEX (user_id),\
        INDEX (timestamp)\
        );\
        \
        ')
        cursor.execute('CREATE TABLE IF NOT EXISTS aggregated_bandwidth_logs_30min (\
        agg_id BIGINT AUTO_INCREMENT PRIMARY KEY,\
        user_id INT NOT NULL,\
        interval_start DATETIME NOT NULL,\
        interval_end DATETIME NOT NULL,\
        total_tx_bytes BIGINT UNSIGNED NOT NULL,\
        total_rx_bytes BIGINT UNSIGNED NOT NULL,\
        FOREIGN KEY (user_id) REFERENCES users(user_id) \
            ON DELETE CASCADE\
            ON UPDATE CASCADE,\
        INDEX (user_id),\
        INDEX (interval_start)\
        );\
        ')
        cursor.execute('CREATE TABLE IF NOT EXISTS aggregated_bandwidth_logs_3hr (\
        agg_id BIGINT AUTO_INCREMENT PRIMARY KEY,\
        user_id INT NOT NULL,\
        interval_start DATETIME NOT NULL,\
        interval_end DATETIME NOT NULL,\
        total_tx_bytes BIGINT UNSIGNED NOT NULL,\
        total_rx_bytes BIGINT UNSIGNED NOT NULL,\
        FOREIGN KEY (user_id) REFERENCES users(user_id) \
            ON DELETE CASCADE\
            ON UPDATE CASCADE,\
        INDEX (user_id),\
        INDEX (interval_start)\
        );\
        ')
        db.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

def cursor_to_object_collection(cursor):
    output = []
    queryResult = cursor.fetchall()
    names = [d[0] for d in cursor.description ]
    for record in queryResult:
        obj = {}
        for i in range(len(names)):
            obj[names[i]] = record[i]
        output.append(obj)
    return output

def query_db(sql, args=[]):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(sql, args)
        return cursor_to_object_collection(cursor)
    except Exception as E:
        print (E)
        return E
    finally:
        if cursor:
            cursor.close()

def read_user_lists():
    try:
        return query_db("SELECT * FROM users;")
    except Exception as E:
        print("error: ", E)

def add_new_user_to_lists(username):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO users (username) VALUES (%s)', [(username)])
        db.commit()
    except Exception as E:
        print("error: ", E)

def get_user_id_from_username(username):
    try:
        result = query_db('SELECT user_id FROM users WHERE username = %s', (username,))
        return result[0]['user_id']
    except Exception as E:
        print("error: ", E)

def add_raw_data(user_id, tx_bytes, rx_bytes, timestamp):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO raw_bandwidth_logs (user_id, tx_bytes, rx_bytes, timestamp) VALUES (%s, %s, %s, %s)', (user_id, tx_bytes, rx_bytes, timestamp))
        db.commit()
    except Exception as E:
        print("error: ", E)

def aggregate_data(user_id, earliest_time, latest_time, total_tx_bytes, total_rx_bytes):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO aggregated_bandwidth_logs_30min (user_id, interval_start, interval_end, total_tx_bytes, total_rx_bytes) VALUES (%s, %s, %s, %s, %s)', (user_id, earliest_time, latest_time, total_tx_bytes, total_rx_bytes))
        cursor.execute('DELETE FROM raw_bandwidth_logs WHERE user_id = %s', (user_id,))
        db.commit()
    except Exception as E:
        print("error: ", E)

def get_detail(limit=150):
    return query_db("SELECT a.username username, total_tx_bytes, total_rx_bytes, interval_end AS 'period' FROM aggregated_bandwidth_logs_30min LEFT JOIN users AS a ON a.user_id = aggregated_bandwidth_logs_30min.user_id ORDER BY interval_end DESC LIMIT %s;", [limit])

def get_by_host():
    return query_db("SELECT a.username username, CAST(SUM(total_tx_bytes) AS INT) AS total_tx_bytes, CAST(SUM(total_rx_bytes) AS INT) AS total_rx_bytes FROM aggregated_bandwidth_logs_30min LEFT JOIN users AS a ON a.user_id = aggregated_bandwidth_logs_30min.user_id GROUP BY username ORDER BY SUM(total_tx_bytes) + SUM(total_rx_bytes) DESC")
    
def get_by_month():
    return query_db("SELECT a.username username, CAST(SUM(total_tx_bytes) AS INT) AS total_tx_bytes, CAST(SUM(total_rx_bytes) AS INT) AS total_rx_bytes, CONCAT(YEAR(interval_end), '-', LPAD(MONTH(interval_end), 2, '0')) AS 'month' FROM aggregated_bandwidth_logs_30min LEFT JOIN users AS a ON a.user_id = aggregated_bandwidth_logs_30min.user_id GROUP BY username, 'month' ORDER BY 'month' DESC, SUM(total_tx_bytes) + SUM(total_rx_bytes) DESC;")

def get_by_week():
    return query_db("SELECT a.username username, CAST(SUM(total_tx_bytes) AS INT) AS total_tx_bytes, CAST(SUM(total_rx_bytes) AS INT) AS total_rx_bytes, CONCAT(YEAR(interval_end), '-', LPAD(WEEK(interval_end), 2, '0')) AS 'week' FROM aggregated_bandwidth_logs_30min LEFT JOIN users AS a ON a.user_id = aggregated_bandwidth_logs_30min.user_id GROUP BY username, 'week' ORDER BY 'week' DESC, SUM(total_tx_bytes) + SUM(total_rx_bytes) DESC;")

def get_by_day():
    return query_db("SELECT a.username username, CAST(SUM(total_tx_bytes) AS INT) AS total_tx_bytes, CAST(SUM(total_rx_bytes) AS INT) AS total_rx_bytes, CONCAT(YEAR(interval_end), '-', LPAD(MONTH(interval_end), 2, '0'), '-', LPAD(DAY(interval_end), 2, '0')) AS 'day' FROM aggregated_bandwidth_logs_30min LEFT JOIN users AS a ON a.user_id = aggregated_bandwidth_logs_30min.user_id GROUP BY username, 'day' ORDER BY 'day' DESC, SUM(total_tx_bytes) + SUM(total_rx_bytes) DESC;")

def get_real_time(user_id):
    return query_db("SELECT a.username username, tx_bytes, rx_bytes, timestamp AS 'period' FROM raw_bandwidth_logs LEFT JOIN users AS a ON a.user_id = raw_bandwidth_logs.user_id WHERE a.user_id = %s ORDER BY timestamp DESC LIMIT 1;", [user_id])
    

init()

