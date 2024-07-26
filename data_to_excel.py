from openpyxl import load_workbook

def data_to_excel(inventories):
    wb = load_workbook('./template.xlsx')
    ws = wb.active

    for i,inventory in enumerate(inventories):
        ws[f'A{i + 4}'].value = inventory['availability_zone']# zone
        # ws[f'B{i + 4}'].value = inventory['name']  # name
        for j in inventory['volumes']:
            if j['bootable']:
                if j['volume_type'] == 'HDD':
                    ws[f'F{i + 4}'].value = j['size']  # HDD size
                else:
                    ws[f'G{i + 4}'].value = j['size']  # SSD size
            else:
                if j['volume_type'] == 'HDD':
                    ws[f'I{i + 4}'].value = j['size']  # ext HDD size
                else:
                    ws[f'J{i + 4}'].value = j['size']  # ext SSD size
        ws[f'M{i + 4}'].value = inventory['publicip']# pub ip
        # ws[f'N{i + 4}'].value = inventory['privateip']# pri ip ## 향후 주석 처리 예정?
        ws[f'O{i + 4}'].value = inventory['created']# created
        ws[f'P{i + 4}'].value = inventory['vm_state'] # vm state
    wb.save('./NHNinventory.xlsx')