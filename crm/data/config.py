import configparser

config = configparser.ConfigParser()

config.read('./project_configuration.ini', encoding='utf-8')

token_of_mainbot = config['CONFIGURATION']['token_of_main_bot']
owners = list(map(int, config['CONFIGURATION']['owners'].split(',')))
BASE_WEBHOOK_URL = config['CONFIGURATION']['BASE_WEBHOOK_URL']
WEB_SERVER_PORT = int(config['CONFIGURATION']['WEB_SERVER_PORT'])
WEB_SERVER_HOST = config['CONFIGURATION']['WEB_SERVER_HOST']
OTHER_BOT_PATH = config['CONFIGURATION']['OTHER_BOT_PATH']
PATH_WITHOUT_TOKEN = config['CONFIGURATION']['PATH_WITHOUT_TOKEN']
WEBHOOK_PATH = config['CONFIGURATION']['WEBHOOK_PATH']
MYSQL_host = config['CONFIGURATION']['MYSQL_host']
MYSQL_user = config['CONFIGURATION']['MYSQL_user']
MYSQL_password = config['CONFIGURATION']['MYSQL_password']
MYSQL_database = config['CONFIGURATION']['MYSQL_database']
FOR_OTHER_BOTS = f'{BASE_WEBHOOK_URL}/{PATH_WITHOUT_TOKEN}/'