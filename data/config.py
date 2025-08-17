from dotenv import load_dotenv
import os

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_ID = int(os.getenv("BOT_ID"))
YOUR_ACCOUNT_USERNAME = os.getenv("YOUR_ACCOUNT_USERNAME")
YOUR_ACCOUNT_ID = int(os.getenv("YOUR_ACCOUNT_ID"))

replace_links_chat = int(os.getenv("replace_links_chat"))

MYSQL_host = os.getenv("MYSQL_host")
MYSQL_user = os.getenv("MYSQL_user")
MYSQL_password = os.getenv("MYSQL_password")
MYSQL_database = os.getenv("MYSQL_database")

owners = eval(os.getenv('owners'))

BASE_WEBHOOK_URL = os.getenv('BASE_WEBHOOK_URL')
WEB_SERVER_HOST = os.getenv('WEB_SERVER_HOST')
WEB_SERVER_PORT = int(os.getenv('WEB_SERVER_PORT'))
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH')
OTHER_BOT_PATH = os.getenv('OTHER_BOT_PATH')
PATH_WITHOUT_TOKEN = os.getenv('PATH_WITHOUT_TOKEN')
FOR_OTHER_BOTS = f'{BASE_WEBHOOK_URL}/{PATH_WITHOUT_TOKEN}/'