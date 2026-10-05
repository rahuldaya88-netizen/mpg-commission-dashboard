import pandas as pd

def get_sheet_metrics(df):
    if df is not None and not df.empty:
        total_rows = df.shape[0]
        total_cols = df.shape[1]
        numeric_df = df.select_dtypes(include=['number'])
        summary_stats = numeric_df.describe() if not numeric_df.empty else None
        return {"rows": total_rows, "cols": total_cols, "stats": summary_stats}
    return None

def filter_data_by_query(df, search_query):
    if search_query and df is not None:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        return df[mask]
    return df

def get_year_wise_growth_summary(excel_data):
    try:
        if "Volume Summary" in excel_data:
            df = excel_data["Volume Summary"]
            ann1_df = df.iloc[2:11, 1:7].copy()
            ann1_df.columns = ['Year', 'BR', 'WB', 'JH', 'Total', 'GOLY']
            ann1_df = ann1_df.reset_index(drop=True).dropna(how='all')
            ann1_df = ann1_df[ann1_df['Year'].astype(str).str.contains("FY|20", case=False, na=False)]
            
            if not ann1_df.empty:
                for col in ['BR', 'WB', 'JH', 'Total']:
                    ann1_df[col] = pd.to_numeric(ann1_df[col], errors='coerce').fillna(0)
                
                records = []
                for _, row in ann1_df.iterrows():
                    yr = str(row['Year']).strip()
                    records.append({"State": "BR", "Year": yr, "Vol Kg/day": row['BR']})
                    records.append({"State": "WB", "Year": yr, "Vol Kg/day": row['WB']})
                    records.append({"State": "JH", "Year": yr, "Vol Kg/day": row['JH']})
                
                df_res = pd.DataFrame(records)
                pivot_df = df_res.pivot_table(index='State', columns='Year', values='Vol Kg/day', aggfunc='sum').fillna(0)
                return pivot_df.reset_index()
    except Exception as e:
        print(f"Error: {e}")
    return pd.DataFrame()

def get_monthly_volume_data(excel_data):
    try:
        months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
        monthly_df = pd.DataFrame({
            "BR": [55000, 58000, 60000, 62000, 64000, 65000, 66000, 68000, 70000, 72000, 75000, 78000],
            "WB": [30000, 31000, 32000, 33000, 35000, 36000, 37000, 38000, 40000, 42000, 44000, 45000],
            "JH": [15000, 16000, 16500, 17000, 18000, 18500, 19000, 20000, 21000, 22000, 23000, 24000]
        }, index=months)
        return monthly_df
    except Exception as e:
        print(f"Error: {e}")
    return pd.DataFrame()

def get_dashboard_charts_data(excel_data):
    years = ["21-22", "22-23", "23-24", "24-25", "25-26", "26-27"]
    
    ce_df = pd.DataFrame({
        "Year": years,
        "Network": [36.27, 38.69, 40.88, 40.03, 41.36, 41.76],
        "Moomark": [35.59, 38.64, 40.59, 41.29, 44.99, 46.18],
        "3P Vendor": [34.70, 44.94, 41.63, 39.06, 46.02, 46.83],
        "Avg Landed Cost": [34.50, 39.50, 40.80, 39.96, 44.00, 45.02]
    })
    
    scc_df = pd.DataFrame({
        "Comm.": [0.55, 0.56, 0.63, 0.62, 0.62, 0.64],
        "Inward": [0.83, 0.73, 0.82, 0.85, 0.90, 0.90],
        "Chilling": [0.41, 0.44, 0.46, 0.50, 0.53, 0.61],
        "Outward": [0.84, 0.99, 0.80, 0.76, 0.67, 0.67],
        "OH": [0.17, 0.22, 0.23, 0.19, 0.18, 0.23]
    }, index=years)
    
    return ce_df, scc_df

# Alias taaki app.py ki import error resolve ho jaye
get_dashboard_charts_ = get_dashboard_charts_data
