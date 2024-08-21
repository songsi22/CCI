import pandas as pd
import os


def read_template(filename, customer, userid):
    """
    엑셀 파일에서 고객사별 VM 정보를 읽어오는 함수.

    Args:
        filename (str): 읽어올 엑셀 파일의 이름.
        customer (str): 고객사명.
        userid (str): 사용자 ID.

    Returns:
        pd.DataFrame: 고객사 정보가 포함된 DataFrame.
    """
    file_path = f'files/{userid}_files/{filename}'

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    df = pd.read_excel(file_path, index_col=None, header=None, skiprows=4,
                       names=['Zone', 'HostName', 'OS', 'CPU', 'MEM',
                              'OSDISK[HDD]', 'OSDISK[SSD]', 'SWAP',
                              'EXTDISK[HDD]', 'EXTDISK[SSD]', 'NAS',
                              'Mount Point', '공인IP', '사설IP', 'VM생성날짜',
                              'VM상태'], dtype=object)
    df.insert(0, '고객사', customer)
    return df


def read_customer_file(filename, userid):
    """
    엑셀 파일에서 고객사의 호스트명과 IP 정보를 읽어오는 함수.

    Args:
        filename (str): 읽어올 엑셀 파일의 이름.
        userid (str): 사용자 ID.

    Returns:
        pd.DataFrame: 호스트명, IP, 포트, 사용자명 및 비밀번호 정보를 포함한 DataFrame.
    """
    file_path = f'files/{userid}_files/{filename}'

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    df = pd.read_excel(file_path, usecols=[1, 13], skiprows=4, index_col=None, header=None,
                       names=['hostname', 'ip'], dtype=object)

    df.insert(2, 'port', 22)
    df.insert(3, 'user', '')
    df.insert(4, 'password', '')
    return df
