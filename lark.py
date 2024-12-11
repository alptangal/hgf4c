import aiohttp
import asyncio
import subprocess
import requests
from datetime import datetime
from aiohttp import ClientTimeout
import traceback

class LarkClass:
    def __init__(self,app_id,app_secret):
        self.tenant_token=None
        self.user_token=None
        self.app_token=None
        self.app_id=app_id
        self.app_secret=app_secret
        self.token_created_at=None
        self.expire=None
        self.headers={
            'authorization':f"Bearer {self.tenant_token or self.user_token or self.app_token}",
        }
    async def get_tenant_token(self):
        try:
            now=int(datetime.now().timestamp())
            if  not self.token_created_at or now -self.token_created_at>self.expire:
                url='https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal'
                headers={}
                data={
                    'app_id':self.app_id,
                    'app_secret':self.app_secret
                }
                async with aiohttp.ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.post(url, headers=headers, json=data) as res:
                        if res.status<400:
                            result=await res.json()
                            self.token_created_at=int(datetime.now().timestamp())
                            self.expire=result['expire']
                            self.tenant_token=result['tenant_access_token']
                            print('Get token success')
                            return True
                return False
        except Exception as err:
            traceback.print_exc()
            return False
    async def get_user_token(self):
        try:
            url='https://open.larksuite.com/open-apis/authen/v1/oidc/access_token'
            headers={}
            data={
                'app_id':self.app_id,
                'app_secret':self.app_secret
            }
            async with aiohttp.ClientSession(timeout=ClientTimeout(total=30)) as session:
                async with session.post(url, headers=headers, json=data) as res:
                    if res.status<400:
                        print('Get token success')
                        result=await res.json()
                        return result
            return False
        except Exception as err:
            print(err)
            return False
        
    async def get_app_token(self):
        try:
            url='https://open.larksuite.com/open-apis/auth/v3/app_access_token/internal'
            headers={}
            data={
                'app_id':self.app_id,
                'app_secret':self.app_secret
            }
            async with aiohttp.ClientSession(timeout=ClientTimeout(total=30)) as session:
                async with session.post(url, headers=headers, json=data) as res:
                    if res.status<400:
                        print('Get token success')
                        result=await res.json()
                        return result
            return False
        except Exception as err:
            print(err)
            return False
    async def create_new_request(self,method,url,data=None):
        await self.get_tenant_token()
        headers={
            'authorization':f"Bearer {self.tenant_token or self.user_token or self.app_token}",
        }
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=30)) as session:
            try:
                if method.lower() == "get":
                    response = await session.get(url, headers=headers)
                elif method.lower() == "post":
                    response = await session.post(url, headers=headers,json=data)
                    #print(await response.text())
                elif method.lower() == "put":
                    response = await session.put(url, headers=headers,json=data)
                elif method.lower() == "patch":
                    response = await session.patch(url, headers=headers,json=data)
                elif method.lower() == "delete":
                    if data:
                        response = await session.delete(url, headers=headers,json=data)
                    else:
                        response = await session.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                if response.status<400:
                    result=await response.json()
                    if result['code']==0 and 'data' in result:
                        return result['data']
                    else:
                        return result
                    print(result)
                if 'x-ogw-ratelimit-reset' in response.headers:
                    return {'status':'error','msg':f"Rate limit is exceeded, reconnect in {response.headers['x-ogw-ratelimit-reset']}",'reconnect_after':int(response.headers['x-ogw-ratelimit-reset'])}
            except Exception as err:
                print(err)
        return False
    async def list_files(self,folder_token):
        result=await self.create_new_request('get',f"https://open.larksuite.com/open-apis/drive/v1/files?folder_token="+folder_token)
        return result
    async def create_app(self,folder_token,name):
        data={
            "name":name,
            "folder_token": folder_token
        }
        result=await self.create_new_request('post','https://open.larksuite.com/open-apis/bitable/v1/apps',data)
        return result
    async def create_table(self,app_token,table_name,fields):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables"
        data={
            "table":{
                "name":table_name,
                "default_view_name":"Grid",
                "fields":fields
            }
        }
        result=await self.create_new_request(method='post',url=url,data=data)
        return result
    async def get_tables(self,app_token):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables"
        result=await self.create_new_request(method='get',url=url)
        if result:
            return result['items']
        return False
    async def delete_table(self,app_token,table_id):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}"
        result=await self.create_new_request(method='delete',url=url)
        if result:
            return result
        return False
    async def get_list_record(self,app_token,table_id,page_size=500,page_token=None):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size={page_size}"+(f"&page_token={page_token}" if page_token else '')
        result=await self.create_new_request(method='get',url=url)
        if result:
            return result
        return False
    async def create_new_record(self,app_token,table_id,value_fields):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        data={
            "fields":value_fields
        }
        result=await self.create_new_request(method='post',url=url,data=data)
        if result:
            return result
        return False
    async def get_record(self,app_token,table_id,record_id):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        result=await self.create_new_request(method='get',url=url)
        if result:
            return result
        return False
    async def update_record(self,app_token,table_id,record_id,value_fields):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        data={
            "fields":value_fields
        }
        result=await self.create_new_request(method='put',url=url,data=data)
        if result:
            return result
        return False
    async def delete_record(self,app_token,table_id,record_id):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        result=await self.create_new_request(method='delete',url=url)
        if result:
            return result
        return False
    async def create_new_records(self,app_token,table_id,array_value):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
        data={
            "records":array_value
        }
        result=await self.create_new_request(method='post',url=url,data=data)
        if result:
            return result
        return False
    async def update_records(self,app_token,table_id,array_value):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update"
        data={
            "records":array_value
        }
        result=await self.create_new_request(method='post',url=url,data=data)
        if result:
            return result
        return False
    async def delete_records(self,app_token,table_id,array_record_id):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_delete"
        data={
            'records':array_record_id
        }
        result=await self.create_new_request(method='post',url=url,data=data)
        if result:
            return result
        return False
    async def get_list_fields(self,app_token,table_id,page_size=100,page_token=None):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields?page_size={page_size}"+(f"page_token={page_token}" if page_token else '')
        result=await self.create_new_request(method='get',url=url)
        if result:
            return result
        return False
    async def get_bot_info(self):
        url=f"https://open.larksuite.com/open-apis/bot/v3/info"
        headers={
            'authorization':f"Bearer {self.tenant_token or self.user_token or self.app_token}",
        }
        async with aiohttp.ClientSession() as session:
            result = await session.get(url, headers=headers)
            if result.status<400:
                js=await result.json()
                return js['bot']
        return False
    async def search_record(self,app_token,table_id,conditions_array,page_size=500,page_token=None,conjunction='and'):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search?page_size={page_size}"+(f'&page_token={page_token}' if page_token else '')
        headers={
            'authorization':f"Bearer {self.tenant_token or self.user_token or self.app_token}",
        }
        data={
            "filter": {
                "conjunction": conjunction,
                "conditions": conditions_array
            },
        }
        result=await self.create_new_request(method='post',url=url,data=data)
        if result:
            return result
        return False
    async def download_file(self,url,file_name):
        headers={
            'authorization':f"Bearer {self.tenant_token or self.user_token or self.app_token}",
        }
        try:
            response = requests.get(url,headers=headers)
            if response.status_code == 200:
                with open(file_name, 'wb') as file:
                    file.write(response.content)
                print(f"Tệp đã được tải xuống thành công và lưu thành {file_name}.")
                return file_name
            else:
                print(f"Lỗi tải tệp: {response.status_code}")
        except Exception as err:
            print(f'Can\'t download file. Error- {err}')
        return False
    async def create_table(self,app_token,table_name,fields_array):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables"
        data={
            "table":{
                "name":table_name,
                "default_view_name":"Grid",
                "fields":fields_array
            }
        }
        result=await self.create_new_request(method='post',url=url,data=data)
        if result:
            return result
        return False
    async def rename_table(self,app_token,table_id,new_name):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}"
        data={
            'name':new_name
        }
        result=await self.create_new_request(method='PATCH',url=url,data=data)
        if result:
            return result
        return False
    async def delete_table(self,app_token,table_id):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}"
        result=await self.create_new_request(method='delete',url=url)
        if result:
            return result
        return False
    async def get_list_files(self,page_size=200,folder_token=None,page_token=None):
        url=f'https://open.larksuite.com/open-apis/drive/v1/files?page_size={page_size}'+(f"&folder_token={folder_token}" if folder_token else '')+(f"&page_token={page_token}" if page_token else '')
        result=await self.create_new_request(method='get',url=url)
        if result:
            return result
        return False
    async def get_root_folder_meta(self):
        url=f"https://open.larksuite.com/open-apis/drive/explorer/v2/root_folder/meta"
        result=await self.create_new_request(method='get',url=url)
        if result:
            return result
        return False
    async def rename_app(self,app_token,new_name):
        url=f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}"
        data={
            "name": new_name
        }
        result=await self.create_new_request(method='put',url=url,data=data)
        if result:
            return result
        return False