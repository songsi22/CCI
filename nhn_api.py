import json
import datetime
import requests

from csp_interface import CSPInterface
import time


class NHNAPI(CSPInterface):
    def __init__(self, username, password, tenantid, zone, gov):
        self.gov = gov
        self.zone = zone
        self.username = username
        self.password = password
        self.tenantid = tenantid
        self.token = None
        self.token_expiry = 0
        if self.gov:
            self.BASE_AUTH_URI = 'https://api-identity-infrastructure.gov-nhncloudservice.com'
            if self.zone == 'kr1':
                self.BASE_URI = 'https://kr1-api-instance-infrastructure.gov-nhncloudservice.com'
            elif self.zone == 'kr2':
                self.BASE_URI = 'https://kr2-api-instance-infrastructure.gov-nhncloudservice.com'
        else:
            self.BASE_AUTH_URI = 'https://api-identity-infrastructure.nhncloudservice.com'
            if self.zone == 'kr1':
                self.BASE_URI = 'https://kr1-api-instance-infrastructure.nhncloudservice.com'
            elif self.zone == 'kr2':
                self.BASE_URI = 'https://kr2-api-instance-infrastructure.nhncloudservice.com'
            elif self.zone == 'jp1':
                self.BASE_URI = 'https://jp1-api-instance-infrastructure.nhncloudservice.com'

    def authenticate(self):
        # NHN API를 통해 토큰을 얻는 로직 (예: HTTP 요청)
        URL = f'{self.BASE_AUTH_URI}/v2.0/tokens'
        data = {
            "auth": {
                "tenantId": self.tenantid,
                "passwordCredentials": {
                    "username": self.username,
                    "password": self.password
                }
            }
        }
        headers = {'Content-Type': 'application/json'}
        data = json.dumps(data)
        response = requests.post(URL, data=data, headers=headers)
        if response.status_code > 210:
            print(response.json()['error']['message'])
            exit()
        else:
            response = response.json()
            token = response['access']['token']['id']
            self.token = token  # 실제 토큰 값으로 대체
            self.token_expiry = time.time() + 3600  # 1시간 후 만료

    def get_token(self):
        if self.token is None or time.time() >= self.token_expiry:
            self.authenticate()
        return self.token

    def get_inventory(self):
        token = self.get_token()
        URL = f'{self.BASE_URI}/v2/{self.tenantid}/servers/detail'
        headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
        response = requests.get(URL, headers=headers)
        if response.status_code > 210:
            print(response.json()['error']['message'])
        else:
            response = response.json()
            inventories = []
            for server in response['servers']:
                publicip = None
                for address in server['addresses']:
                    for addr in server['addresses'][address]:
                        if addr['OS-EXT-IPS:type'] in 'floating':
                            publicip = addr['addr']
                        else:
                            vmgestip = addr['addr']
                    break
                data = {
                    'privateip': vmgestip,
                    'availability_zone': server['OS-EXT-AZ:availability_zone'],
                    'vm_state': server['OS-EXT-STS:vm_state'],
                    'name': server['name'],
                    'created': server['created'][:10],
                    'publicip': publicip
                }
                # current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M")
                # with open(f'./nhn-{current_time}-inventory', 'a+') as f:
                #     f.write(f"{server['name']} {vmgestip}\n")
                inventories.append(data)
            return inventories
