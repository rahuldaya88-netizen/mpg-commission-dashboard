import os
import glob
import pandas as pd
from sqlalchemy import create_engine, text
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

DB_FILE = "app_database.db"
engine = create_engine(f"sqlite:///{DB_FILE}")

def process_and_save_df(combined_df):
    """Excel Dataframe ko clean karke SQL me daalta hai."""
    combined_df.columns = [str(col).strip() for col in combined_df.columns]
    combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
    
    # Existing FY Column Check
    fy_col = None
    for col in combined_df.columns:
        if 'fy' in col.lower() or 'financial' in col.lower() or 'year' in col.lower():
            fy_col = col
            break
            
    if fy_col:
        combined_df['Financial_Year'] = combined_df[fy_col].astype(str).str.strip()
    else:
        combined_df['Financial_Year'] = 'FY 2026-27'

    if 'Status' not in combined_df.columns:
        combined_df['Status'] = 'Pending'
    else:
        combined_df['Status'] = combined_df['Status'].fillna('Pending')
        
    combined_df.to_sql("payments", engine, if_exists="replace", index=True, index_label="id")
    return True

def get_data_from_sql(fy_filter=None):
    try:
        if fy_filter and fy_filter != "All":
            query = f"SELECT * FROM payments WHERE Financial_Year = '{fy_filter}'"
        else:
            query = "SELECT * FROM payments"
        return pd.read_sql(query, engine)
    except Exception:
        return pd.DataFrame()

def update_payment_status(row_id, new_status):
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE payments SET Status = :status WHERE id = :id"),
            {"status": new_status, "id": row_id}
        )

def generate_pdf_statement(data_row):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, "====================================")
    p.drawString(100, 735, "    PAYMENT STATEMENT / RECEIPT    ")
    p.drawString(100, 720, "====================================")
    
    y = 680
    for key, value in data_row.items():
        if y < 50:
            p.showPage()
            y = 750
        p.drawString(100, y, f"{key}: {value}")
        y -= 20
        
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

st.set_page_config(page_title="Payment Dashboard", layout="wide")
st.title("📊 Excel to SQL & Payment Management System")

# Sidebar - Direct File Upload & Control
st.sidebar.header("📁 Upload Excel File")
uploaded_files = st.sidebar.file_uploader("Apni Excel File Yahan Upload Karein", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    all_data = [pd.read_excel(file) for file in uploaded_files]
    combined_df = pd.concat(all_data, ignore_index=True)
    if process_and_save_df(combined_df):
        st.sidebar.success("✅ File Successfully Loaded!")

# Data Fetching
all_df = get_data_from_sql()

if not all_df.empty and 'Financial_Year' in all_df.columns:
    fy_options = ["All"] + sorted(all_df['Financial_Year'].dropna().unique().tolist())
    selected_fy = st.sidebar.selectbox("📅 Select Financial Year (FY):", fy_options)
else:
    selected_fy = "All"

df = get_data_from_sql(selected_fy)

if not df.empty:
    st.subheader(f"📋 Payment Records ({selected_fy})")
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("⚙️ Actions & Operations (Search & Update by ID)")

    # ID Selection / Search Dropdown
    selected_id = st.selectbox("🔍 Select or Search ID:", df['id'].tolist())
    
    # Correct filtering using selected_id
    selected_row = df[df['id'] == selected_id].iloc[0].to_dict()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 1. Print Statement")
        pdf_file = generate_pdf_statement(selected_row)
        st.download_button(
            label="📄 Download Statement (PDF)",
            data=pdf_file,
            file_name=f"statement_{selected_id}.pdf",
            mime="application/pdf"
        )

    with col2:
        st.markdown("### 2. Payment Control")
        current_status = selected_row.get('Status', 'Pending')
        st.info(f"Current Status for ID {selected_id}: **{current_status}**")
        
        if current_status == 'Hold':
            if st.button("🔓 Release Payment"):
                update_payment_status(selected_id, "Released")
                st.success(f"Payment for ID {selected_id} Release ho gaya!")
                st.rerun()
        else:
            if st.button("🔒 Hold Payment"):
                update_payment_status(selected_id, "Hold")
                st.warning(f"Payment for ID {selected_id} Hold ho gaya!")
                st.rerun()
else:
    st.warning("👈 Left sidebar me **Upload Excel File** par click karke apni Excel file choose karein!")
