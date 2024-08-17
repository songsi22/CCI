import os
from datetime import datetime
import json
from streamlit_option_menu import option_menu

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

with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

csp_dict = {'민간NCP': 'NCP', '공공NCP': 'NCPG', '민간KTC[@D]': 'KTC', '공공KTC[@D]': 'KTCG', '민간NHN': 'NHN', '공공NHN': 'NHNG'}


def manage_inventory(session: str):
    session_username = session
    customers = os.listdir(f'{session_username}_custom')
    visible = True
    auto, manual, remote_comm = st.tabs(['자동', '수동', '명령어 수집'])
    with auto:
        if customers:
            name = st.selectbox(label='고객명', options=customers, key='auto')
            csp_type = st.radio(label='CSP 선택',
                                options=['민간NCP', '공공NCP', '민간KTC[@D]', '공공KTC[@D]', '민간NHN', '공공NHN'], horizontal=True)
            if 'NCP' in csp_dict[csp_type]:
                access_key = st.text_input('Access Key', placeholder='API access Key').strip()
                secret_key = st.text_input('Secret Key', placeholder='API secret Key', type="password").strip()
                if st.button(label='API를 통한 수집', key='ncpb'):
                    if all([name, access_key, secret_key]):
                        with st.spinner('진행 중'):
                            create_day_in_file = datetime.now().strftime("%Y%m%d")
                            create_time_in_file = datetime.now().strftime("%H%M")
                            csp = CSPFactory.get_csp(csp_type=csp_dict[csp_type], access_key=access_key,
                                                     secret_key=secret_key)
                            data_to_excel(csp.get_inventory(), csp_type=csp_dict[csp_type], customer=name,
                                          path=f'{session_username}',
                                          cday=create_day_in_file)
                            write_to_file(type='API', customer=name, csp_type=csp_dict[csp_type],
                                          path=f'{session_username}',
                                          cday=create_day_in_file, ctime=create_time_in_file)
                            st.success(f'{name} 등록 완료. 인벤토리에서 확인하세요')
                    else:
                        st.warning('모든 입력을 완료해주세요.')

            elif 'NHN' in csp_dict[csp_type]:
                tenantid = st.text_input('Tenant ID', placeholder='API endpoint tenantid').strip()
                username = st.text_input('Username', placeholder='root@mail.com').strip()
                password = st.text_input('Password', placeholder='API endpoint password', type="password").strip()
                if st.button(label='API를 통한 수집', disabled=visible, key='nhnb'):
                    if all([name, tenantid, username, password]):
                        with st.spinner('진행 중'):
                            create_day_in_file = datetime.now().strftime("%Y%m%d")
                            create_time_in_file = datetime.now().strftime("%H%M")
                            csp = CSPFactory.get_csp(csp_type=csp_dict[csp_type], tenantid=tenantid, username=username,
                                                     password=password)
                            data_to_excel(csp.get_inventory(), csp_type=csp_dict[csp_type], customer=name,
                                          path=f'{session_username}',
                                          cday=create_day_in_file)
                            write_to_file(type='API', customer=name, csp_type=csp_dict[csp_type],
                                          path=f'{session_username}',
                                          cday=create_day_in_file, ctime=create_time_in_file)
                            st.success(f'{name} 등록 완료. 인벤토리에서 확인하세요')
                    else:
                        st.warning('모든 입력을 완료해주세요.')

            elif 'KTC' in csp_dict[csp_type]:
                username = st.text_input('Username', placeholder='root@mail.com').strip()
                password = st.text_input('Password', placeholder='root\' password', type="password").strip()
                if st.button(label='API를 통한 수집', disabled=visible, key='ktcb'):
                    if all([name.stripe(), username, password]):
                        with st.spinner('진행 중'):
                            create_day_in_file = datetime.now().strftime("%Y%m%d")
                            create_time_in_file = datetime.now().strftime("%H%M")
                            csp = CSPFactory.get_csp(csp_dict[csp_type], username=username, password=password)
                            data_to_excel(csp.get_inventory(), csp_type=csp_dict[csp_type], customer=name,
                                          path=f'{session_username}',
                                          cday=create_day_in_file)
                            write_to_file(type='API', customer=name, csp_type=csp_dict[csp_type],
                                          path=f'{session_username}',
                                          cday=create_day_in_file, ctime=create_time_in_file)
                            st.success(f'{name} 등록 완료. 인벤토리에서 확인하세요')
                    else:
                        st.warning('모든 입력을 완료해주세요.')
        else:
            st.warning('등록된 고객이 없습니다.')
    with manual:
        customers = os.listdir(f'{session_username}_custom')
        if customers:
            visible = True
            name = st.selectbox(label='고객명', options=customers, key='manual')
            upload_template = st.file_uploader(label='파일 업로드', type='xlsx')
            if name and upload_template:
                visible = False
            col1, col2 = st.columns([1, 6])
            with col1:
                if st.button(label='등록', disabled=visible, key='col1'):
                    with st.spinner('진행 중'):
                        if upload_template is not None:
                            save_path = os.path.join(f"{session_username}_files", upload_template.name)
                            with open(save_path, "wb") as f:
                                f.write(upload_template.getbuffer())
                            with open(f'{session_username}_custom/{name}', 'a+', encoding='utf-8') as f:
                                create_day_in_file = datetime.now().strftime("%Y%m%d")
                                create_time_in_file = datetime.now().strftime("%H%M")
                                f.write(f'{upload_template.name},{create_day_in_file}{create_time_in_file}\n')
                            st.success(f'{name} 등록 완료. 인벤토리에서 확인하세요')
            with col2:
                with open('./template.xlsx', 'rb') as file:
                    file_data = file.read()
                st.download_button(label='템플릿 다운로드', data=file_data, file_name='template.xlsx',
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning('등록된 고객이 없습니다.')
        with remote_comm:
            customers = os.listdir(f'{session_username}_custom')
            if customers:
                name = st.selectbox(label='고객명', options=customers, key='remote_comm', index=None,
                                    placeholder='고객사를 선택해주세요')
                if name:
                    with open(f'{session_username}_custom/{name}', 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) != 0:
                            flines = lines[-1].strip()
                            filename = flines.split(',')[0]
                            df = read_customer_file(filename=filename, userid=session_username)
                            command_df = st.data_editor(df)
                            if st.button(label='추출'):
                                command_df_dict = command_df.to_dict(orient='records')
                                with open(f'{session_username}_files/{name}_remote_comm.json', 'w') as f:
                                    f.write(json.dumps(command_df_dict))
                        else:
                            st.warning('등록된 인벤토리가 없습니다.')


def manage_customer(session: str):
    session_username = session
    create, delete = st.tabs(['등록', '삭제'])
    with create:
        customer = st.text_input('고객사명', key='customer').strip()
        if customer:
            if os.path.exists(f'{session_username}_custom/{customer}'):
                st.warning(f'{customer}은 존재합니다.')
        if st.button(label='등록', key='create'):
            if not customer:  # 고객사명이 공백일 경우
                st.warning('고객사명을 입력해 주세요.')
            else:
                with st.spinner('진행 중'):
                    with open(f'{session_username}_custom/{customer}', 'w') as f:
                        pass
                    st.success(f'{customer} 고객 등록 완료')

    with delete:
        customers = os.listdir(f'{session_username}_custom')
        if customers:
            selected = st.selectbox(label='고객명', options=customers, key='delete')
            if st.button('삭제'):
                os.remove(f'{session_username}_custom/{selected}')
                st.rerun()
        else:
            st.warning('등록된 고객이 없습니다.')


def front(session: str):
    session_username = session
    if not os.path.exists(f"{st.session_state['username']}_custom"):
        os.makedirs(f"{st.session_state['username']}_custom")
    if not os.path.exists(f"{st.session_state['username']}_files"):
        os.makedirs(f"{st.session_state['username']}_files")
    customers = os.listdir(f'{session_username}_custom')
    df = None
    if customers:
        options = st.multiselect(options=customers, label='고객사 선택', default=customers, placeholder='고객사를 선택하세요.', )
        for customer in options:
            filename = None
            with open(f'{session_username}_custom/{customer}', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) != 0:
                    flines = lines[-1].strip()
                    filename = flines.split(',')[0]
                    createdtime = flines.split(',')[1]
                    createdtime = datetime.strptime(createdtime, "%Y%m%d%H%M").strftime("%Y년 %m월 %d일 %H시 %M분")
            if filename is not None and 'xlsx' in filename:
                userid = f'{session_username}'
                if len(options) == 1:
                    df = read_template(userid=userid, customer=customer, filename=filename)
                elif len(options) > 1:
                    df2 = read_template(userid=userid, customer=customer, filename=filename)
                    df = pd.concat([df, df2], axis=0, ignore_index=True)
                df.fillna('', inplace=True)
                # df = df.map(lambda x: int(x) if isinstance(x, float) else x)
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
        st.dataframe(filtered, use_container_width=True)


authenticator.login()
if st.session_state['authentication_status']:
    session_username = st.session_state['username']
    with st.sidebar:
        authenticator.logout()
        choice = option_menu("Menu", ["인벤토리", "고객사 관리", "인벤토리 관리"],
                             icons=['file-bar-graph', 'people-fill', 'files'],
                             menu_icon="app-indicator", default_index=0,
                             styles={
                                 "container": {"padding": "4!important", "background-color": "#fafafa"},
                                 "icon": {"color": "black", "font-size": "25px"},
                                 "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px",
                                              "--hover-color": "#fafafa"},
                                 "nav-link-selected": {"background-color": "#08c7b4"},
                             }
                             )
    if choice == '인벤토리':
        front(session=session_username)
    elif choice == '고객사 관리':
        manage_customer(session=session_username)
    elif choice == '인벤토리 관리':
        manage_inventory(session=session_username)
elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')
elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')
