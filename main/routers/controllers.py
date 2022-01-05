from fastapi import Depends, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from requests.sessions import session
from starlette.templating import Jinja2Templates
from starlette.requests import Request
from main.model import (
    read_task,
    read_user,
    insert_user,
    read_task2,
    update_tsak,
    add_task,
    delete_task,
    read_task3,
    get_new_task,
)
from main.db import get_connection
import re
from main.mycalendar import MyCalendar
from datetime import datetime, timedelta
from main.auth import auth
from starlette.responses import RedirectResponse
import json

from fastapi import APIRouter

router = APIRouter()

pattern = re.compile(r"\w{4,20}")  # 任意の4~20の英数字を示す正規表現
pattern_pw = re.compile(r"\w{6,20}")  # 任意の6~20の英数字を示す正規表現
pattern_mail = re.compile(
    r"^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$"
)  # e-mailの正規表現

security = HTTPBasic()

# テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")
# Jinja2.Environment : filterやglobalの設定用
jinja_env = templates.env


@router.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/admin")
@router.post("/admin")
def admin(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    username = auth(credentials)

    # ユーザとタスクを取得
    conn = get_connection()
    cur = conn.cursor()
    user = read_user(cur, username)
    task = read_task(cur, user[0])
    cur.close()
    conn.close()

    today = datetime.now()
    next_w = today + timedelta(days=7)  # １週間後の日付

    # カレンダーをHTML形式で取得
    cal = MyCalendar(
        username, {t[3].strftime("%Y%m%d"): t[5] for t in task}
    )  # 予定がある日付をキーとして渡す

    cal = cal.formatyear(today.year, 4)  # カレンダーをHTMLで取得

    # 直近のタスクだけでいいので、リストを書き換える
    task = [t for t in task if today <= t[3] <= next_w]
    links = [t[3].strftime("/todo/" + username + "/%Y/%m/%d") for t in task]  # 直近の予定リンク

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "user": user,
            "task": task,
            "links": links,
            "calender": cal,
        },
    )


@router.get("/register")
@router.post("/register")
async def register(request: Request):
    if request.method == "GET":
        return templates.TemplateResponse(
            "register.html", {"request": request, "username": "", "error": []}
        )

    if request.method == "POST":
        # POSTデータ
        data = await request.form()
        username = data.get("username")
        password = data.get("password")
        password_tmp = data.get("password_tmp")
        mail = data.get("mail")

        user_data = (username, password, mail)

        error = []

        conn = get_connection()
        cur = conn.cursor()

        # ユーザ-を取得
        user = read_user(cur, username)

        # 怒涛のエラー処理
        if user != []:
            error.append("同じユーザ名のユーザが存在します。")
        if password != password_tmp:
            error.append("入力したパスワードが一致しません。")
        if pattern.match(username) is None:
            error.append("ユーザ名は4~20文字の半角英数字にしてください。")
        if pattern_pw.match(password) is None:
            error.append("パスワードは6~20文字の半角英数字にしてください。")
        if pattern_mail.match(mail) is None:
            error.append("正しくメールアドレスを入力してください。")

        # エラーがあれば登録ページへ戻す
        if error:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "username": username, "error": error},
            )

        # 問題がなければユーザ登録
        insert_user(conn, cur, user_data)
        cur.close()
        conn.close()

        return templates.TemplateResponse(
            "complete.html", {"request": request, "username": username}
        )


# @router.get("/todo/{username}/{year}/{month}/{day}")
@router.get("/todo")
def detail(
    request: Request,
    username,
    year,
    month,
    day,
    credentials: HTTPBasicCredentials = Depends(security),
):

    # 認証OK？
    username_tmp = auth(credentials)

    # もし他のユーザが訪問してきたらはじく
    if username_tmp != username:
        return RedirectResponse("/")

    # ユーザを取得
    conn = get_connection()
    cur = conn.cursor()
    user = read_user(cur, username)
    # 該当の日付と一致するものだけのリストにする
    deadline_date = "{}-{}-{}".format(year, month.zfill(2), day.zfill(2))
    task = read_task2(cur, user[0], deadline_date)

    cur.close()
    conn.close()

    return templates.TemplateResponse(
        "detail.html",
        {
            "request": request,
            "username": username,
            "task": task,
            "year": year,
            "month": month,
            "day": day,
        },
    )


@router.post("/done")
async def done(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    # 認証OK？
    username = auth(credentials)

    # ユーザとタスクを取得
    conn = get_connection()
    cur = conn.cursor()
    user = read_user(cur, username)
    task = read_task(cur, user[0])

    # フォームで受け取ったタスクの終了判定を見て内容を変更する
    data = await request.form()
    t_dones = data.getlist("done[]")

    task_done_id = []
    for t in task:
        if str(t[0]) in t_dones:  # もしIDが一致すれば "終了した予定" とする
            task_done_id.append(t[0])

    # 予定を終了する
    if task_done_id != []:
        update_tsak(conn, cur, task_done_id)

    cur.close()
    conn.close()

    # 管理者トップへリダイレクト
    return RedirectResponse("/admin")


@router.post("/add")
async def add(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    # 認証
    username = auth(credentials)

    # ユーザーを取得
    conn = get_connection()
    cur = conn.cursor()
    user = read_user(cur, username)

    # フォームからデータを取得
    data = await request.form()
    year = int(data["year"])
    month = int(data["month"])
    day = int(data["day"])
    hour = int(data["hour"])
    minute = int(data["minute"])

    deadline = "{}-{}-{} {}:{}:{}".format(
        year,
        str(month).zfill(2),
        str(day).zfill(2),
        str(hour).zfill(2),
        str(minute).zfill(2),
        "00",
    )
    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 新しくタスクを生成しコミット
    add_task(conn, cur, user[0], data["content"], deadline, now_time)

    cur.close()
    conn.close()

    return RedirectResponse("/admin")


@router.get("/delete")
def delete(
    request: Request, t_id, credentials: HTTPBasicCredentials = Depends(security)
):
    # 認証
    username = auth(credentials)

    # ユーザーとタスクを取得
    conn = get_connection()
    cur = conn.cursor()
    user = read_user(cur, username)
    task = read_task3(cur, t_id)

    # もしユーザIDが異なれば削除せずリダイレクト
    if task[0][1] != str(user[0][0]):
        return RedirectResponse("/admin")

    # 該当のタスクを削除しコミット
    delete_task(conn, cur, t_id)

    cur.close()
    conn.close()

    return RedirectResponse("/admin")


@router.get("/get")
def get(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    conn: session = Depends(get_connection),
):
    # 認証
    username = auth(credentials)

    # ユーザーとタスクを取得
    cur = conn.cursor()
    user = read_user(cur, username)
    task = read_task(cur, user[0])

    cur.close()
    conn.close()

    # タスク一覧をjson形式に変換
    task_json = []

    for t in task:
        param = {
            "id": t[0],
            "user_id": t[1],
            "content": t[2],
            "deadline": t[3].strftime("%Y-%m-%d %H:%M:%S"),
            "date": t[4].strftime("%Y-%m-%d %H:%M:%S"),
            "done": t[5],
        }
        task_json.append(param)

    # json文字列の作成
    jsonStr = json.dumps(task_json, ensure_ascii=False)

    # Pythonオブジェクトに変換して返す
    # task_jsonと同様なのでわざわざ上でjson文字列に変換する必要はなかったのかも
    return json.loads(jsonStr)


@router.post("/add_task")
async def insert(
    request: Request,
    content: str = Form(...),
    deadline: str = Form(...),
    credentials: HTTPBasicCredentials = Depends(security),
    conn: session = Depends(get_connection),
):
    """
    タスクを追加してJSONで新規タスクを返す
    """
    # 認証
    username = auth(credentials)

    # ユーザーを取得
    cur = conn.cursor()
    user = read_user(cur, username)

    try:
        # タスクを追加
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        add_task(conn, cur, user[0], content, deadline, now_time)

        # テーブルから新しく追加したタスクを取得する
        new_task = get_new_task(cur, user[0])

        cur.close()
        conn.close()

        task_json = []
        # タスク一覧をjson形式に変換
        param = {
            "id": new_task[0][0],
            "content": new_task[0][2],
            "deadline": new_task[0][3].strftime("%Y-%m-%d %H:%M:%S"),
            "published": new_task[0][4].strftime("%Y-%m-%d %H:%M:%S"),
            "done": new_task[0][5],
        }
        task_json.append(param)

        # json文字列の作成
        jsonStr = json.dumps(task_json, ensure_ascii=False)

        # Pythonオブジェクトに変換して返す
        # task_jsonと同様なのでわざわざ上でjson文字列に変換する必要はなかったのかも
        return json.loads(jsonStr)

    except Exception as e:

        print("=== エラー内容 ===")
        print("type:" + str(type(e)))
        print("エラー:" + str(e))
