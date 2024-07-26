from openpyxl import load_workbook

def data_to_excel(inventories):
    wb = load_workbook('./template.xlsx')
    ws = wb.active

    for i,inventory in  enumerate(inventories):
        ws[f'A{i+3}'].value = inventory['availability_zone']# zone
        ws[f'B{i + 3}'].value = inventory['name']  # name
        ws[f'L{i+3}'].value = inventory['publicip']# pub ip
        ws[f'M{i+3}'].value = inventory['privateip']# pri ip ## 향후 주석 처리 예정?
        ws[f'N{i+3}'].value = inventory['created']# created
        ws[f'O{i+3}'].value = inventory['vm_state'] # vm state
    wb.save('./inventory.xlsx')