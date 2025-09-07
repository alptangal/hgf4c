import sys,os,time,json
from datetime import datetime
from random import randrange,choice
import random
import asyncio
import lark as basic
#import hf
from dotenv import load_dotenv
import aiohttp,requests
import traceback
import server
import string
import headers_db
import encrypt
import base64
import shutil
load_dotenv()

FOLDER_TOKEN=os.getenv('folder_token').strip().replace("\n",'')
APP_ID=os.getenv('app_id').strip().replace("\n",'')
APP_SECRET=os.getenv('app_secret').strip().replace("\n",'')
SECRET_KEY=base64.b64decode(os.getenv('secret_key').strip())
IV=base64.b64decode(os.getenv('iv').strip())

folder_path = "downloads"
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
    print(f"Folder '{folder_path}' created.")
else:
    print(f"Folder '{folder_path}' already exists.")
def generate_random_string(length):
    if length <= 0:
        raise ValueError("Length must be a positive integer.")

    characters = string.ascii_letters + string.digits
    return ''.join(choice(characters) for _ in range(length))
def generate_random_string_with_shift(length):
    if length < 2:
        raise ValueError("Độ dài chuỗi phải lớn hơn hoặc bằng 2.")
    chars = string.ascii_letters + string.digits + '-'
    middle_part = ''.join(random.choices(chars, k=length - 2))
    first_char = random.choice(string.ascii_letters + string.digits)
    last_char = random.choice(string.ascii_letters + string.digits)

    random_string = first_char + middle_part + last_char
    return random_string
def is_running():
    url='https://huggingface.co/spaces/megaphuongdo/test1'
    response=requests.get(url)
    if response.status_code<400:
        return 'Running' in response.text
    return False
def restart_space():
    url='https://huggingface.co/api/spaces/megaphuongdo/test1/restart'
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
        'Cookie': 'token='+os.getenv('hf_token')+';'
    }
    response=requests.post(url,headers)
    if response.status_code<400:
        return True
    return False

async def my_process1():
    try:
        while True:
            if not is_running():
                restart_space()
            await asyncio.sleep(15)
    except Exception as error:
        print(error)
async def main():
    try:
        req=requests.get('http://localhost:8888')
        sys.exit("Exited")
    except Exception as error:
        server.b() 
        try:
            await my_process1()
        except Exception as err:
            traceback.print_exc()
            pass
asyncio.run(main())
