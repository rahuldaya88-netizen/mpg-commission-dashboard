import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import os
from loader import load_excel_sheets
from calculator import get_year_wise_growth_summary, get_dashboard_charts_data, get_monthly_volume_data, get_executive_kpis

st.set_page_config(
    page_title="MPG Commission - Live Dashboard",
    page_icon="🥛",
    layout="wide"
)

# Custom Glassmorphism / Dark UI Styling + Clean Fonts
st.markdown("""
    <style>
    .stApp {
        background-color: #0B0F19;
        color: #E2E8F0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 10px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetric"] label {
        color: #94A3B8 !important;
        font-size: 13px !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-size: 20px !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.2rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def fetch_data():
    return load_excel_sheets()

excel_data = fetch_data()

if excel_data is not None:
    st.sidebar.header("🎛️ Dashboard Controls & Filters")
    
    if 'nav_selection' not in st.session_state:
        st.session_state.nav_selection = "Summary"

    if st.sidebar.button("📊 Summary", use_container_width=True):
        st.session_state.nav_selection = "Summary"
        
    if st.sidebar.button("📊 Power BI Report (HTML)", use_container_width=True):
        st.session_state.nav_selection = "Power BI Report"
        
    st.sidebar.markdown("---")
    
    sheet_names = list(excel_data.keys())
    dropdown_options = ["Summary", "Power BI Report"] + sheet_names
    current_index = dropdown_options.index(st.session_state.nav_selection) if st.session_state.nav_selection in dropdown_options else 0

    selected_sheet = st.sidebar.selectbox("Choose Sheet", dropdown_options, index=current_index)
    st.session_state.nav_selection = selected_sheet
    
    st.sidebar.markdown("---")
    
    state_filter = "All states"
    sourcing_filter = "All sourcing"
    selected_year_filter = "All Years"
    selected_qtrs = []
    
    if selected_sheet == "Summary":
        growth_df_temp = get_year_wise_growth_summary(excel_data)
        dynamic_years = [col for col in growth_df_temp.columns if col not in ['State', 'Particulas']] if not growth_df_temp.empty else ["2014-15", "2015-16", "2016-17", "2017-18", "2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26", "2026-27"]

        st.sidebar.markdown("### ⚙️ View & Filters")
        view_mode = st.sidebar.radio("View Mode", ["FY", "Monthly"], horizontal=True)
        
        if view_mode == "Monthly":
            year_options = ["All Years"] + dynamic_years
            selected_year_filter = st.sidebar.selectbox("Select Year", year_options)
            
            qtr_options = ["Q1", "Q2", "Q3", "Q4"]
            selected_qtrs = st.sidebar.multiselect("Select Qtr (Multiple Options)", qtr_options, default=[])

        state_filter = st.sidebar.selectbox("Select State", ["All states", "BR", "WB", "JH"])
        sourcing_filter = st.sidebar.selectbox("Select Sourcing", ["All sourcing", "Network", "Moomark", "3P Vendor", "Avg Landed Cost"])

    # Main Dashboard Header
    st.title("🥛 Historical Procurement Live Dashboard")
    st.markdown("Dashboard **real-time synchronized**.")
    
    # --- EXECUTIVE KPI CARDS ROW (Synchronized with filters) ---
    kpis = get_executive_kpis(excel_data, state_filter=state_filter, sourcing_filter=sourcing_filter)
    
    st.markdown("---")
    kpi_cols = st.columns(8)
    
    with kpi_cols[0]:
        st.metric(label="VOLUME", value=f"{kpis['volume']:,.0f}", delta="▲ 24.5% GoLY")
        st.caption("▼ 28.8% vs Plan\nkgs / day")
    with kpi_cols[1]:
        st.metric(label="NETWORK VOL", value=f"{kpis['network_vol']:,.0f}", delta="▲ 53.1% GoLY")
        st.caption("▼ 11.1% vs Plan\nkgs/day - of total vol")
    with kpi_cols[2]:
        st.metric(label="AVG LANDED COST", value=f"₹ {kpis['avg_cost']:.2f}", delta="▲ 5.7% GoLY")
        st.caption("▼ 0.6% vs Plan\nper kg")
    with kpi_cols[3]:
        st.metric(label="SUPL. CHAIN COST", value=f"₹ {kpis['scc_cost']:.2f}", delta="▲ 4.5% GoLY")
        st.caption("▲ 0.3% vs Plan\nper kg - Network")
    with kpi_cols[4]:
        st.metric(label="NO. OF FARMERS", value=f"{kpis['farmers']:,}", delta="▲ 12.3% GoLY")
        st.caption("▲ 108.1% vs Plan\nsum of state peaks")
    with kpi_cols[5]:
        st.metric(label="POURING / FARMER", value="20", delta="▲ 36.4% GoLY")
        st.caption("▼ 57.3% vs Plan\nNetwork kgs + farmers")
    with kpi_cols[6]:
        st.metric(label="NO OF MPGS", value=f"{kpis['mpgs']:,}", delta="▲ 34.8% GoLY")
        st.caption("▼ 13.0% vs Plan\nsum of state peaks")
    with kpi_cols[7]:
        st.metric(label="POURING / MPG", value="185", delta="▲ 13.6% GoLY")
        st.caption("▲ 2.1% vs Plan\nNetwork kgs + MPGs")
    st.markdown("---")
    
    if selected_sheet == "Power BI Report":
        st.subheader("📊 Power BI Report / HTML Canvas View")
        html_file_path = "powerbi_report.html"
        
        if os.path.exists(html_file_path):
            with open(html_file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            components.html(html_content, height=800, scrolling=True)
        else:
            st.info("💡 `powerbi_report.html` file nahi mili. Pehle apne folder mein `convert_pbix.py` script run karein.")
            
    elif selected_sheet == "Summary":
        if view_mode == "Monthly":
            col_top_l, col_top_r = st.columns(2)
            
            with col_top_l:
                st.subheader("📋 Monthly Detailed Table (Sourcing & Metrics)")
                monthly_raw_df = get_monthly_volume_data(excel_data, sourcing_filter=sourcing_filter)
                
                if not monthly_raw_df.empty:
                    filtered_m = monthly_raw_df.copy()
                    if selected_year_filter != "All Years":
                        filtered_m = filtered_m[filtered_m['Financial Year'].astype(str).str.contains(selected_year_filter, case=False, na=False)]
                    
                    if state_filter != "All states":
                        filtered_m = filtered_m[filtered_m['State'] == state_filter]
                    
                    q_map = {
                        "Q1": ['Apr', 'May', 'Jun', 'Q1'],
                        "Q2": ['Jul', 'Aug', 'Sep', 'Q2'],
                        "Q3": ['Oct', 'Nov', 'Dec', 'Q3'],
                        "Q4": ['Jan', 'Feb', 'Mar', 'Q4']
                    }
                    
                    base_cols = ['State', 'Particulas', 'Financial Year'] if sourcing_filter != "All sourcing" else ['State', 'Financial Year']
                    all_months = ['Apr', 'May', 'Jun', 'Q1', 'Jul', 'Aug', 'Sep', 'Q2', 'Oct', 'Nov', 'Dec', 'Q3', 'Jan', 'Feb', 'Mar', 'Q4']
                    
                    if selected_qtrs:
                        active_cols = []
                        for q in selected_qtrs:
                            active_cols.extend(q_map.get(q, []))
                        keep_cols = base_cols + [c for c in active_cols if c in filtered_m.columns]
                    else:
                        keep_cols = base_cols + [m for m in all_months if m in filtered_m.columns]
                        
                    filtered_m = filtered_m[[c for c in keep_cols if c in filtered_m.columns]]
                    st.dataframe(filtered_m, use_container_width=True, hide_index=True, height=210)
                else:
                    st.warning("Monthly data available nahi hai.")

            with col_top_r:
                st.subheader("📊 Monthly Volume Trend")
                if not monthly_raw_df.empty and 'filtered_m' in locals():
                    months_list = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
                    if selected_qtrs:
                        active_months = []
                        for q in selected_qtrs:
                            active_months.extend([m for m in q_map.get(q, []) if m in months_list])
                        available_m = [m for m in months_list if m in filtered_m.columns and m in active_months]
                    else:
                        available_m = [m for m in months_list if m in filtered_m.columns]
                    
                    if available_m:
                        id_vars_list = ['State', 'Particulas', 'Financial Year'] if 'Particulas' in filtered_m.columns else ['State', 'Financial Year']
                        color_col = 'Particulas' if 'Particulas' in filtered_m.columns else 'State'
                        
                        melted_m = filtered_m.melt(id_vars=id_vars_list, value_vars=available_m, var_name='Month', value_name='Volume')
                        melted_m['Volume'] = pd.to_numeric(melted_m['Volume'], errors='coerce').fillna(0)
                        
                        fig_monthly = px.bar(
                            melted_m, x='Month', y='Volume', color=color_col, barmode='relative',
                            text_auto=',.0f'
                        )
                        fig_monthly.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                            font_color='white', height=245, margin=dict(l=10, r=10, t=10, b=10)
                        )
                        fig_monthly.update_traces(textfont_size=8, textangle=0, textposition="inside", cliponaxis=False)
                        st.plotly_chart(fig_monthly, use_container_width=True)

            st.markdown("---")
            col_bot_l, col_bot_r = st.columns(2)
            with col_bot_l:
                st.subheader("📊 Operational Cost Analytics")
                ce_df, scc_data = get_dashboard_charts_data(excel_data)
                if not ce_df.empty:
                    melted_ce = ce_df.melt('Year', var_name='Sourcing_Type', value_name='Cost')
                    if sourcing_filter != "All sourcing":
                        melted_ce = melted_ce[melted_ce['Sourcing_Type'] == sourcing_filter]
                    melted_ce['Cost'] = pd.to_numeric(melted_ce['Cost'], errors='coerce').fillna(0)

                    fig_ce = px.line(melted_ce, x='Year', y='Cost', color='Sourcing_Type', markers=True, text='Cost')
                    fig_ce.update_traces(line=dict(shape='spline', width=2), marker=dict(size=6), textposition="top center", texttemplate='%{text:.2f}')
                    fig_ce.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=245, margin=dict(l=10, r=10, t=10, b=10))
                    st.plotly_chart(fig_ce, use_container_width=True)

            with col_bot_r:
                st.subheader("📊 Supply Chain Cost Breakdown")
                if not scc_data.empty:
                    scc_chart_df = scc_data.reset_index()
                    id_col = scc_chart_df.columns[0]
                    value_cols = [c for c in scc_chart_df.columns if c != id_col]
                    scc_melted = scc_chart_df.melt(id_vars=[id_col], value_vars=value_cols, var_name='Cost_Type', value_name='Cost')
                    scc_melted['Cost'] = pd.to_numeric(scc_melted['Cost'], errors='coerce').fillna(0)

                    fig_scc = px.bar(scc_melted, x=id_col, y='Cost', color='Cost_Type', barmode='group', text_auto='.2f')
                    fig_scc.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=245, margin=dict(l=10, r=10, t=10, b=10))
                    fig_scc.update_traces(textfont_size=8, textangle=0, textposition="outside", cliponaxis=False)
                    st.plotly_chart(fig_scc, use_container_width=True)

        else:
            col_fy_l, col_fy_r = st.columns(2)
            
            growth_df = get_year_wise_growth_summary(excel_data, sourcing_filter=sourcing_filter)
            filtered_growth = growth_df.copy()
            if state_filter != "All states":
                if 'State' in filtered_growth.columns:
                    filtered_growth = filtered_growth[filtered_growth['State'] == state_filter]
            
            for col in filtered_growth.columns:
                if col not in ['State', 'Particulas']:
                    filtered_growth[col] = pd.to_numeric(filtered_growth[col], errors='coerce')
                    filtered_growth[col] = filtered_growth[col].round(2)

            with col_fy_l:
                st.subheader("📈 Year-by-Year Volume (Sourcing Breakdown)")
                if not filtered_growth.empty:
                    st.dataframe(filtered_growth, use_container_width=True, hide_index=True, height=210)
                else:
                    st.warning("Data available nahi hai.")

            with col_fy_r:
                st.subheader("📊 Visual Growth Chart (Stacked View)")
                chart_cols = [col for col in filtered_growth.columns if col not in ['State', 'Particulas']]
                if chart_cols and not filtered_growth.empty:
                    id_vars_fy = ['State', 'Particulas'] if 'Particulas' in filtered_growth.columns else ['State']
                    color_col_fy = 'Particulas' if 'Particulas' in filtered_growth.columns else 'State'
                    
                    chart_df = filtered_growth.melt(id_vars=id_vars_fy, value_vars=chart_cols, var_name='Year', value_name='Volume')
                    chart_df['Volume'] = pd.to_numeric(chart_df['Volume'], errors='coerce').fillna(0)
                    
                    fig_growth = px.bar(chart_df, x='Year', y='Volume', color=color_col_fy, barmode='relative', text_auto=',.2f')
                    fig_growth.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font_color='white', height=245, margin=dict(l=10, r=10, t=10, b=10),
                        legend=dict(title="Category")
                    )
                    fig_growth.update_traces(textfont_size=8, textangle=0, textposition="inside", cliponaxis=False)
                    st.plotly_chart(fig_growth, use_container_width=True)

            st.markdown("---")
            col_b_l, col_b_r = st.columns(2)
            
            ce_df, scc_data = get_dashboard_charts_data(excel_data)
            
            with col_b_l:
                st.subheader("📊 Operational Cost Analytics & Trends")
                if not ce_df.empty:
                    melted_ce = ce_df.melt('Year', var_name='Sourcing_Type', value_name='Cost')
                    if sourcing_filter != "All sourcing":
                        melted_ce = melted_ce[melted_ce['Sourcing_Type'] == sourcing_filter]
                    melted_ce['Cost'] = pd.to_numeric(melted_ce['Cost'], errors='coerce').fillna(0)

                    fig_ce = px.line(melted_ce, x='Year', y='Cost', color='Sourcing_Type', markers=True, text='Cost')
                    fig_ce.update_traces(line=dict(shape='spline', width=2), marker=dict(size=6), textposition="top center", texttemplate='%{text:.2f}')
                    fig_ce.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=245, margin=dict(l=10, r=10, t=10, b=10))
                    st.plotly_chart(fig_ce, use_container_width=True)

            with col_b_r:
                st.subheader("📊 Supply Chain Cost Breakdown (₹ / kg)")
                if not scc_data.empty:
                    scc_chart_df = scc_data.reset_index()
                    id_col = scc_chart_df.columns[0]
                    value_cols = [c for c in scc_chart_df.columns if c != id_col]
                    scc_melted = scc_chart_df.melt(id_vars=[id_col], value_vars=value_cols, var_name='Cost_Type', value_name='Cost')
                    scc_melted['Cost'] = pd.to_numeric(scc_melted['Cost'], errors='coerce').fillna(0)

                    fig_scc = px.bar(scc_melted, x=id_col, y='Cost', color='Cost_Type', barmode='group', text_auto='.2f')
                    fig_scc.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=245, margin=dict(l=10, r=10, t=10, b=10))
                    fig_scc.update_traces(textfont_size=8, textangle=0, textposition="outside", cliponaxis=False)
                    st.plotly_chart(fig_scc, use_container_width=True)

    elif selected_sheet == "Volume Summary":
        df = excel_data[selected_sheet]
        st.subheader("📊 Volume Summary - Data Structure & Annexures")
        
        ann_tab1, annex_tab2, annex_tab3 = st.tabs(["Annexure 1 (State Growth)", "Annexure 2 (Key Metrics)", "Annexure 3 (Plant & Plan)"])
        
        with ann_tab1:
            st.markdown("### Annexure-1: State-wise Year Growth Summary")
            try:
                ann1_df = df.iloc[2:18, 1:7].copy()
                ann1_df.columns = ['Year', 'BR', 'WB', 'JH', 'Total', 'GOLY']
                ann1_df = ann1_df.reset_index(drop=True).dropna(how='all')
                
                if 'GOLY' in ann1_df.columns:
                    ann1_df['GOLY'] = pd.to_numeric(ann1_df['GOLY'], errors='coerce')
                    ann1_df['GOLY'] = (ann1_df['GOLY'] * 100).round(0).astype(str).str.replace('.0', '', regex=False) + '%'
                    
                st.dataframe(ann1_df, use_container_width=True, height=280)
            except Exception as e:
                st.error(f"Error loading Annexure 1: {e}")
                
        with annex_tab2:
            st.markdown("### Annexure-2: Operational Key Metrics")
            try:
                ann2_df = df.iloc[16:23, 1:6].copy()
                ann2_df.columns = ['Particulars', 'UoM', '23-24', '24-25', 'YTD Sep25']
                st.dataframe(ann2_df.reset_index(drop=True).dropna(how='all'), use_container_width=True, height=280)
            except Exception as e:
                st.error(f"Error loading Annexure 2: {e}")
                
        with annex_tab3:
            st.markdown("### Annexure-3: State, District, Plant & MPG Growth Plan")
            try:
                ann3_df = df.iloc[29:35, 1:14].copy()
                cols = ['Year', '2020-21', '2021-22', '2022-23', '2023-24', '2024-25', '2025-26', '2026-27 Plan', 'PY-1', 'PY-2', 'PY-3', 'PY-4', 'PY-5']
                ann3_df.columns = cols[:len(ann3_df.columns)]
                st.dataframe(ann3_df.reset_index(drop=True).dropna(how='all'), use_container_width=True, height=280)
            except Exception as f_err:
                st.error(f"Error loading Annexure 3: {f_err}")
                
    else:
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

            st.subheader(f"📋 {selected_sheet} - Cleaned Structured Table Data")
            st.dataframe(display_df, use_container_width=True, height=220)
            
            if not subtotal_df.empty:
                st.markdown("📌 **Subtotal Summary (Fixed Bottom View):**")
                st.dataframe(subtotal_df, use_container_width=True, height=100)
                
        except Exception as e:
            st.error(f"Error processing sheet structure: {e}")
            st.dataframe(df, use_container_width=True)
        
else:
    st.error("⚠️ Error: 'Historical Data.xlsx' file nahi mili!")
