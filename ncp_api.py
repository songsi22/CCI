import base64
import hmac
import time
import hashlib
import re
import requests

from csp_interface import CSPInterface


class NCPAPI(CSPInterface):
    """
    NCP API와 통신하기 위한 클래스.

    Args:
        access_key (str): API 인증에 사용할 액세스 키.
        secret_key (str): API 인증에 사용할 시크릿 키.
        zone (str): 서비스 존(zone) 정보.
        gov (bool): 공공 클라우드 여부 (기본값은 False).
    """

    def __init__(self, access_key, secret_key, zone, gov=False):
        self.gov = gov
        self.zone = zone
        self.access_key = access_key
        self.secret_key = secret_key
        self.BASE_URI = 'https://ncloud.apigw.gov-ntruss.com' if self.gov else 'https://ncloud.apigw.ntruss.com'

    def generate_hmac(self, uri) -> dict:
        """
        HMAC 기반의 인증 헤더를 생성하는 메서드.

        Args:
            uri (str): API 엔드포인트 URI.

        Returns:
            dict: 인증 헤더가 포함된 사전.
        """
        timestamp = str(int(time.time() * 1000))
        secret_key = bytes(self.secret_key, 'UTF-8')
        message = f"GET /vserver/v2/{uri}?responseFormatType=json\n{timestamp}\n{self.access_key}"
        message = bytes(message, 'UTF-8')
        signingKey = base64.b64encode(hmac.new(secret_key, message, digestmod=hashlib.sha256).digest())
        headers = {
            "x-ncp-apigw-timestamp": timestamp,
            "x-ncp-iam-access-key": self.access_key,
            "x-ncp-apigw-signature-v2": signingKey,
        }
        return headers

    def get_instances(self, uri):
        """
        NCP에서 모든 인스턴스 정보를 가져오는 메서드.

        Args:
            uri (str): API 엔드포인트 URI.

        Returns:
            dict: 인스턴스 정보가 포함된 사전.

        Raises:
            Exception: 요청 실패 시 예외를 발생시킵니다.
        """
        headers = self.generate_hmac(uri)
        response = requests.get(f'{self.BASE_URI}/vserver/v2/{uri}?responseFormatType=json', headers=headers)
        if response.status_code > 210:
            raise Exception(f"Failed to get instances: {response.status_code} - {response.text}")
        return response.json()

    def get_inventory(self):
        """
        인벤토리 정보를 수집하여 반환하는 메서드.

        Returns:
            list: 인벤토리 데이터가 포함된 리스트.
        """
        instances = self.get_instances('getServerInstanceList')['getServerInstanceListResponse']['serverInstanceList']
        networks = self.get_network('getNetworkInterfaceList')
        volumes = self.get_blockstorage('getBlockStorageInstanceList')['getBlockStorageInstanceListResponse'][
            'blockStorageInstanceList']
        instance_volumes = self.block_filter(instances, volumes)

        inventories = []
        for server in instances:
            publicip = server['publicIp'] if server['publicIp'] else None
            vmguestip = next((item['ip'] for item in networks if item['instanceNo'] == server['serverInstanceNo']),
                             None)
            data = {
                vmguestip: {
                    'availability_zone': server['zoneCode'],
                    'vm_state': 'RUNNING' if server['serverInstanceStatus']['code'] == 'RUN' else 'STOP',
                    'vcpus': server['cpuCount'],
                    'ram': server['memorySize'] // 1024 // 1024 // 1024,
                    'name': server['serverName'],
                    'created': server['createDate'][:10],
                    'publicip': publicip
                }
            }
            if server['serverInstanceNo'] in instance_volumes:
                data[vmguestip].update({"volumes": instance_volumes[server['serverInstanceNo']]['volumes']})
            inventories.append(data)
        return inventories

    def get_network(self, uri):
        """
        네트워크 인터페이스 정보를 가져오는 메서드.

        Args:
            uri (str): API 엔드포인트 URI.

        Returns:
            list: 네트워크 인터페이스 정보가 포함된 리스트.
        """
        headers = self.generate_hmac(uri)
        response = requests.get(f'{self.BASE_URI}/vserver/v2/{uri}?responseFormatType=json', headers=headers).json()
        networks = []
        for i in response['getNetworkInterfaceListResponse']['networkInterfaceList']:
            try:
                networks.append({'instanceNo': i['instanceNo'], 'ip': i['ip']})
            except KeyError as e:
                print(f'KeyError: {e}')  # 로깅으로 대체 가능
        return networks

    def get_blockstorage(self, uri):
        """
        블록 스토리지 정보를 가져오는 메서드.

        Args:
            uri (str): API 엔드포인트 URI.

        Returns:
            dict: 블록 스토리지 데이터가 포함된 사전.
        """
        headers = self.generate_hmac(uri)
        response = requests.get(f'{self.BASE_URI}/vserver/v2/{uri}?responseFormatType=json', headers=headers).json()
        return response

    def block_filter(self, instances, volumes):
        """
        인스턴스와 연관된 블록 스토리지를 필터링하는 메서드.

        Args:
            instances (list): 인스턴스 리스트.
            volumes (list): 볼륨 리스트.

        Returns:
            dict: 인스턴스 번호를 키로 하고, 각 인스턴스에 속한 볼륨 리스트를 값으로 가지는 사전.
        """
        instance_volumes = {instance["serverInstanceNo"]: {"instance_name": instance["serverName"], "volumes": []}
                            for instance in instances}

        for volume in volumes:
            volume_type_match = re.findall(r'\b\w*\s?(HDD|SSD)\b', volume["blockStorageDiskDetailType"]["code"])
            volume_type = volume_type_match[0] if volume_type_match else "Unknown"
            instance_id = volume["serverInstanceNo"]
            if instance_id in instance_volumes:
                instance_volumes[instance_id]["volumes"].append({
                    "device": volume["deviceName"],
                    "volume_type": volume_type,
                    "size": volume["blockStorageSize"] // 1024 // 1024 // 1024,
                    "bootable": volume["blockStorageType"]["code"] == "BASIC"
                })
        return instance_volumes
