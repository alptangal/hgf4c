import sys,os,time,json
from datetime import datetime
from random import randrange,choice
import random
import asyncio
import lark as basic
import hf
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
async def my_process():
    try:
        while True:
            lark=basic.LarkClass(APP_ID,APP_SECRET)
            base_token=None
            lark_db_token=None
            page_token=None
            while True:
                result=await lark.get_list_files(folder_token=FOLDER_TOKEN,page_token=page_token)
                if result:
                    for file in result['files']:
                        if 'huggingfaces_db' == file['name'].lower():
                            base_token=file['token']
                        elif 'lark_db' == file['name'].lower():
                            lark_db_token=file['token']
                if result and 'has_more' in result and result['has_more']:
                    page_token=result['next_page_token']
                else:
                    break
            if base_token and lark_db_token:
                page_token=None
                apps_table_id=None
                while True:
                    result=await lark.get_tables(app_token=lark_db_token)
                    if result:
                        for table in result:
                            if 'apps'==table['name']:
                                apps_table_id=table['table_id']
                    if 'has_more' in result and result['has_more']:
                        page_token=result['next_page_token']
                    else:
                        break
                lark_apps=[]
                if apps_table_id:
                    page_token=None
                    conditions_array=[
                        {
                            'field_name':'TYPE',
                            'operator':'doesNotContain',
                            'value':['do_not_use']
                        },
                    ]
                    while True:
                        result=await lark.search_record(app_token=lark_db_token,table_id=apps_table_id,page_token=page_token,conditions_array=conditions_array)
                        if result and 'items' in result:
                            lark_apps+=result['items']
                        if 'has_more' in result and result['has_more']:
                            page_token=result['next_page_token']
                        else:
                            break
                page_token=None
                accounts_table_id=None
                spaces_table_id=None
                packages_table_id=None
                while True:
                    result=await lark.get_tables(app_token=base_token)
                    if result:
                        for table in result:
                            if 'accounts'==table['name']:
                                accounts_table_id=table['table_id']
                            elif 'spaces' ==table['name']:
                                spaces_table_id=table['table_id']
                            elif 'packages' ==table['name']:
                                packages_table_id=table['table_id']
                    if 'has_more' in result and result['has_more']:
                        page_token=result['next_page_token']
                    else:
                        break
                if accounts_table_id:
                    page_token=None
                    conditions_array=[
                        {
                            'field_name':'STATUS',
                            'operator':'contains',
                            'value':['alive']
                        },
                        {
                            'field_name':'PASSWORD',
                            'operator':'isNotEmpty',
                            'value':[]
                        }
                    ]
                    while True:
                        result=await lark.search_record(app_token=base_token,table_id=accounts_table_id,page_token=page_token,conditions_array=conditions_array)
                        if result and 'items' in result:
                            for record in result['items']:
                                record_id=record['record_id']
                                email=record['fields']['EMAIL'][0]['text']
                                password=record['fields']['PASSWORD']
                                header=None
                                if 'TOKEN' in record['fields']:
                                    st=''
                                    for tmp in record['fields']['TOKEN']:
                                        st+=tmp['text']
                                    header=json.loads(st)
                                if not header:
                                    header=await hf.login(email=email,password=password)
                                    await lark.update_record(app_token=base_token,table_id=accounts_table_id,record_id=record_id,value_fields={'TOKEN':json.dumps(header)})
                                await hf.random_action(header=header)
                                req=requests.get('https://huggingface.co/new-space',headers=header,allow_redirects=False)
                                if req.status_code==200:
                                    await lark.update_record(app_token=base_token,table_id=accounts_table_id,record_id=record_id,value_fields={'STATUS':'alive'})
                                    conditions_array1=[
                                        {
                                            'field_name':'STATUS',
                                            'operator':'contains',
                                            'value':['waiting']
                                        },
                                        {
                                            'field_name':'OWNER',
                                            'operator':'contains',
                                            'value':[record_id]
                                        },
                                        {
                                            'field_name':'PACKAGE',
                                            'operator':'isNotEmpty',
                                            'value':[]
                                        }
                                    ]
                                    page_token1=None
                                    while True:
                                        result1=await lark.search_record(app_token=base_token,table_id=spaces_table_id,conditions_array=conditions_array1,page_token=page_token1)
                                        if result1 and 'items' in result1:
                                            for space in result1['items']:
                                                folder_path = f"downloads/{int(datetime.now().timestamp())}"
                                                if not os.path.exists(folder_path):
                                                    os.makedirs(folder_path)
                                                    print(f"Folder '{folder_path}' created.")
                                                else:
                                                    print(f"Folder '{folder_path}' already exists.")
                                                space_record_id=space['record_id']
                                                space_name=space['fields']['NAME'][0]['text']
                                                if 'random'==space_name:
                                                    space_name=generate_random_string_with_shift(length=randrange(12,40))
                                                package_record_id=space['fields']['PACKAGE']['link_record_ids'][0]
                                                package_info=await lark.get_record(app_token=base_token,table_id=packages_table_id,record_id=package_record_id)
                                                space_files=package_info['record']['fields']['FILES']
                                                files_path=[]
                                                for file in space_files:
                                                    rs=await lark.download_file(file['url'],file_name=f"{folder_path}/{file['name']}")
                                                    if rs:
                                                        files_path.append(f"{folder_path}/{file['name']}")
                                                if not os.path.exists(f'{folder_path}/bin'):
                                                    ext=generate_random_string(randrange(3,10))
                                                    with open(f'{folder_path}/bin', 'w') as file:
                                                        file.write(ext)
                                                else:
                                                    with open(f'{folder_path}/bin', 'r') as file:
                                                        ext = file.read()
                                                files_arr=[]
                                                str_files=[]
                                                for file in files_path:
                                                    file_name,old_ext_file=os.path.splitext(file)
                                                    if old_ext_file!='' and old_ext_file=='.py' and 'encrypt.py' not in file:
                                                        file_en=generate_random_string(length=randrange(20,50))
                                                        rs=encrypt.do_encrypt(file,f'{folder_path}/'+file_en,SECRET_KEY,IV)
                                                        if rs:
                                                            files_arr.append(rs)
                                                            str_files.append(base64.b64encode(f"{datetime.now().timestamp()}||{file_en}||{file.replace(f'{folder_path}/','')}".encode('utf-8')).decode('utf-8'))
                                                    else:
                                                        files_arr.append(file)
                                                with open(f'{folder_path}/list', 'w') as file:
                                                    for item in str_files:
                                                        file.write(item + "\n")
                                                files_path=files_arr
                                                files_path.append(f'{folder_path}/bin')
                                                files_path.append(f'{folder_path}/list')
                                                random_app=choice(lark_apps)
                                                secrets=[
                                                    {
                                                        'key':'app_id',
                                                        'value':random_app['fields']['APP_ID'][0]['text']
                                                    },
                                                    {
                                                        'key':'app_secret',
                                                        'value':random_app['fields']['APP_SECRET'][0]['text']
                                                    },
                                                    {
                                                        'key':'base_token',
                                                        'value':'GJhXbg4l5aRzjBsUsl6lFaRjgfZ'
                                                    },
                                                    {
                                                        'key':'secret_key',
                                                        'value':os.getenv('secret_key').strip()
                                                    },
                                                    {
                                                        'key':'iv',
                                                        'value':os.getenv('iv').strip()
                                                    },
                                                    {
                                                        'key':'folder_token',
                                                        'value':FOLDER_TOKEN
                                                    }
                                                ]
                                                header=await hf.login(email=email,password=password)
                                                try:
                                                    rs=await hf.create_new_space(header=header,name=space_name,secrets=secrets)
                                                except:
                                                    traceback.print_exc()
                                                    pass
                                                await hf.random_action(header=header)
                                                if rs:
                                                    git_path=rs['name']
                                                    await lark.update_record(app_token=base_token,table_id=spaces_table_id,record_id=space_record_id,value_fields={'NAME':space_name,'GIT_PATH':git_path,'STATUS':'completed','URL':f"https://{git_path.replace('/','-')}.hf.space"})
                                                    file_content="""#!/bin/bash
            uvicorn app:app --host 0.0.0.0 --port 7860 &
            python encrypt.py
            wait

            #entrypoint.sh              
                                                    """
                                                    try:
                                                        await hf.create_new_file(header=header,git_path=git_path,file_name='entrypoint.sh',content=file_content)
                                                        await hf.commit_file(header=header,git_path=git_path,files_path=files_path)
                                                    except:
                                                        traceback.print_exc()
                                                        pass
                                                    if os.path.exists(folder_path) and os.path.isdir(folder_path):
                                                        shutil.rmtree(folder_path)
                                                        print(f"Thư mục '{folder_path}' đã được xóa.")
                                                    else:
                                                        print(f"Thư mục '{folder_path}' không tồn tại.")
                                        if 'has_more' in result1 and result1['has_more']:
                                            page_token=result1['page_token']
                                        else:
                                            break
                                else:
                                    print(f"{email} is suspended")
                                    await lark.update_record(app_token=base_token,table_id=accounts_table_id,record_id=record_id,value_fields={'STATUS':'dead'})
                                    page_token1=None
                                    conditions_array1=[
                                        {
                                            'field_name':'OWNER',
                                            'operator':'contains',
                                            'value':[record_id]
                                        }
                                    ]
                                    while True:
                                        result1=await lark.search_record(app_token=base_token,table_id=spaces_table_id,conditions_array=conditions_array1,page_token=page_token1)
                                        if result1 and 'items' in result1:
                                            for item in result1['items']:
                                                await lark.update_record(app_token=base_token,table_id=spaces_table_id,record_id=item['record_id'],value_fields={'STATUS':'dead'})
                                        if 'has_more' in result1 and result1['has_more']:
                                            page_token=result1['page_token']
                                        else:
                                            break
                        if result and 'has_more' in result and result['has_more']:
                            page_token=result['page_token']
                        else:
                            break
            await asyncio.sleep(3)
    except:
        traceback.print_exc()
        pass

async def main():
    try:
        req=requests.get('http://localhost:8888')
        sys.exit("Exited")
    except Exception as error:
        server.b() 
        try:
            await my_process()
        except Exception as err:
            traceback.print_exc()
            pass
asyncio.run(main())