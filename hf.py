import asyncio
import aiohttp
from datetime import datetime
import re,os,sys
from bs4 import BeautifulSoup as BS4
import base64
import json
from datetime import datetime
import headers_db
import random
from random import choice,randrange
import traceback

async def login(email,password):
    url='https://huggingface.co/login'
    async with aiohttp.ClientSession() as session:
        data={
            'username':email,
            'password':password
        }
        header={
            'user-agent':choice(headers_db.user_agents),
            'Accept-Language': choice(headers_db.accept_languages),
            'Accept-Encoding': choice(headers_db.encodings),
            'Connection': 'keep-alive',
            'Referer':choice(headers_db.referers),
            'X-Forwarded-For': f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        }
        async with session.post(url,headers=header,data=data,allow_redirects=False) as response:
            if response.status==302:
                rs=response.headers.get('set-cookie',None)
                if rs:
                    token=re.search('token\=(.*?)\;.*',rs).group(1)
                    print(f"{email} login success")
                    header['cookie']='token='+token
                    return header
    print(f"{email} can\'t login")
    return False
async def create_access_token(header,name='vs'):
    url='https://huggingface.co/settings/tokens/new'
    async with aiohttp.ClientSession() as session:
        async with session.get(url,headers=header) as response:
            if response.status<400:
                content=await response.text()
                soup=BS4(content,'html.parser')
                input=soup.find('input',{'name':'csrf'})
                csrf=input.get('value')
                data={
                    "csrf":csrf,
                    "role":"fineGrained",
                    "displayName":name,
                    "ownUserPermissions":[
                        "repo.content.read",
                        "repo.write",
                        "inference.endpoints.infer.write",
                        "inference.endpoints.write",
                        "user.webhooks.read",
                        "user.webhooks.write",
                        "collection.read",
                        "collection.write",
                        "discussion.write",
                        "user.billing.read"
                        ],
                    "globalPermissions":[
                        "inference.serverless.write",
                        "discussion.write",
                        "post.write"
                        ],
                    "canReadGatedRepos":"true"
                      }
                url='https://huggingface.co/api/settings/tokens'
                async with session.post(url,headers=header,json=data) as response:
                    if response.status<400:
                        js=await response.json()
                        print(f"Create new access token success")
                        return js['token']
    print("Can't create new access token")
    return False
async def create_new_space(header,name,secrets=[],sdk='docker',private=False,sleep_time_seconds=172800):
    async with aiohttp.ClientSession() as session:
        url='https://huggingface.co/new-space'
        async with session.get(url,headers=header) as response:
            if response.status==200:
                url='https://huggingface.co/api/event'
                data={"n":"pageview","u":"https://huggingface.co/new-space","d":"huggingface.co","r":None,"p":{"loggedin":"true"}}
                async with session.post(url,headers=header,json=data) as response:
                    if response.status==202:
                        url='https://huggingface.co/api/repos/create'
                        data={"sdk":"docker","hardware":"cpu-basic","storageTier":None,"sleepTimeSeconds":sleep_time_seconds,"secrets":secrets,"variables":[],"name":name,"type":"space","private":private,"devModeEnabled":False}
                        async with session.post(url,headers=header,json=data) as response:
                            if response.status<400:
                                js=await response.json()
                                async with session.get(js['url'],headers=header) as response:
                                    print(response.status)
                                print(f'Space {name} created success')
                                return js
    print(f"Space {name} can't create")
    return False
async def commit_file(header,git_path,files_path):
    url=f'https://huggingface.co/api/spaces/{git_path}/preupload/main'
    data={
        'files':[]
    }
    for path in files_path:
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            with open(path, "rb" ) as file:
                content = file.read()
                tmp={
                    'path':path.split('/')[-1],
                    'sample':base64.b64encode(content).decode('utf-8'),
                    'size':file_size
                }
                data['files'].append(tmp)

    async with aiohttp.ClientSession() as session:
        async with session.post(url,headers=header,json=data) as response:
            if response.status<400:
                js=await response.json()
                commitOid=js['commitOid']
                data=[]
                for path in files_path:
                    with open(path, "rb") as file:
                        content = file.read()
                        tmp={"key":"file","value":{"content":base64.b64encode(content).decode('utf-8'),"path":path.split('/')[-1],"encoding":"base64"}}
                        data.append(tmp)
                ns=str({"key":"header","value":{"summary":f"Upload {datetime.now().timestamp()}","description":"","parentCommit":commitOid}})+'\n'
                for st in data:
                    ns+=str(st)+'\n'
                url=f'https://huggingface.co/api/spaces/{git_path}/commit/main'
                header['content-type']='application/x-ndjson'
                async with session.post(url,headers=header,data=ns.replace("'",'"')) as response:
                    if response.status<400:
                        js=await response.json()
                        print('Commited file success')
                        return js
    print("Can't commit files")
    return False
async def create_new_file(header,git_path,file_name,content):
    url=f"https://huggingface.co/spaces/{git_path}/new/main"
    async with aiohttp.ClientSession() as session:
        async with session.get(url,headers=header) as response:
            if response.status==200:
                content_str=await response.text()
                soup=BS4(content_str,'html.parser')
                divEl=soup.find('div',{"data-target":"CommitFormEdit"})
                data_props=json.loads(divEl.get('data-props'))
                commitOid=data_props['latestCommit']
                url=f"https://huggingface.co/api/spaces/{git_path}/commit/main"
                data={
                    "description":"",
                    "summary":f"Create {file_name}",
                    "parentCommit":commitOid,
                    "files":[
                            {
                                "content":content,
                                "encoding":"utf-8",
                                "path":file_name
                            }
                        ]
                    }
                async with session.post(url,headers=header,json=data) as response:
                    if response.status<400:
                        js=await response.json()
                        print(f"{file_name} created success")
                        return js
    print(f"{file_name} can't create")
    return False
async def fke_access_page(header,url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url,headers=header,allow_redirects=False) as response:
            if response.status==200:
                url1='https://huggingface.co/api/event'
                data={"n":"pageview","u":url,"d":"huggingface.co","r":None,"p":{"loggedin":"true"}}
                async with session.post(url1,headers=header,json=data,allow_redirects=False) as response:
                    if response.status==202:
                        print(f"{url} access success")
                        return True
    print(f"{url} can't access")
    return False
async def random_action(header):
    url='https://huggingface.co/'
    async with aiohttp.ClientSession() as session:
        async with session.get(url,headers=header,allow_redirects=False) as response:
            if response.status==200:
                content=await response.text()
                soup=BS4(content,'html.parser')
                links=soup.find_all('a')
                for i in range(randrange(1,len(links) if len(links)<20 else 10)):
                    item=choice(links)
                    url=f"https://huggingface.co{item.get('href')}" if 'https://' not in item.get('href') else item.get('href')
                    try:
                        rs=await fke_access_page(header=header,url=url)
                        await asyncio.sleep(randrange(500,1500)/100)
                    except:
                        traceback.print_exc()
                print('Random actions success')
                return True
    print("Can't random actions")
    return False
async def delete_space(header,organization,space_name):
    url='https://huggingface.co/api/repos/delete'
    data={"organization":organization,"name":space_name,"type":"space"}
    async with aiohttp.ClientSession() as session:
        async with session.delete(url,headers=header,json=data,allow_redirects=False) as response:
            if response.status==200:
                print(f"{space_name} deleted success")
                return True
    print(f"{space_name} can't delete")
    return False