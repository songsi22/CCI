import os
from datetime import datetime
from csp_factory import CSPFactory
import streamlit as st
import pandas as pd
from st_keyup import st_keyup
from data_to_excel import data_to_excel, write_to_file
from read_inventory import read_template
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

st.set_page_config(layout="wide")

with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)


def front():
    csp_dict = {'민간NCP': 'NCP', '공공NCP': 'NCPG', '민간KTC[@D]': 'KTC', '공공KTC[@D]': 'KTCG', '민간NHN': 'NHN',
                '공공NHN': 'NHNG'}
    if not os.path.exists(f"{st.session_state['username']}_custom"):
        os.makedirs(f"{st.session_state['username']}_custom")
    if not os.path.exists(f"{st.session_state['username']}_files"):
        os.makedirs(f"{st.session_state['username']}_files")
    with st.expander("고객사 등록"):
        visible = True
        auto, manual = st.tabs(['자동', '수동'])
        with auto:
            name = st.text_input('고객사명')
            csp_type = st.radio(label='CSP 선택', options=['민간NCP', '공공NCP', '민간KTC[@D]', '공공KTC[@D]', '민간NHN', '공공NHN'])
            st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
            if 'NCP' in csp_dict[csp_type]:
                access_key = st.text_input('Access Key', placeholder='API access Key')
                secret_key = st.text_input('Secret Key', placeholder='API secret Key', type="password")
                if name != '' and access_key != '' and secret_key != '':
                    visible = False
                if st.button(label='등록 및 API 실행', disabled=visible):
                    with st.spinner('진행 중'):
                        create_day_in_file = datetime.now().strftime("%Y%m%d")
                        create_time_in_file = datetime.now().strftime("%H%M")
                        csp = CSPFactory.get_csp(csp_type=csp_dict[csp_type], access_key=access_key,
                                                 secret_key=secret_key)
                        data_to_excel(csp.get_inventory(), csp_type=csp_dict[csp_type], customer=name,
                                      path=st.session_state['username'],
                                      cday=create_day_in_file)
                        write_to_file(type='API', customer=name, csp_type=csp_dict[csp_type],
                                      path=f'{st.session_state['username']}',
                                      cday=create_day_in_file, ctime=create_time_in_file)
                        st.rerun()
            elif 'NHN' in csp_dict[csp_type]:
                tenantid = st.text_input('Tenant ID', placeholder='API endpoint tenantid')
                username = st.text_input('Username', placeholder='root@mail.com')
                password = st.text_input('Password', placeholder='API endpoint password', type="password")
                if name != '' and username != '' and password != '' and tenantid != '':
                    visible = False
                if st.button(label='등록 및 API 실행', disabled=visible):
                    with st.spinner('진행 중'):
                        create_day_in_file = datetime.now().strftime("%Y%m%d")
                        create_time_in_file = datetime.now().strftime("%H%M")
                        csp = CSPFactory.get_csp(csp_type=csp_dict[csp_type], tenantid=tenantid, username=username,
                                                 password=password)
                        data_to_excel(csp.get_inventory(), csp_type=csp_dict[csp_type], customer=name,
                                      path=st.session_state['username'],
                                      cday=create_day_in_file)
                        write_to_file(type='API', customer=name, csp_type=csp_dict[csp_type],
                                      path=f'{st.session_state['username']}',
                                      cday=create_day_in_file, ctime=create_time_in_file)
                        st.rerun()
            elif 'KTC' in csp_dict[csp_type]:
                username = st.text_input('Username', placeholder='root@mail.com')
                password = st.text_input('Password', placeholder='root\' password', type="password")
                if name != '' and username != '' and password != '':
                    visible = False
                if st.button(label='등록 및 API 실행', disabled=visible):
                    with st.spinner('진행 중'):
                        create_day_in_file = datetime.now().strftime("%Y%m%d")
                        create_time_in_file = datetime.now().strftime("%H%M")
                        csp = CSPFactory.get_csp(csp_dict[csp_type], username=username, password=password)
                        data_to_excel(csp.get_inventory(), csp_type=csp_dict[csp_type], customer=name,
                                      path=st.session_state['username'],
                                      cday=create_day_in_file)
                        write_to_file(type='API', customer=name, csp_type=csp_dict[csp_type],
                                      path=f'{st.session_state['username']}',
                                      cday=create_day_in_file, ctime=create_time_in_file)
                        st.rerun()
        with manual:
            with open('./template.xlsx', 'rb') as file:
                file_data = file.read()
            st.download_button(label='템플릿 다운로드', data=file_data, file_name='template.xlsx',
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            upload_template = st.file_uploader(label='파일 업로드', type='xlsx')
            if st.button(label='등록'):
                with st.spinner('진행 중'):
                    if upload_template is not None:
                        save_path = os.path.join(f"{st.session_state['username']}_files", upload_template.name)
                        with open(save_path, "wb") as f:
                            f.write(upload_template.getbuffer())
                        with open(f'{st.session_state['username']}_custom/한국환경산업기술원', 'a+', encoding='utf-8') as f:
                            create_day_in_file = datetime.now().strftime("%Y%m%d")
                            create_time_in_file = datetime.now().strftime("%H%M")
                            f.write(f'{upload_template.name},{create_day_in_file}{create_time_in_file}\n')
                        st.rerun()

    customers = os.listdir(f'{st.session_state['username']}_custom')

    options = st.multiselect(options=customers, label='고객사 선택', default=customers, placeholder='고객사를 선택하세요.', )
    filename = None
    df = None
    for customer in options:
        filename = None
        with open(f'{st.session_state['username']}_custom/{customer}', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) != 0:
                flines = lines[-1].strip()
                filename = flines.split(',')[0]
                createdtime = flines.split(',')[1]
                createdtime = datetime.strptime(createdtime, "%Y%m%d%H%M").strftime("%Y년 %m월 %d일 %H시 %M분")
        if filename is not None and 'xlsx' in filename:
            userid = f'{st.session_state['username']}'
            if len(options) == 1:
                df = read_template(userid=userid, customer=customer, filename=filename)
            elif len(options) > 1:
                df2 = read_template(userid=userid, customer=customer, filename=filename)
                df = pd.concat([df, df2], axis=0, ignore_index=True)
            df.fillna('', inplace=True)
            df = df.map(lambda x: int(x) if isinstance(x, float) else x)
        else:
            st.write(f'{customer}는 현재 인벤토리가 없습니다. 실행시키시겠습니까?')

    if df is not None:
        filter_df = df
        keyword = st_keyup('고객사, 호스트명, IP로 찾아보세요', debounce=500)
        if keyword:
            filtered = filter_df[filter_df.사설IP.str.lower().str.contains(keyword.lower(), na=False) |
                                 filter_df.공인IP.str.lower().str.contains(keyword.lower(), na=False) |
                                 filter_df.고객사.str.lower().str.contains(keyword.lower(), na=False) |
                                 filter_df.HostName.str.lower().str.contains(keyword.lower(), na=False)
                                 ]
        else:
            filtered = filter_df
        st.dataframe(filtered, use_container_width=True)


authenticator.login()
if st.session_state['authentication_status']:
    authenticator.logout()
    front()
elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')
elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')
