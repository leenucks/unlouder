# CONFIG

import os

api_id = int('1234567') # API ID  (int)
api_hash = str("j34jkn34jon3oi4jio34") # API HASH  (str)
bot_token = str("524146561:EGETd-rwferfER_rfeER") # BOT TOKEN 524146561:EGETd-rwferfER_rfeER (str)
channel_id = int('-100145563312') # CHANNEL ID [put -1001 before channel id] 
download_dir = str(os.path.join(os.getcwd(), 'downloads'))
sessions_dir = str(os.path.join(os.getcwd(), 'sessions'))
files_dir = str(os.path.join(os.getcwd(), 'files'))
status_logs_dir = str(os.path.join(os.getcwd(), 'temp'))

def CheckDirExistence(dir):

    if not os.path.isdir(dir):
        os.mkdir(dir)

CheckDirExistence(download_dir)
CheckDirExistence(sessions_dir)
CheckDirExistence(files_dir)
CheckDirExistence(status_logs_dir)