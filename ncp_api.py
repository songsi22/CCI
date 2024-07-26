import base64
import datetime
import hmac
import time
import hashlib
import re
import requests

from csp_interface import CSPInterface


class NCPAPI(CSPInterface):
    def __init__(self, access_key, secret_key, zone, gov):
        self.gov = gov
        self.zone = zone
        self.access_key = access_key
        self.secret_key = secret_key
        if self.gov:
            self.BASE_URI = 'https://ncloud.apigw.gov-ntruss.com'
        else:
            self.BASE_URI = 'https://ncloud.apigw.ntruss.com'

    def generate_hmac(self, uri) -> dict:
        # HMAC 생성 로직
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
        headers = self.generate_hmac(uri)
        response = requests.get(f'{self.BASE_URI}/vserver/v2/{uri}?responseFormatType=json', headers=headers)
        if response.status_code > 210:
            raise Exception(f"Failed to get instances: {response.status_code} - {response.text}")
            exit()
        else:
            response = response.json()
            return response

    def get_inventory(self, uri):
        instances = self.get_instances('getServerInstanceList')
        networks = self.get_network('getNetworkInterfaceList')
        inventories = []
        for server in instances['getServerInstanceListResponse']['serverInstanceList']:
            if server['publicIp'] == '':
                publicip = None
            else:
                publicip = server['publicIp']
            vmgestip = next((item['ip'] for item in networks if item['instanceNo'] == server['serverInstanceNo']),
                            None)
            data = {
                'privateip': vmgestip,
                'availability_zone': server['zoneCode'],
                'vm_state': server['serverInstanceStatus']['code'],
                'vcpus': server['cpuCount'],
                'ram': server['memorySize'] // 1024 // 1024 // 1024,
                'name': server['serverName'],
                'created': server['createDate'][:10],
                'publicip': publicip
            }
            # current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M")
            # with open(f'./ncp-{current_time}-inventory', 'a+') as f:
            #     f.write(f"{server['serverName']} {vmgestip}\n")
            inventories.append(data)
        return inventories

    def get_network(self, uri):
        headers = self.generate_hmac(uri)
        response = requests.get(f'{self.BASE_URI}/vserver/v2/{uri}?responseFormatType=json', headers=headers).json()
        networks = []
        for i in response['getNetworkInterfaceListResponse']['networkInterfaceList']:
            try:
                networks.append({'instanceNo': i['instanceNo'], 'ip': i['ip']})
            except Exception as e:
                pass
                print(f'Exception: {e}')
        return networks

    #     getBlockStorageInstanceList
    def get_blockstorage(self, uri):
        headers = self.generate_hmac(uri)
        response = requests.get(f'{self.BASE_URI}/vserver/v2/{uri}?responseFormatType=json', headers=headers).json()
        return response

    def block_filter(self):
        instances = self.get_instances('getServerInstanceList')['getServerInstanceListResponse']['serverInstanceList']
        volumes = self.get_blockstorage('getBlockStorageInstanceList')['getBlockStorageInstanceListResponse'][
            'blockStorageInstanceList']

        instance_volumes = {}

        for instance in instances:
            instance_volumes[instance["serverInstanceNo"]] = {
                "instance_name": instance["serverName"],
                "volumes": []
            }

        for volume in volumes:
            volume_type_match = re.findall(r'\b\w*\s?(HDD|SSD)\b', volume["blockStorageDiskDetailType"]['code'])
            volume_type = volume_type_match[0] if volume_type_match else "Unknown"
            instance_id = volume['serverInstanceNo']
            if instance_id in instance_volumes:
                instance_volumes[instance_id]["volumes"].append(
                    {
                        "device": volume['deviceName'],
                        "volume_type": volume_type,
                        "size": volume["blockStorageSize"] // 1024 // 1024 // 1024
                    }
                )
        return instance_volumes
