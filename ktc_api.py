import re
import json
import requests
from csp_interface import CSPInterface
import time


class KTCAPI(CSPInterface):
    """
    KTC API와 통신하기 위한 클래스.

    Args:
        username (str): API 인증에 사용할 사용자 이름.
        password (str): API 인증에 사용할 비밀번호.
        zone (str): 서비스 존(zone) 정보 (예: 'd1', 'd2', 'd3').
        gov (bool): 공공 클라우드 여부 (기본값은 False).
    """

    BASE_URIS = {
        'gd1': 'https://api.ucloudbiz.olleh.com/gd1',
        'd1': 'https://api.ucloudbiz.olleh.com/d1',
        'd2': 'https://api.ucloudbiz.olleh.com/d2',
        'd3': 'https://api.ucloudbiz.olleh.com/d3'
    }

    def __init__(self, username, password, zone, gov=False):
        self.zone = 'gd1' if gov else zone
        self.gov = gov
        self.username = username
        self.password = password
        self.token = None
        self.token_expiry = 0
        self.project_id = None
        self.BASE_URI = self.BASE_URIS.get(self.zone)

    def authenticate(self):
        """
        API 인증을 수행하고, 토큰을 획득하는 메서드.
        """
        URL = f'{self.BASE_URI}/identity/auth/tokens'
        data = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "domain": {"id": "default"},
                            "name": self.username,
                            "password": self.password
                        }
                    }
                },
                "scope": {
                    "project": {
                        "domain": {"id": "default"},
                        "name": self.username
                    }
                }
            }
        }
        response = requests.post(URL, data=json.dumps(data))

        if response.status_code > 210:
            raise Exception(f"Authentication failed: {response.json()['error']['message']}")

        self.token = response.headers['X-Subject-Token']
        self.project_id = response.json()['token']['project']['id']
        self.token_expiry = time.time() + 3600  # 1시간 후 만료

    def get_token(self):
        """
        유효한 토큰을 반환하는 메서드. 만료된 경우 새로 인증을 시도합니다.

        Returns:
            str: 유효한 인증 토큰.
        """
        if self.token is None or time.time() >= self.token_expiry:
            self.authenticate()
        return self.token

    def get_instances(self):
        """
        모든 인스턴스의 세부 정보를 가져오는 메서드.

        Returns:
            dict: 서버 세부 정보가 포함된 사전.
        """
        token = self.get_token()
        URL = f'{self.BASE_URI}/server/servers/detail'
        headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
        response = requests.get(URL, headers=headers).json()
        return response

    def get_inventory(self):
        """
        인벤토리 정보를 가져와서 반환하는 메서드.

        Returns:
            list: 인벤토리 데이터가 포함된 리스트.
        """
        token = self.get_token()
        headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
        instances = self.get_instances()['servers']
        volumes = self.get_blockstorage()['volumes']
        instance_volumes = self.block_filter(instances, volumes)
        NT_URL = f'{self.BASE_URI}/nc/IpAddress'
        networks = requests.get(NT_URL, headers=headers).json()['nc_listentpublicipsresponse']['publicips']

        pubipes = []
        inventories = []

        for ip in networks:
            if ip['type'] == 'STATICNAT':
                pubipes.append({
                    'pubip': ip['virtualips'][0]['ipaddress'],
                    'privateip': ip['virtualips'][0]['vmguestip']
                })

        for server in instances:
            publicip = None
            vmguestip = next(iter(server['addresses'].values()))[0]['addr']
            for pubip in pubipes:
                if vmguestip in pubip['privateip']:
                    publicip = pubip['pubip']

            data = {
                vmguestip: {
                    'availability_zone': server['OS-EXT-AZ:availability_zone'],
                    'vm_state': 'RUNNING' if server['OS-EXT-STS:vm_state'] == 'active' else 'STOP',
                    'vcpus': server['flavor']['vcpus'],
                    'ram': server['flavor']['ram'] // 1024,
                    'name': server['name'],
                    'created': server['created'][:10],
                    'publicip': publicip
                }
            }

            if server['id'] in instance_volumes:
                data[vmguestip].update({"volumes": instance_volumes[server['id']]['volumes']})

            inventories.append(data)

        return inventories

    def get_blockstorage(self):
        """
        블록 스토리지 정보를 가져오는 메서드.

        Returns:
            dict: 블록 스토리지 데이터가 포함된 사전.
        """
        token = self.get_token()
        URL = f'{self.BASE_URI}/volume/{self.project_id}/volumes/detail'
        headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
        response = requests.get(URL, headers=headers).json()
        return response

    def block_filter(self, instances, volumes):
        """
        인스턴스와 연관된 블록 스토리지를 필터링하는 메서드.

        Args:
            instances (list): 인스턴스 리스트.
            volumes (list): 볼륨 리스트.

        Returns:
            dict: 인스턴스 ID를 키로 하고, 각 인스턴스에 속한 볼륨 리스트를 값으로 가지는 사전.
        """
        instance_volumes = {instance["id"]: {"instance_name": instance["name"], "volumes": []} for instance in
                            instances}

        for volume in volumes:
            volume_type_match = re.findall(r'\b\w*\s?(HDD|SSD)\b', volume["volume_type"])
            volume_type = volume_type_match[0] if volume_type_match else "Unknown"

            volume_info = {
                "volume_type": volume_type,
                "size": volume["size"],
                "bootable": volume["bootable"] == 'true'
            }

            for attachment in volume.get("attachments", []):
                instance_id = attachment["server_id"]
                if instance_id in instance_volumes:
                    instance_volumes[instance_id]["volumes"].append({
                        "device": attachment["device"],
                        "volume_type": volume_info["volume_type"],
                        "size": volume_info["size"],
                        "bootable": volume_info["bootable"]
                    })

        return instance_volumes
