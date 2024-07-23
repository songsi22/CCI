import requests
import pandas as pd
import os
df = pd.read_excel('inventory.xlsx',header=None,skiprows=2,names=['zone','hostname','centos','ubuntu','rocky','redhat','cpu','mem',
                   'osdisk','exthdd','extssd','nas','swap','mp','publicip','priavteip','created','status'])


class CompletionExecutor:
    def __init__(self, host, api_key, api_key_primary_val, request_id):
        self._host = host
        self._api_key = api_key
        self._api_key_primary_val = api_key_primary_val
        self._request_id = request_id
        import pdb;pdb.set_trace()
# os.getenv()
    def execute(self, completion_request):
        headers = {
            'X-NCP-CLOVASTUDIO-API-KEY': self._api_key,
            'X-NCP-APIGW-API-KEY': self._api_key_primary_val,
            'X-NCP-CLOVASTUDIO-REQUEST-ID': self._request_id,
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'text/event-stream'
        }

        with requests.post(self._host + '/testapp/v1/chat-completions/HCX-003',
                           headers=headers, json=completion_request
                # , stream=True
        ) as r:
            for line in r.iter_lines():
                if line:
                    print(line.decode("utf-8"))


if __name__ == '__main__':
    completion_executor = CompletionExecutor(
        host='https://clovastudio.stream.ntruss.com',
        api_key=os.environ.get('X-NCP-CLOVASTUDIO-API-KEY'),
        api_key_primary_val=os.environ.get('X-NCP-APIGW-API-KEY'),
        request_id=os.environ.get('X-NCP-CLOVASTUDIO-REQUEST-ID')
    )

    preset_text = [{"role":"system","content":"pandas 의 dataframe 을 읽어서 분석해주는 전문가야\n"
                                              "Index(['zone', 'hostname', 'centos', 'ubuntu', 'rocky', 'redhat', 'cpu', 'mem', 'osdisk', 'exthdd', 'extssd', 'nas', 'swap', 'mp', 'publicip', 'priavteip', 'created', 'status'],      dtype='object')\n"
                                              " centos,ubuntu,rocky,redhat 에 적힌 숫자는 갯수가 아닌 버전 이야\n"
                                              "nan 은 계산하지 않아\n"
                                              "단답으로 답변해줘, 찾는 정보가 없다면 없다고 답변해줘"},{"role":"user","content":f'{df} centos 사용 버전 별로 갯수 알려줘'}]

    request_data = {
        'messages': preset_text,
        'topP': 0.8,
        'topK': 0,
        'maxTokens': 256,
        'temperature': 0.1,
        'repeatPenalty': 0.1,
        'stopBefore': [],
        'includeAiFilters': True,
        'seed': 0
    }

    print(preset_text)
    completion_executor.execute(request_data)