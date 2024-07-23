# CCI - Corea Cloud Inventory
한국 3사 CSP 사(KTC,NHN,NCP) 의 API 를 사용하여 inventory 를 만드는 프로젝트 입니다.</br>
inventory 를 만드는데 있어 API 에만 의존하지 않고 운영체제에서의 정보를 토대로 하나의 완성된 inventory 를 만들고</br>
inventory 파일을 토대로 웹 대시보드를 만들고자 합니다.</br>
LLM chat 기능을 통해 inventory 의 정보를 활용합니다.</br>

1. CSP 제공 API를 활용하여 최소 정보 수집[본 코드에서는 zone, VM 생성날짜, VM 상태, 공인IP, 사설IP 정도 수집](가장 중요한 것은 IP 정보)
2. 수집된 IP를 토대로 ansible-playbook 으로 OS 정보 수집
3. 수집된 데이터를 template 에 저장
4. streamlit 으로 template 양식을 표 형태로 화면에 출력
5. LLM(본 코드에서는 clovastudio 의 HCX-003 모델을 사용하였으나 Ollama 또는 llama3 로 대체 예정) 을 통해 표 정보를 활용
   
