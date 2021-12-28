from fastapi import Depends, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from requests.sessions import session
from starlette.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import RedirectResponse
from fastapi import APIRouter

router = APIRouter()

security = HTTPBasic()

# テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")
# Jinja2.Environment : filterやglobalの設定用
jinja_env = templates.env


@router.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
