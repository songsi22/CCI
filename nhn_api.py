import json
import requests
import re
from csp_interface import CSPInterface
import time


class NHNAPI(CSPInterface):
    """
    NHN API와 통신하기 위한 클래스.

    Args:
        username (str): API 인증에 사용할 사용자 이름.
        password (str): API 인증에 사용할 비밀번호.
        tenantid (str): 테넌트 ID.
        zone (str): 서비스 존(zone) 정보.
        gov (bool): 공공 클라우드 여부 (기본값은 False).
    """

    def __init__(self, username, password, tenantid, zone, gov=False):
        self.gov = gov
        self.zone = zone
        self.username = username
        self.password = password
        self.tenantid = tenantid
        self.token = None
        self.token_expiry = 0

        self.BASE_AUTH_URI, self.VM_BASE_URI, self.ST_BASE_URI = self._initialize_uris()

    def _initialize_uris(self):
        """
        NHN API의 URI들을 초기화하는 헬퍼 메서드.

        Returns:
            tuple: 인증, VM, 스토리지 URI의 튜플.
        """
        if self.gov:
            base_auth_uri = 'https://api-identity-infrastructure.gov-nhncloudservice.com'
            if self.zone == 'kr1':
                vm_base_uri = 'https://kr1-api-instance-infrastructure.gov-nhncloudservice.com'
                st_base_uri = 'https://kr1-api-block-storage-infrastructure.gov-nhncloudservice.com'
            elif self.zone == 'kr2':
                vm_base_uri = 'https://kr2-api-instance-infrastructure.gov-nhncloudservice.com'
                st_base_uri = 'https://kr2-api-block-storage-infrastructure.gov-nhncloudservice.com'
        else:
            base_auth_uri = 'https://api-identity-infrastructure.nhncloudservice.com'
            if self.zone == 'kr1':
                vm_base_uri = 'https://kr1-api-instance-infrastructure.nhncloudservice.com'
                st_base_uri = 'https://kr1-api-block-storage-infrastructure.nhncloudservice.com'
            elif self.zone == 'kr2':
                vm_base_uri = 'https://kr2-api-instance-infrastructure.nhncloudservice.com'
                st_base_uri = 'https://kr2-api-block-storage-infrastructure.nhncloudservice.com'
            elif self.zone == 'jp1':
                vm_base_uri = 'https://jp1-api-instance-infrastructure.nhncloudservice.com'
                st_base_uri = 'https://jp1-api-block-storage-infrastructure.nhncloudservice.com'

        return base_auth_uri, vm_base_uri, st_base_uri

    def authenticate(self):
        """
        API 인증을 수행하고, 토큰을 획득하는 메서드.
        """
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
        response = requests.post(URL, data=json.dumps(data), headers=headers)
        if response.status_code > 210:
            raise Exception(f"Authentication failed: {response.status_code} - {response.json()['error']['message']}")

        response = response.json()
        self.token = response['access']['token']['id']
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
        NHN에서 모든 인스턴스 정보를 가져오는 메서드.

        Returns:
            dict: 인스턴스 정보가 포함된 사전.

        Raises:
            Exception: 요청 실패 시 예외를 발생시킵니다.
        """
        token = self.get_token()
        URL = f'{self.VM_BASE_URI}/v2/{self.tenantid}/servers/detail'
        headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
        response = requests.get(URL, headers=headers)
        if response.status_code > 210:
            raise Exception(f"Failed to get instances: {response.status_code} - {response.text}")

        return response.json()

    def filter_flavors(self, flavor_id):
        """
        주어진 플레이버 ID에 해당하는 플레이버 정보를 반환하는 메서드.

        Args:
            flavor_id (str): 플레이버 ID.

        Returns:
            str: 플레이버 이름에서 CPU와 메모리 정보를 추출한 문자열.
        """
        token = self.get_token()
        URL = f'{self.VM_BASE_URI}/v2/{self.tenantid}/flavors'
        headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
        flavors = requests.get(URL, headers=headers).json()['flavors']
        for flavor in flavors:
            if flavor['id'] == flavor_id:
                return flavor['name'].split('.')[1]

    def get_inventory(self):
        """
        인벤토리 정보를 수집하여 반환하는 메서드.

        Returns:
            list: 인벤토리 데이터가 포함된 리스트.
        """
        instances = self.get_instances()['servers']
        volumes = self.get_blockstorage()['volumes']
        instance_volumes = self.block_filter(instances, volumes)
        inventories = []

        for server in instances:
            type_info = self.filter_flavors(server['flavor']['id'])
            publicip = None
            for address in server['addresses']:
                for addr in server['addresses'][address]:
                    if addr['OS-EXT-IPS:type'] == 'floating':
                        publicip = addr['addr']
                    else:
                        vmguestip = addr['addr']
                break
            match = re.compile(r'c(\d+)m(\d+)').match(type_info)
            if match:
                cpu = match.group(1)
                mem = match.group(2)
            data = {
                vmguestip: {
                    'availability_zone': server['OS-EXT-AZ:availability_zone'],
                    'vm_state': 'RUNNING' if server['OS-EXT-STS:vm_state'] == 'active' else 'STOP',
                    'vcpus': cpu,
                    'ram': mem,
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
        URL = f'{self.ST_BASE_URI}/v2/{self.tenantid}/volumes/detail'
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
        instance_volumes = {instance["id"]: {"instance_name": instance["name"], "volumes": []}
                            for instance in instances}

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
                        "bootable": volume["bootable"] == 'true'
                    })

        return instance_volumes
