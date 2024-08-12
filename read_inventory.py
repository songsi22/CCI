import pandas as pd


def read_template(filename, customer, userid):
    df = pd.read_excel(f'{userid}_files/{filename}', index_col=None, header=None, skiprows=4,
                       names=['Zone', 'HostName', 'OS', 'CPU', 'MEM',
                              'OSDISK[HDD]', 'OSDISK[SSD]', 'SWAP',
                              'EXTDISK[HDD]', 'EXTDISK[SSD]', 'NAS',
                              'Mount Point', '공인IP', '사설IP', 'VM생성날짜',
                              'VM상태'])
    df.insert(0, '고객사', customer)
    return df
