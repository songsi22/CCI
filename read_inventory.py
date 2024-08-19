import pandas as pd


def read_template(filename, customer, userid):
    df = pd.read_excel(f'files/{userid}_files/{filename}', index_col=None, header=None, skiprows=4,
                       names=['Zone', 'HostName', 'OS', 'CPU', 'MEM',
                              'OSDISK[HDD]', 'OSDISK[SSD]', 'SWAP',
                              'EXTDISK[HDD]', 'EXTDISK[SSD]', 'NAS',
                              'Mount Point', '공인IP', '사설IP', 'VM생성날짜',
                              'VM상태'])
    df.insert(0, '고객사', customer)
    return df


def read_customer_file(filename, userid):
    df = pd.read_excel(f'files/{userid}_files/{filename}', usecols=[1, 13], skiprows=4, index_col=None, header=None,
                       names=['hostname', 'ip'])
    df.insert(2, 'port', 22)
    df.insert(3, 'user', '')
    df.insert(4, 'password', '')
    return df
