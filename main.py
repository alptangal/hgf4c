import sys,os,time
from datetime import datetime
from random import randrange
import asyncio
import lark as basic
import hf
from dotenv import load_dotenv
import aiohttp,requests
import traceback
load_dotenv()

FOLDER_TOKEN=os.getenv('folder_token').strip().replace("\n",'')
APP_ID=os.getenv('app_id').strip().replace("\n",'')
APP_SECRET=os.getenv('app_secret').strip().replace("\n",'')

folder_path = "downloads"
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
    print(f"Folder '{folder_path}' created.")
else:
    print(f"Folder '{folder_path}' already exists.")
async def main():
    try:
        while True:
            lark=basic.LarkClass(APP_ID,APP_SECRET)
            base_token=None
            page_token=None
            while True:
                result=await lark.get_list_files(folder_token=FOLDER_TOKEN,page_token=page_token)
                if result:
                    if 'huggingfaces_db' in str(result['files']):
                        for file in result['files']:
                            if 'huggingfaces_db' == file['name']:
                                base_token=file['token']
                if 'has_more' in result and result['has_more']:
                    page_token=result['next_page_token']
                else:
                    break
            if base_token:
                page_token=None
                accounts_table_id=None
                spaces_table_id=None
                while True:
                    result=await lark.get_tables(app_token=base_token)
                    if result:
                        for table in result:
                            if 'accounts'==table['name']:
                                accounts_table_id=table['table_id']
                            elif 'spaces' ==table['name']:
                                spaces_table_id=table['table_id']
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
                                token=record['fields']['TOKEN'][0]['text'] if 'TOKEN' in record['fields'] else None
                                if not token:
                                    token=await hf.login(email=email,password=password)
                                    await lark.update_record(app_token=base_token,table_id=accounts_table_id,record_id=record_id,value_fields={'TOKEN':token})
                                header={
                                    'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 uacq',
                                    'cookie':'token='+token
                                }
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
                                            'field_name':'FILES',
                                            'operator':'isNotEmpty',
                                            'value':[]
                                        }
                                    ]
                                    page_token1=None
                                    while True:
                                        result1=await lark.search_record(app_token=base_token,table_id=spaces_table_id,conditions_array=conditions_array1,page_token=page_token1)
                                        if result1 and 'items' in result1:
                                            for space in result1['items']:
                                                space_record_id=space['record_id']
                                                space_name=space['fields']['NAME'][0]['text']
                                                space_files=space['fields']['FILES']
                                                files_path=[]
                                                for file in space_files:
                                                    rs=await lark.download_file(file['url'],file_name=f"downloads/{file['name']}")
                                                    if rs:
                                                        files_path.append(f"downloads/{file['name']}")
                                                secrets=[
                                                    {
                                                        'key':'app_id',
                                                        'value':'cli_a7b8ab263e78d02f'
                                                    },
                                                    {
                                                        'key':'app_secret',
                                                        'value':'a1lm2lLyCnF230lEuuisTfD6u5kY0xY1'
                                                    },
                                                    {
                                                        'key':'base_token',
                                                        'value':'GJhXbg4l5aRzjBsUsl6lFaRjgfZ'
                                                    },
                                                    {
                                                        'key':'secret_key',
                                                        'value':'uq32lXwH4NQdYNlVjNbr1u1izkSosPc90moet7HyoiE='
                                                    },
                                                    {
                                                        'key':'iv',
                                                        'value':'EPvZwpHV+NJLspDM5t1+iQ=='
                                                    }
                                                ]
                                                rs=await hf.create_new_space(header=header,name=space_name,secrets=secrets)
                                                if rs:
                                                    git_path=rs['name']
                                                    await lark.update_record(app_token=base_token,table_id=spaces_table_id,record_id=space_record_id,value_fields={'GIT_PATH':git_path,'STATUS':'completed','URL':f"https://{git_path.replace('/','-')}.hf.space"})
                                                    file_content="""#!/bin/bash
            uvicorn app:app --host 0.0.0.0 --port 7860 &
            python encrypt.py
            wait

            #entrypoint.sh              
                                                    """
                                                    await hf.create_new_file(header=header,git_path=git_path,file_name='entrypoint.sh',content=file_content)
                                                    await hf.commit_file(header=header,git_path=git_path,files_path=files_path)
                                                    
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
                                                await lark.delete_record(app_token=base_token,table_id=spaces_table_id,record_id=item['record_id'])
                                        if 'has_more' in result1 and result1['has_more']:
                                            page_token=result1['page_token']
                                        else:
                                            break
                        if 'has_more' in result and result['has_more']:
                            page_token=result['page_token']
                        else:
                            break
            await asyncio.sleep(3)
    except:
        traceback.print_exc()
        pass

asyncio.run(main())