import mysql.connector
import datetime

HOST = "localhost"
USER = "root"
PASSWORD = ""
DATABASE = "uts_pemiot"

def get_conn():
    return mysql.connector.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE)

def ensure_table():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS data_sensor (
            id INT AUTO_INCREMENT PRIMARY KEY,
            suhu FLOAT NOT NULL,
            humidity FLOAT NOT NULL,
            lux INT NOT NULL,
            timestamp DATETIME NOT NULL
        ) ENGINE=InnoDB
        """
    )
    conn.commit()
    cur.close()
    conn.close()

def insert_data(suhu, humidity, lux, ts_value):
    if ts_value is None:
        ts_value = datetime.datetime.now()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO data_sensor (suhu, humidity, lux, timestamp) VALUES (%s,%s,%s,%s)", (suhu, humidity, lux, ts_value))
    conn.commit()
    cur.close()
    conn.close()

def get_lastdata():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, suhu, humidity, lux, timestamp FROM data_sensor ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_summary():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT MAX(suhu), MIN(suhu), AVG(suhu) FROM data_sensor")
    agg = cur.fetchone()
    if agg:
        suhumax = agg[0]
        suhumin = agg[1]
        if agg[2] is not None:
            suhurata = float(round(float(agg[2]), 2))
        else:
            suhurata = None
    else:
        suhumax = None
        suhumin = None
        suhurata = None

    cur.execute("SELECT id, suhu, humidity, lux, timestamp FROM data_sensor ORDER BY suhu DESC, id ASC LIMIT 1")
    row_suhu = cur.fetchone()
    cur.execute("SELECT id, suhu, humidity, lux, timestamp FROM data_sensor ORDER BY humidity DESC, id ASC LIMIT 1")
    row_humid = cur.fetchone()
    cur.close(); conn.close()

    list_rows = []
    month_year = []
    for r in [row_suhu, row_humid]:
        if r:
            ts_val = r[4]
            if hasattr(ts_val, "strftime"):
                ts_text = ts_val.strftime("%Y-%m-%d %H:%M:%S")
                month_year.append({"month_year": str(ts_val.month) + "-" + str(ts_val.year)})
            else:
                ts_text = str(ts_val)
                month_year.append({"month_year": str(ts_val)})
            list_rows.append({
                "idx": r[0],
                "suhu": r[1],
                "humid": r[2],
                "kecerahan": r[3],
                "timestamp": ts_text
            })

    return {
        "suhumax": suhumax,
        "suhumin": suhumin,
        "suhurata": suhurata,
        "nilai_suhu_max_humid_max": list_rows,
        "month_year_max": month_year
    }

try:
    ensure_table()
except Exception as e:
    print("Gagal memastikan tabel:", e)