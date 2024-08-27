import os
from datetime import datetime
import json
from streamlit_option_menu import option_menu
from st_aggrid import AgGrid, GridOptionsBuilder
from csp_factory import CSPFactory
import streamlit as st
import pandas as pd
from st_keyup import st_keyup
from data_to_excel import data_to_excel, write_to_file
from read_inventory import read_template, read_customer_file
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

st.set_page_config(layout="wide", page_title='Inventory')


def load_config():
    with open('./config.yaml') as file:
        return yaml.load(file, Loader=SafeLoader)


config = load_config()
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

csp_dict = {'민간NCP[VPC]': 'NCP', '공공NCP[VPC]': 'NCPG',
            '민간KTC[@D]': 'KTC', '공공KTC[@D]': 'KTCG',
            '민간NHN': 'NHN', '공공NHN': 'NHNG'
            }


def get_current_datetime():
    """
    현재 날짜와 시간을 반환하는 함수.

    Returns:
        tuple: 현재 날짜(YYYYMMDD)와 시간(HHMM) 문자열의 튜플.
    """
    now = datetime.now()
    return now.strftime("%Y%m%d"), now.strftime("%H%M")


def handle_inventory_save(csp, csp_type, customer, session_username):
    """
    수집된 인벤토리 데이터를 엑셀 파일로 저장하고 기록 파일에 정보를 기록하는 함수.

    Args:
        csp: CSP 객체.
        csp_type (str): CSP 유형.
        customer (str): 고객명.
        session_username (str): 현재 세션의 사용자 이름.
    """
    create_day_in_file, create_time_in_file = get_current_datetime()
    data_to_excel(csp.get_inventory(), csp_type=csp_type, customer=customer,
                  path=f'{session_username}', cday=create_day_in_file)
    write_to_file(type='API', customer=customer, csp_type=csp_type,
                  path=f'{session_username}', cday=create_day_in_file, ctime=create_time_in_file)
    st.success(f'{customer} 등록 완료. 인벤토리에서 확인하세요')


def manage_inventory(session: str):
    """
        고객 인벤토리를 관리하는 함수.

        사용자는 고객을 선택하고 CSP 유형에 따라 API 키 또는 사용자 정보를 입력하여
        인벤토리를 수집할 수 있습니다. 수집된 데이터는 엑셀 파일로 저장되고,
        기록 파일에도 해당 정보가 기록됩니다.

        Args:
            session (str): 현재 세션의 사용자 이름.
        """
    session_username = session
    customers = os.listdir(f'files/{session_username}_custom')
    auto, manual, remote_comm = st.tabs(['자동', '수동', '명령어 수집'])
    with auto:
        if customers:
            name = st.selectbox(label='고객명', options=customers, key='auto')
            csp_type = st.radio(label='CSP 선택',
                                options=['민간NCP[VPC]', '공공NCP[VPC]', '민간KTC[@D]', '공공KTC[@D]', '민간NHN', '공공NHN'],
                                horizontal=True)
            if 'NCP' in csp_dict[csp_type]:
                access_key = st.text_input('Access Key', placeholder='API access Key').strip()
                secret_key = st.text_input('Secret Key', placeholder='API secret Key', type="password").strip()
                if st.button(label='API를 통한 수집', key='ncpb'):
                    if all([name, access_key, secret_key]):
                        with st.spinner('진행 중'):
                            csp = CSPFactory.get_csp(csp_type=csp_dict[csp_type], access_key=access_key,
                                                     secret_key=secret_key)
                            handle_inventory_save(csp, csp_dict[csp_type], name, session_username)
                    else:
                        st.warning('모든 입력을 완료해주세요.')

            elif 'NHN' in csp_dict[csp_type]:
                if 'G' not in csp_dict[csp_type]:
                    zones = ['kr1', 'kr2', 'jp1']
                    zone = st.radio(label='Zone', options=zones, key='nhnzone', horizontal=True)
                else:
                    zones = ['kr1', 'kr2']
                    zone = st.radio(label='Zone', options=zones, key='nhnzone', horizontal=True)
                tenantid = st.text_input('Tenant ID', placeholder='API endpoint tenantid').strip()
                username = st.text_input('Username', placeholder='root@mail.com').strip()
                password = st.text_input('Password', placeholder='API endpoint password', type="password").strip()
                if st.button(label='API를 통한 수집', key='nhnb'):
                    if all([name, tenantid, username, password]):
                        with st.spinner('진행 중'):
                            csp = CSPFactory.get_csp(csp_type=csp_dict[csp_type], tenantid=tenantid, username=username,
                                                     password=password, zone=zone)
                            handle_inventory_save(csp, csp_dict[csp_type], name, session_username)
                    else:
                        st.warning('모든 입력을 완료해주세요.')

            elif 'KTC' in csp_dict[csp_type]:
                zone = None
                if 'G' not in csp_dict[csp_type]:
                    zones = ['d1', 'd2', 'd3']
                    zone = st.radio(label='Zone', options=zones, key='ktczone', horizontal=True)
                username = st.text_input('Username', placeholder='root@mail.com').strip()
                password = st.text_input('Password', placeholder='root\'s password', type="password").strip()
                if st.button(label='API를 통한 수집', key='ktcb'):
                    if all([name, username, password]):
                        with st.spinner('진행 중'):
                            if zone:
                                csp = CSPFactory.get_csp(csp_dict[csp_type], username=username, password=password,
                                                         zone=zone)
                            else:
                                csp = CSPFactory.get_csp(csp_dict[csp_type], username=username, password=password)
                            handle_inventory_save(csp, csp_dict[csp_type], name, session_username)
                    else:
                        st.warning('모든 입력을 완료해주세요.')


        else:
            st.warning('등록된 고객이 없습니다.')
    with manual:
        if customers:
            name = st.selectbox(label='고객명', options=customers, key='manual')
            col1, col2 = st.columns([1, 6])
            with col1:
                with open('files/template.xlsx', 'rb') as file:
                    file_data = file.read()
                st.download_button(label='템플릿 다운로드', data=file_data, file_name='files/template.xlsx',
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with col2:
                upload_template = st.file_uploader(label='파일 업로드', type='xlsx')
            if st.button(label='등록', key='col1'):
                if all([name, upload_template]):
                    with st.spinner('진행 중'):
                        save_path = os.path.join(f"files/{session_username}_files", upload_template.name)
                        with open(save_path, "wb") as f:
                            f.write(upload_template.getbuffer())
                        with open(f'files/{session_username}_custom/{name}', 'a+', encoding='utf-8') as f:
                            create_day_in_file, create_time_in_file = get_current_datetime()
                            f.write(f'{upload_template.name},{create_day_in_file}{create_time_in_file}\n')
                        st.success(f'{name} 등록 완료. 인벤토리에서 확인하세요')
                else:
                    st.warning('파일을 업로드 해주세요.')
        else:
            st.warning('등록된 고객이 없습니다.')
    with remote_comm:
        if customers:
            name = st.selectbox(label='고객명', options=customers, key='remote_comm', index=None,
                                placeholder='고객사를 선택해주세요')
            if name:
                try:
                    with open(f'files/{session_username}_custom/{name}', 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) != 0:
                            flines = lines[-1].strip()
                            filename = flines.split(',')[0]
                            df = read_customer_file(filename=filename, userid=session_username)
                            command_df = st.data_editor(df)
                            if st.button(label='추출'):
                                with st.spinner('진행 중'):
                                    command_df_dict = command_df[
                                        (command_df['user'] != '') & (command_df['password'] != '')].to_dict(
                                        orient='records')
                                    command_df_dict.append({'filename': filename})
                                    command_df_dict.append({'user': session_username})
                                    with open(f'files/{session_username}_files/{name}_remote_comm.json', 'w') as f:
                                        f.write(json.dumps(command_df_dict))
                                    st.success('추출 완료')
                                    with open(f'files/{session_username}_files/{name}_remote_comm.json', 'r') as file:
                                        file_data = file.read()
                                    st.download_button(label='추출파일 다운로드', data=file_data, file_name='remote_comm.json',
                                                       mime="application/json")
                            with open('files/inventory_remote.exe', "rb") as f:
                                binary_file = f.read()
                            st.download_button(label="실행기", data=binary_file, file_name="inventory_remote.exe",
                                               mime="application/octet-stream")
                        else:
                            st.warning('등록된 인벤토리가 없습니다.')
                except Exception as e:
                    st.error(f'오류 발생: {str(e)}')
        else:
            st.warning('등록된 고객이 없습니다.')


def manage_customer(session: str):
    """
    고객 관리 기능을 제공하는 함수.

    사용자는 새로운 고객을 등록하거나 기존 고객을 삭제할 수 있습니다.
    고객 목록은 세션 사용자에 따라 관리됩니다.

    Args:
        session (str): 현재 세션의 사용자 이름.
    """
    session_username = session
    create, delete = st.tabs(['등록', '삭제'])
    with create:
        customer = st.text_input('고객사명', key='customer').strip()
        if customer and os.path.exists(f'files/{session_username}_custom/{customer}'):
            st.warning(f'{customer}은 존재합니다.')
        if st.button(label='등록', key='create'):
            if not customer:  # 고객사명이 공백일 경우
                st.warning('고객사명을 입력해 주세요.')
            else:
                try:
                    with st.spinner('진행 중'):
                        with open(f'files/{session_username}_custom/{customer}', 'w') as f:
                            pass
                        st.success(f'{customer} 고객 등록 완료')
                except Exception as e:
                    st.error(f'오류 발생: {str(e)}')

    with delete:
        customers = os.listdir(f'files/{session_username}_custom')
        if customers:
            selected = st.selectbox(label='고객명', options=customers, key='delete')
            if st.button('삭제'):
                try:
                    os.remove(f'files/{session_username}_custom/{selected}')
                    st.rerun()
                except Exception as e:
                    st.error(f'오류 발생: {str(e)}')
        else:
            st.warning('등록된 고객이 없습니다.')


def front(session: str):
    """
    고객의 인벤토리를 보여주는 함수.

    사용자는 고객사를 선택하고, 선택된 고객사의 인벤토리 데이터를 필터링하여
    화면에 표시할 수 있습니다.

    Args:
        session (str): 현재 세션의 사용자 이름.
    """
    session_username = session

    try:
        if not os.path.exists(f"files/{session_username}_custom"):
            os.makedirs(f"files/{session_username}_custom")
        if not os.path.exists(f"files/{session_username}_files"):
            os.makedirs(f"files/{session_username}_files")
    except Exception as e:
        st.error(f'디렉토리 생성 중 오류 발생: {str(e)}')
        return

    customers = os.listdir(f'files/{session_username}_custom')
    df = None
    if customers:
        options = st.multiselect(options=customers, label='고객사 선택', default=customers, placeholder='고객사를 선택하세요.', )
        for customer in options:
            filename = None
            try:
                with open(f'files/{session_username}_custom/{customer}', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) != 0:
                        flines = lines[-1].strip()
                        filename = flines.split(',')[0]
            except Exception as e:
                st.error(f'파일 읽기 중 오류 발생: {str(e)}')
                continue

            if filename is not None and 'xlsx' in filename:
                userid = f'{session_username}'
                try:
                    if len(options) == 1:
                        df = read_template(userid=userid, customer=customer, filename=filename)
                    elif len(options) > 1:
                        df2 = read_template(userid=userid, customer=customer, filename=filename)
                        df = pd.concat([df, df2], axis=0, ignore_index=True)
                except Exception as e:
                    st.error(f'데이터 처리 중 오류 발생: {str(e)}')
            else:
                st.warning(f'{customer}은 현재 인벤토리가 없습니다. 인벤토리 관리를 통해 등록하세요')
    else:
        st.warning(f'등록된 고객사가 없습니다. 고객사 관리에서 고객을 등록 하고 인벤토리를 등록하세요.')

    if df is not None:
        filter_df = df
        keyword = st_keyup('고객사, 호스트명, IP로 찾아보세요', debounce=500)
        if keyword:
            filtered = filter_df[
                filter_df.사설IP.str.lower().str.contains(keyword.lower(), na=False) |
                filter_df.공인IP.str.lower().str.contains(keyword.lower(), na=False) |
                filter_df.고객사.str.lower().str.contains(keyword.lower(), na=False) |
                filter_df.HostName.str.lower().str.contains(keyword.lower(), na=False)
                ]
        else:
            filtered = filter_df
        filtered.reset_index(inplace=True)
        gb = GridOptionsBuilder.from_dataframe(filtered)
        gb.configure_default_column(wrapText=True, autoHeight=True, autoWidth=True,
                                    cellStyle={'whiteSpace': 'pre-wrap',  # 개행 처리
                                               'lineHeight': '20px',  # 줄 간격 설정
                                               'textAlign': 'center',  # 텍스트 가운데 정렬
                                               'justifyContent': 'center'  # 셀 내용 가운데 정렬
                                               })
        gbb = gb.build()
        AgGrid(filtered, gridOptions=gbb, allow_unsafe_jscode=True, height=600)


authenticator.login()
if st.session_state['authentication_status']:
    session_username = st.session_state['username']
    with st.sidebar:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f'사용자: {session_username}')
        with col2:
            authenticator.logout()
        if 'menu_choice' not in st.session_state:
            st.session_state['menu_choice'] = "인벤토리"  # 기본 메뉴 선택

        # Option menu 선택
        st.session_state['menu_choice'] = option_menu("메뉴",
                                                      ["인벤토리", "고객사 관리", "인벤토리 관리"],
                                                      icons=['file-bar-graph', 'people-fill', 'files'],
                                                      menu_icon="app-indicator",
                                                      default_index=0,
                                                      styles={
                                                          "container": {"padding": "5!important",
                                                                        "background-color": "#fafafa"},
                                                          "icon": {"color": "black", "font-size": "20px"},
                                                          "nav-link": {"font-size": "14px", "text-align": "left",
                                                                       "margin": "0px",
                                                                       "--hover-color": "#eeeeee"},
                                                          "nav-link-selected": {"background-color": "#08c7b4"},
                                                      }
                                                      )

    # 선택된 메뉴에 따른 화면 표시
    if st.session_state['menu_choice'] == '인벤토리':
        front(session=session_username)
    elif st.session_state['menu_choice'] == '고객사 관리':
        manage_customer(session=session_username)
    elif st.session_state['menu_choice'] == '인벤토리 관리':
        manage_inventory(session=session_username)

elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')
elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')
