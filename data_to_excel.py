from openpyxl import load_workbook
from openpyxl.styles import Border, Side, Alignment
from datetime import datetime
import string


def data_to_excel(inventories, csp_type, path, cday, customer=''):
    thin_border = Border(left=Side(style='thin'),
                         right=Side(style='thin'),
                         top=Side(style='thin'),
                         bottom=Side(style='thin'))
    wb = load_workbook('./template.xlsx')
    ws = wb.active
    for i, inventory in enumerate(inventories):
        ext_ssd = 0
        ext_hdd = 0
        vmguestip = next(iter(inventory))
        inventory = inventory[vmguestip]
        create_time_in_excel = datetime.now().strftime("%Y년%m월%d일")
        ws['A1'].value = customer
        ws['O1'].value = create_time_in_excel
        ws[f'A{i + 5}'].value = inventory['availability_zone']  # zone
        ws[f'B{i + 5}'].value = inventory['name']  # name
        ws[f'D{i + 5}'].value = inventory['vcpus']  # vcpu
        ws[f'E{i + 5}'].value = inventory['ram']  # ram
        for volume in inventory['volumes']:
            if volume['bootable']:
                if volume['volume_type'] == 'HDD':
                    ws[f'F{i + 5}'].value = volume['size']  # HDD size
                else:
                    ws[f'G{i + 5}'].value = volume['size']  # SSD size
            else:
                if volume['volume_type'] == 'HDD':
                    ext_hdd += volume['size']
                else:
                    ext_ssd += volume['size']
        if ext_ssd == 0 and ext_hdd == 0:
            pass
        elif ext_ssd != 0:
            ws[f'J{i + 5}'].value = ext_ssd  # ext SSD total(sum) size
        else:
            ws[f'I{i + 5}'].value = ext_hdd  # ext HDD total(sum) size
        ws[f'M{i + 5}'].value = inventory['publicip']  # pub ip
        ws[f'N{i + 5}'].value = vmguestip  # pri ip
        ws[f'O{i + 5}'].value = inventory['created']  # created
        ws[f'P{i + 5}'].value = inventory['vm_state']  # vm state
        for uppercase in string.ascii_uppercase[:-10]:
            ws[f'{uppercase}{i + 5}'].border = thin_border
            ws[f'{uppercase}{i + 5}'].alignment = Alignment(horizontal='center', vertical='center')
    wb.save(f'./{path}_files/{customer}{csp_type}_inventory_{cday}.xlsx')


def write_to_file(type, csp_type, customer, path, cday, ctime, filename=''):
    if type == 'API':
        with open(f'{path}_custom/{customer}', 'a+', encoding='utf-8') as f:
            f.write(f'{customer}-{csp_type}_inventory_{cday}.xlsx,{cday}{ctime}\n')
    else:
        with open(f'{path}_custom/{customer}', 'a+', encoding='utf-8') as f:
            f.write(f'{filename},{cday}{ctime}\n')
