import mysql.connector

def get_db():
    try:
        db = mysql.connector.connect(
            host="172.19.0.3",
            user="test_mikrotik_stat",
            password="1sampai8*mikrotik",
            database="test_mikrotik_stat"
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

init()

