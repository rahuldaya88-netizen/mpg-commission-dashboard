import pandas as pd
import os

def load_excel_sheets():
    # File ka path data folder ke andar hai
    file_path = os.path.join("data", "Historical Data.xlsx")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None
        
    try:
        # Saari sheets read karna
        excel_file = pd.ExcelFile(file_path)
        
        # Sirf wahi sheets allow karni hain jo aapne batayin hain (Hidden ya extra sheets ignore hongi)
        allowed_sheets = ["BIHAR", "Jharkhand", "West Bengal", "West Bangal", "Volume Summary", "Charts"]
        
        sheets_data = {}
        for sheet in excel_file.sheet_names:
            # Sheet name ko clean karke allowed list se match karna
            cleaned_sheet_name = sheet.strip()
            if any(cleaned_sheet_name.lower() == allowed.lower() for allowed in allowed_sheets):
                sheets_data[cleaned_sheet_name] = excel_file.parse(sheet)
                
        return sheets_data
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return None
