import os
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(page_title="MPG Commission Dashboard - Original Files", layout="wide")

st.title("📊 MPG Payment (Original Files View)")


@st.cache_data(ttl=600)
def load_original_files():
    # Folder jya tamari original Excel files padi che
    potential_folders = [
        "Farmer Payment",
        "data/Farmer Payment",
        ".",
    ]

    folders = [f for f in potential_folders if os.path.exists(f)]
    all_files_data = {}
    debug_info = []

    if not folders:
        debug_info.append("❌ 'Farmer Payment' folder malyo nathi!")
        return all_files_data, debug_info

    for folder in folders:
        debug_info.append(f"✅ Folder malyu: {folder}")
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith((".xlsx", ".xlsb", ".xls")) and not file.startswith("~$"):
                    file_path = os.path.join(root, file)
                    try:
                        engine = "pyxlsb" if file.lower().endswith(".xlsb") else "openpyxl"
                        
                        # Badhi sheets read karo or default first sheet
                        xls = pd.ExcelFile(file_path, engine=engine)
                        sheet_names = xls.sheet_names
                        
                        # Ek dictionary ma file na naam sathe badhi sheets store karo
                        for sheet in sheet_names:
                            df = pd.read_excel(xls, sheet_name=sheet, header=0)
                            key_name = f"{file} ---> [{sheet}]"
                            all_files_data[key_name] = df
                        
                        debug_info.append(f"📁 File load thai: {file} (Sheets: {sheet_names})")
                    except Exception as e:
                        debug_info.append(f"⚠️ Error reading {file}: {str(e)}")

    return all_files_data, debug_info


# Data load karo
files_data, debug_info = load_original_files()

with st.expander("🔍 File Loading Status"):
    for info in debug_info:
        st.write(info)

if files_data:
    st.sidebar.header("📂 Select File & Sheet")
    selected_file_sheet = st.sidebar.selectbox("Choose File/Sheet to View", list(files_data.keys()))

    if selected_file_sheet:
        df_selected = files_data[selected_file_sheet]
        
        # Original columns and rows as it is display karva
        st.subheader(f"📄 Viewing: {selected_file_sheet}")
        st.write(f"Total Rows: {len(df_selected):,} | Total Columns: {len(df_selected.columns)}")
        
        # Raw data table
        st.dataframe(df_selected, use_container_width=True)
        
        # Download button original file view mate
        csv = df_selected.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download this Sheet as CSV",
            data=csv,
            file_name=f"{selected_file_sheet.replace(' ', '_').replace('--->', '_')}.csv",
            mime="text/csv",
        )
else:
    st.warning("⚠️ Koi pan Excel file madi nathi. Kripya check karo ke 'Farmer Payment' folder GitHub par properly upload thayu che ke nahi.")
