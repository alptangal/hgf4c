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
from bs4 import BeautifulSoup
load_dotenv()

FOLDER_TOKEN=os.getenv('folder_token').strip().replace("\n",'')
APP_ID=os.getenv('app_id').strip().replace("\n",'')
APP_SECRET=os.getenv('app_secret').strip().replace("\n",'')
SECRET_KEY=base64.b64decode(os.getenv('secret_key').strip())
IV=base64.b64decode(os.getenv('iv').strip())
MAIN_URL='https://huggingface.co/spaces/megaphuongdo/test'
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
async def is_running():
    url=MAIN_URL
    response=requests.get(url)
    print(response)
    if response.status_code<400:
        return 'Running' in response.text
    return False
async def restart_space():
    url=MAIN_URL
    headers={'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'}
    cookies={'token':os.getenv('hf_token')}
    response=requests.get(url,headers,cookies=cookies)
    soup=BeautifulSoup(response.text,'html.parser')
    csrf_token=soup.find('input',attrs={'name':'csrf'})['value']
    url=MAIN_URL+'/start'
    data={
        'csrf':csrf_token
    }
    headers={
        'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'referer':MAIN_URL,
        
    }
    response=requests.post(url,headers=headers,cookies=cookies,data=data)
    print(response,'Started' if response.status_code<400 else 'can\'t start')
    url=MAIN_URL.replace('.co/','.co/api/')+'/restart'#'https://huggingface.co/api/spaces/megaphuongdo/test/restart'
    response=requests.post(url,headers=headers,cookies=cookies)
    print(response,'Restarted' if response.status_code<400 else 'can\'t restart')
    if response.status_code<400:
        return True
    stop=False
    while not stop:
        result=await is_running()
        if result:
            stop=True
        await asyncio.sleep(1)
    return False

async def my_process1():
    try:
        while True:
            running=await is_running()
            if not running:
                await restart_space()
            else:
                print('Running '+MAIN_URL)
            await asyncio.sleep(1)
    except Exception as error:
        print(error)
async def main():
    try:
        req=requests.get('http://localhost:888')
        sys.exit("Exited")
    except Exception as error:
        server.b() 
        try:
            await my_process1()
        except Exception as err:
            print(err)
            traceback.print_exc()
            pass
asyncio.run(main())
