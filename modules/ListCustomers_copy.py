import pandas as pd
# Đọc Excel
df_customerAll = pd.read_excel('/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/file/CRM_Account.xlsx', engine='openpyxl')

# Chuyển thành list of dicts
list_customerNPP = df_customerAll.to_dict(orient='records')