import psycopg2
import os


# DB接続用関数
def get_connection():
    user = os.getenv("POSTGRES_USER", None)
    pwd = os.getenv("POSTGRES_PASS", None)
    server = os.getenv("POSTGRES_HOST", None)
    port = os.getenv("POSTGRES_HOST", None)
    db = os.getenv("POSTGRES_PORT", None)


    con = psycopg2.connect(
        "host="
        + server
        + " port="
        + port
        + " dbname="
        + db
        + " user="
        + user
        + " password="
        + pwd
    )

    return con
