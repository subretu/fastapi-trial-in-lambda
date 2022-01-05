from main.db import get_connection
from main.model import read_user
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi import HTTPException


def auth(credentials):
    """ Basic認証チェック """
    # Basic認証で受け取った情報
    username = credentials.username
    password = credentials.password

    # ユーザとタスクを取得
    conn = get_connection()
    cur = conn.cursor()
    user = read_user(cur, username)
    cur.close()
    conn.close()

    # 該当ユーザがいない場合
    if user == [] or user[0][2] != password:
        error = "ユーザ名かパスワードが間違っています"
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=error,
            headers={"WWW-Authenticate": "Basic"},
        )

    return username
