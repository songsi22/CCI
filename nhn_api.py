import json
import datetime
import requests
import re
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
                self.VM_BASE_URI = 'https://kr1-api-instance-infrastructure.gov-nhncloudservice.com'
                self.ST_BASE_URI = 'https://kr1-api-block-storage-infrastructure.gov-nhncloudservice.com'
            elif self.zone == 'kr2':
                self.VM_BASE_URI = 'https://kr2-api-instance-infrastructure.gov-nhncloudservice.com'
                self.ST_BASE_URI = 'https://kr2-api-block-storage-infrastructure.gov-nhncloudservice.com'

        else:
            self.BASE_AUTH_URI = 'https://api-identity-infrastructure.nhncloudservice.com'
            if self.zone == 'kr1':
                self.VM_BASE_URI = 'https://kr1-api-instance-infrastructure.nhncloudservice.com'
                self.ST_BASE_URI = 'https://kr1-api-block-storage-infrastructure.nhncloudservice.com'
            elif self.zone == 'kr2':
                self.VM_BASE_URI = 'https://kr2-api-instance-infrastructure.nhncloudservice.com'
                self.ST_BASE_URI = 'https://kr2-api-block-storage-infrastructure.nhncloudservice.com'
            elif self.zone == 'jp1':
                self.VM_BASE_URI = 'https://jp1-api-instance-infrastructure.nhncloudservice.com'
                self.ST_BASE_URI = 'https://jp1-api-block-storage-infrastructure.nhncloudservice.com'

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

    def get_instances(self):
        token = self.get_token()
        URL = f'{self.VM_BASE_URI}/v2/{self.tenantid}/servers/detail'
        headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
        response = requests.get(URL, headers=headers)
        if response.status_code > 210:
            raise Exception(f"Failed to get instances: {response.status_code} - {response.text}")
            exit()
        else:
            response = response.json()
            return response

    def get_inventory(self):
        instances = self.get_instances()['servers']
        volumes = self.get_blockstorage()['volumes']
        instance_volumes = self.block_filter(instances, volumes)

        inventories = []
        for server in instances:
            publicip = None
            for address in server['addresses']:
                for addr in server['addresses'][address]:
                    if addr['OS-EXT-IPS:type'] in 'floating':
                        publicip = addr['addr']
                    else:
                        vmgestip = addr['addr']
                break
            data = {
                vmgestip: {
                'availability_zone': server['OS-EXT-AZ:availability_zone'],
                'vm_state': 'RUNNING' if server['OS-EXT-STS:vm_state'] == 'active' else 'STOP',
                'name': server['name'],
                'created': server['created'][:10],
                'publicip': publicip
                }
            }
            if server['id'] in instance_volumes:
                data[vmgestip].update({"volumes": instance_volumes[server['id']]['volumes']})
            # current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M")
            # with open(f'./nhn-{current_time}-inventory', 'a+') as f:
            #     f.write(f"{server['name']} {vmgestip}\n")
            inventories.append(data)
        return inventories

    def get_blockstorage(self):
        token = self.get_token()
        URL = f'{self.ST_BASE_URI}/v2/{self.tenantid}/volumes/detail'
        headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
        response = requests.get(URL, headers=headers).json()
        return response

    def block_filter(self, instances, volumes):
        instances = instances
        volumes = volumes

        instance_volumes = {}

        for instance in instances:
            instance_volumes[instance["id"]] = {
                "instance_name": instance["name"],
                "volumes": []
            }

        for volume in volumes:
            volume_type_match = re.findall(r'\b\w*\s?(HDD|SSD)\b', volume["volume_type"])
            volume_type = volume_type_match[0] if volume_type_match else "Unknown"
            volume_info = {
                "volume_type": volume_type,
                "size": volume["size"]
            }

            for attachment in volume.get("attachments", []):
                instance_id = attachment["server_id"]
                if instance_id in instance_volumes:
                    instance_volumes[instance_id]["volumes"].append({
                        "device": attachment["device"],
                        "volume_type": volume_info["volume_type"],
                        "size": volume_info["size"],
                        "bootable": True if volume["bootable"] == 'true' else False
                    })
        return instance_volumes
