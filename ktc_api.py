import datetime
import json
import requests
from csp_interface import CSPInterface
import time


class KTCAPI(CSPInterface):
    def __init__(self, username, password, zone, gov):
        self.zone = zone
        self.gov = gov
        self.username = username
        self.password = password
        self.token = None
        self.token_expiry = 0
        self.project_id = None
        if self.gov:
            self.BASE_URI = 'https://api.ucloudbiz.olleh.com/gd1'
        else:
            if self.zone == 'd1':
                self.BASE_URI = 'https://api.ucloudbiz.olleh.com/d1'
            elif self.zone =='d2':
                self.BASE_URI = 'https://api.ucloudbiz.olleh.com/d3'
            elif self.zone == 'd3':
                self.BASE_URI = 'https://api.ucloudbiz.olleh.com/d3'
    def authenticate(self):
        # KTC API를 통해 토큰을 얻는 로직 (예: HTTP 요청)
        URL = f'{self.BASE_URI}/identity/auth/tokens'
        data = {
            "auth": {
                "identity": {
                    "methods": [
                        "password"
                    ],
                    "password": {
                        "user": {
                            "domain": {
                                "id": "default"
                            },
                            "name": self.username,
                            "password": self.password
                        }
                    }
                },
                "scope": {
                    "project": {
                        "domain": {
                            "id": "default"
                        },
                        "name": self.username
                    }
                }
            }
        }
        data = json.dumps(data)
        response = requests.post(URL, data=data)
        if response.status_code > 210:
            print(response.json()['error']['message'])
            exit()
        else:
            token = response.headers['X-Subject-Token']
            self.project_id = response.json()['token']['project']['id']
            self.token = token  # 실제 토큰 값으로 대체
            self.token_expiry = time.time() + 3600  # 1시간 후 만료

    def get_token(self):
        if self.token is None or time.time() >= self.token_expiry:
            self.authenticate()
        return self.token
    def get_instances(self):
        token = self.get_token()
        URL = f'{self.BASE_URI}/server/servers/detail'
        headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
        response = requests.get(URL, headers=headers).json()
        return response
    def get_inventory(self):
        token = self.get_token()
        headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
        instances = self.get_instances()
        # URL2 = f'{self.BASE_URI}/volume/{self.project_id}/volumes/detail'
        NT_URL = f'{self.BASE_URI}/nc/IpAddress'
        networks = requests.get(NT_URL, headers=headers).json()['nc_listentpublicipsresponse']['publicips']
        # privateip = [addr['addr']for server in response['servers'] for key in server['addresses'] for addr in server['addresses'][key]]
        pubipes = []
        inventories = []
        for ip in networks:
            if ip['type'] == 'STATICNAT':
                pubipes.append(
                    {'pubip': ip['virtualips'][0]['ipaddress'], 'privateip': ip['virtualips'][0]['vmguestip']})

        for server in instances['servers']:
            publicip = None
            for pubip in pubipes:
                for key in server['addresses']:
                    vmgestip = server['addresses'][key][0]['addr']
                    if vmgestip in pubip['privateip']:
                        publicip = pubip['pubip']
            data = {
                'privateip': vmgestip,
                'availability_zone': server['OS-EXT-AZ:availability_zone'],
                'vm_state': server['OS-EXT-STS:vm_state'],
                'vcpus': server['flavor']['vcpus'],
                'ram': server['flavor']['ram'] // 1024,
                'name': server['name'],
                'created': server['created'][:10],
                'publicip': publicip
            }
            # current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M")
            # with open(f'./kt-{current_time}inventory', 'a+') as f:
            #     f.write(f"{server['name']} {vmgestip}\n")
            inventories.append(data)
        return inventories

    def get_blockstorage(self):
        token = self.get_token()
        URL = f'{self.BASE_URI}/volume/{self.project_id}/volumes/detail'
        headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
        response = requests.get(URL, headers=headers).json()

