from mangum import Mangum
from main.main import app

handler = Mangum(app)