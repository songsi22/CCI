from openpyxl import load_workbook
from openpyxl.styles import Border, Side, Alignment
from datetime import datetime
import string

def data_to_excel(inventories, csp_type):
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
        ws[f'A{i + 4}'].value = inventory['availability_zone']  # zone
        ws[f'B{i + 4}'].value = inventory['name']  # name
        for volume in inventory['volumes']:
            if volume['bootable']:
                if volume['volume_type'] == 'HDD':
                    ws[f'F{i + 4}'].value = volume['size']  # HDD size
                else:
                    ws[f'G{i + 4}'].value = volume['size']  # SSD size
            else:
                if volume['volume_type'] == 'HDD':
                    ext_hdd += volume['size']
                else:
                    ext_ssd += volume['size']
        if ext_ssd == 0 and ext_hdd == 0:
            pass
        elif ext_ssd != 0:
            ws[f'J{i + 4}'].value = ext_ssd  # ext ssd
        else:
            ws[f'I{i + 4}'].value = ext_hdd  # ext ssd
        ws[f'M{i + 4}'].value = inventory['publicip']  # pub ip
        ws[f'N{i + 4}'].value = vmguestip  # pri ip ## 향후 주석 처리 예정?
        ws[f'O{i + 4}'].value = inventory['created']  # created
        ws[f'P{i + 4}'].value = inventory['vm_state']  # vm state
        for uppercase in string.ascii_uppercase[:-10]:
            ws[f'{uppercase}{i + 4}'].border = thin_border
            ws[f'{uppercase}{i + 4}'].alignment = Alignment(horizontal='center', vertical='center')
    create_time = datetime.now().strftime("%Y%m%d-%H%M")
    wb.save(f'./{csp_type}_inventory_{create_time}.xlsx')
