import gspread
import pandas as pd


gc = gspread.service_account(filename='client_secret.json')

spreadsheet_id = '11mnygQWtGF2ZRF4000tpST0rKrftqpjBOojSaNjunss'
worksheet_name = 'TASK SCHEDULED'

spreadsheet = gc.open_by_key(spreadsheet_id)

worksheet = spreadsheet.worksheet(worksheet_name)

data_from_sheets = worksheet.get_all_values()

df = pd.DataFrame(data_from_sheets[1:], columns=data_from_sheets[0])


print(df)
