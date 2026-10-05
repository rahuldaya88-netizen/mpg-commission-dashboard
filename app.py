import streamlit as st
import pandas as pd
from loader import load_excel_sheets
from calculator import get_year_wise_growth_summary

# Streamlit page layout configuration
st.set_page_config(
    page_title="MPG Commission - Live Dashboard",
    page_icon="🥛",
    layout="wide"
)

st.title("🥛 MPG Commission & Milk Procurement Live Dashboard")
st.markdown("Yeh dashboard aapke PC ke Excel data se **real-time synchronized** hai.")

# Data load karne ka function
@st.cache_data(ttl=10)
def fetch_data():
    return load_excel_sheets()

excel_data = fetch_data()

if excel_data is not None:
    st.sidebar.header("📍 Region / Sheet Selection")
    
    # Session state initialization
    if 'nav_selection' not in st.session_state:
        st.session_state.nav_selection = "Summary"

    # "Summary" button navigation
    if st.sidebar.button("📊 Summary", use_container_width=True):
        st.session_state.nav_selection = "Summary"
        
    st.sidebar.markdown("---")
    
    # Sheet names list me 'Summary' option add kar rahe hain
    sheet_names = list(excel_data.keys())
    dropdown_options = ["Summary"] + sheet_names
    
    # Safe index finding for selectbox
    current_index = 0
    if st.session_state.nav_selection in dropdown_options:
        current_index = dropdown_options.index(st.session_state.nav_selection)

    # Dropdown for regions / sheets
    selected_sheet = st.sidebar.selectbox("Choose Sheet", dropdown_options, index=current_index)
    
    # Update session state if dropdown changes
    st.session_state.nav_selection = selected_sheet
    
    if selected_sheet == "Summary":
        st.subheader("📈 Year-by-Year Volume Growth & Trends (BR, WB, JH)")
        st.markdown("Yeh table aur chart aapko batayegi ki kis saal (FY) mein kitna Volume tha aur performance kaisi rahi.")
        
        # Function call karke table mangwana
        growth_df = get_year_wise_growth_summary(excel_data)
        
        if not growth_df.empty:
            # 1. Summary Table dikhana
            st.dataframe(growth_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("📊 Visual Growth Chart (Vol Kg/day)")
            
            # 2. Chart ke liye saare saal wale columns filter karna
            chart_cols = [col for col in growth_df.columns if 'Growth' not in str(col) and col != 'State']
            if chart_cols:
                chart_data = growth_df.set_index('State')[chart_cols].T
                
                # Streamlit ka clean bar chart
                st.bar_chart(chart_data)
        else:
            st.warning("Year-wise data load karne mein kuch samasya aayi.")

    elif selected_sheet == "Volume Summary":
        df = excel_data[selected_sheet]
        st.subheader("📊 Volume Summary - Data Structure & Annexures")
        
        ann_tab1, annex_tab2, annex_tab3 = st.tabs(["Annexure 1 (State Growth)", "Annexure 2 (Key Metrics)", "Annexure 3 (Plant & Plan)"])
        
        with ann_tab1:
            st.markdown("### Annexure-1: State-wise Year Growth Summary")
            try:
                ann1_df = df.iloc[2:11, 1:7].copy()
                ann1_df.columns = ['Year', 'BR', 'WB', 'JH', 'Total', 'GOLY']
                ann1_df = ann1_df.reset_index(drop=True).dropna(how='all')
                
                if 'GOLY' in ann1_df.columns:
                    ann1_df['GOLY'] = pd.to_numeric(ann1_df['GOLY'], errors='coerce')
                    ann1_df['GOLY'] = (ann1_df['GOLY'] * 100).round(0).astype(str).str.replace('.0', '', regex=False) + '%'
                    
                st.dataframe(ann1_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading Annexure 1: {e}")
                
        with annex_tab2:
            st.markdown("### Annexure-2: Operational Key Metrics")
            try:
                ann2_df = df.iloc[16:23, 1:6].copy()
                ann2_df.columns = ['Particulars', 'UoM', '23-24', '24-25', 'YTD Sep25']
                st.dataframe(ann2_df.reset_index(drop=True).dropna(how='all'), use_container_width=True)
            except Exception as e:
                st.error(f"Error loading Annexure 2: {e}")
                
        with annex_tab3:
            st.markdown("### Annexure-3: State, District, Plant & MPG Growth Plan")
            try:
                ann3_df = df.iloc[29:35, 1:14].copy()
                cols = ['Year', '2020-21', '2021-22', '2022-23', '2023-24', '2024-25', '2025-26', '2026-27 Plan', 'PY-1', 'PY-2', 'PY-3', 'PY-4', 'PY-5']
                ann3_df.columns = cols[:len(ann3_df.columns)]
                st.dataframe(ann3_df.reset_index(drop=True).dropna(how='all'), use_container_width=True)
            except Exception as e:
                st.error(f"Error loading Annexure 3: {e}")
                
    else:
        # Regional Sheets (BIHAR, Jharkhand, West Bengal) ke liye Clean Logic
        df = excel_data[selected_sheet]
        st.subheader(f"📊 Region View: {selected_sheet}")
        
        try:
            clean_df = df.copy()
            header_row_idx = 0
            for idx, row in clean_df.iterrows():
                row_str = str(row.values)
                if "Particulas" in row_str or "Parameters" in row_str:
                    header_row_idx = idx
                    break
            
            if header_row_idx > 0:
                clean_df.columns = clean_df.iloc[header_row_idx]
                clean_df = clean_df.iloc[header_row_idx + 1:].copy()
            else:
                if len(clean_df) > 3:
                    clean_df = clean_df.iloc[3:].copy()
            
            expected_cols = [
                'Particulas', 'UoM', 'Months', 
                'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar',
                'Blank_P', 'Q1', 'Q2', 'Q3', 'Q4', 'FY'
            ]
            
            current_cols = list(clean_df.columns)
            mapped_cols = [expected_cols[i] if i < len(expected_cols) else f"Col_{i}" for i in range(len(current_cols))]
            clean_df.columns = mapped_cols
            
            cols_to_drop = [col for col in clean_df.columns if col == 'Blank_P' or col.startswith('Col_')]
            if cols_to_drop:
                clean_df = clean_df.drop(columns=cols_to_drop)
            
            clean_df = clean_df.reset_index(drop=True).dropna(how='all')
            
            if 'Parameters' in clean_df.columns and 'Particulas' not in clean_df.columns:
                clean_df = clean_df.rename(columns={'Parameters': 'Particulas'})

            if selected_sheet == "BIHAR" and 'Particulas' in clean_df.columns:
                sudha_idx = clean_df[clean_df['Particulas'].astype(str).str.contains("Sudha Farm Gate", case=False, na=False)].index
                if not sudha_idx.empty:
                    clean_df = clean_df.loc[:sudha_idx[0]-1]
            
            if "Particulas" in clean_df.columns:
                mask_invalid_headers = clean_df['Particulas'].astype(str).str.contains('@', na=False) & (
                    clean_df['UoM'].isna() | (clean_df['UoM'].astype(str).str.strip().isin(['None', '', 'nan']))
                )
                clean_df = clean_df[~mask_invalid_headers]
                clean_df = clean_df[~clean_df['Particulas'].astype(str).str.contains("Avg Milk/Day @4%", case=False, na=False)]

            for col in clean_df.columns:
                if col not in ['Particulas', 'UoM', 'Months']:
                    clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce').round(2)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Rows", clean_df.shape[0])
            col2.metric("Total Columns", clean_df.shape[1])
            col3.metric("Data Status", "Live & Synchronized 🟢")
            
            st.markdown("---")
            
            # Quick Filter Buttons
            st.markdown("### ⚡ Quick Filter Buttons")
            b1, b2, b3 = st.columns(3)
            b4, b5 = st.columns(2)
            
            if 'filter_selection' not in st.session_state:
                st.session_state.filter_selection = "All"
                
            with b1:
                if st.button("Supply Chain Cost", use_container_width=True):
                    st.session_state.filter_selection = "Supply chain Cost"
            with b2:
                if st.button("Network Landed Cost", use_container_width=True):
                    st.session_state.filter_selection = "Network Landed Cost"
            with b3:
                if st.button("Overall Landed Cost", use_container_width=True):
                    st.session_state.filter_selection = "Overall Landed Cost"
            with b4:
                if st.button("Network Volume", use_container_width=True):
                    st.session_state.filter_selection = "Network"
            with b5:
                if st.button("Show All Data", use_container_width=True):
                    st.session_state.filter_selection = "All"

            # Dropdown Filters Section
            st.markdown("### 🔍 Filter Data (Dropdown Options)")
            f_col1, f_col2 = st.columns(2)
            
            particulas_options = ["All"]
            if "Particulas" in clean_df.columns:
                particulas_options.extend(clean_df["Particulas"].dropna().astype(str).unique().tolist())
                
            fy_options = ["All"]
            if "Months" in clean_df.columns:
                all_months = clean_df["Months"].dropna().astype(str)
                fys = all_months[all_months.str.contains("FY", case=False, na=False)].unique().tolist()
                fy_options.extend(fys)
            
            default_particula_index = 0
            if st.session_state.filter_selection in particulas_options:
                default_particula_index = particulas_options.index(st.session_state.filter_selection)
            
            with f_col1:
                selected_metric = st.selectbox("Select Particulas / Metric:", particulas_options, index=default_particula_index)
            with f_col2:
                selected_fy = st.selectbox("Select Financial Year:", fy_options)
                
            filtered_df = clean_df.copy()
            active_filter = selected_metric if selected_metric != "All" else st.session_state.filter_selection
            
            if active_filter == "Network":
                network_keywords = ["Own Network", "Vendor", "Transfer", "Moo Mark", "3P Network"]
                pattern = '|'.join(network_keywords)
                filtered_df = filtered_df[filtered_df["Particulas"].astype(str).str.contains(pattern, case=False, na=False)]
            elif active_filter != "All":
                filtered_df = filtered_df[filtered_df["Particulas"].astype(str).str.contains(active_filter, case=False, na=False)]
                
            if selected_fy != "All":
                filtered_df = filtered_df[filtered_df["Months"].astype(str).str.contains(selected_fy, case=False, na=False)]
                
            display_df = filtered_df.copy()
            subtotal_df = pd.DataFrame()
            
            if not display_df.empty:
                numeric_cols = [c for c in display_df.columns if c not in ['Particulas', 'UoM', 'Months']]
                subtotal_data = {'Particulas': '⚡ TOTAL / SUBTOTAL', 'UoM': '', 'Months': ''}
                for col in numeric_cols:
                    subtotal_data[col] = display_df[col].sum().round(2)
                subtotal_df = pd.DataFrame([subtotal_data])

            st.subheader(f"📋 {selected_sheet} - Cleaned Structured Table")
            st.dataframe(display_df, use_container_width=True)
            
            if not subtotal_df.empty:
                st.markdown("📌 **Subtotal Summary (Fixed Bottom View):**")
                st.dataframe(subtotal_df, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error processing sheet structure: {e}")
            st.dataframe(df, use_container_width=True)
        
else:
    st.error("⚠️ Error: 'Historical Data.xlsx' file nahi mili!")
