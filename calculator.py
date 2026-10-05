import pandas as pd

def get_sheet_metrics(df):
    """DataFrame se basic calculations aur metrics nikalne ke liye function"""
    if df is not None and not df.empty:
        total_rows = df.shape[0]
        total_cols = df.shape[1]
        
        numeric_df = df.select_dtypes(include=['number'])
        summary_stats = numeric_df.describe() if not numeric_df.empty else None
        
        return {
            "rows": total_rows,
            "cols": total_cols,
            "stats": summary_stats
        }
    return None

def filter_data_by_query(df, search_query):
    """Agar client ko data me kuch search karna ho"""
    if search_query and df is not None:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        return df[mask]
    return df

def get_state_wise_summary(excel_data):
    """Basic state-wise summary table ke liye"""
    summary_data = []
    for sheet_name, df in excel_data.items():
        if sheet_name not in ["Summary", "Volume Summary"]:
            try:
                vol_val = 0
                cost_val = 0
                for _, row in df.iterrows():
                    row_text = str(row.values)
                    if "Vol Kg/day" in row_text:
                        numeric_vals = pd.to_numeric(pd.Series(row.values), errors='coerce').dropna()
                        if not numeric_vals.empty:
                            vol_val = numeric_vals.iloc[-1]
                    if "Supply Chain Cost" in row_text:
                        numeric_vals = pd.to_numeric(pd.Series(row.values), errors='coerce').dropna()
                        if not numeric_vals.empty:
                            cost_val = numeric_vals.iloc[-1]
                summary_data.append({
                    "State / Region": sheet_name,
                    "Vol Kg/day": round(vol_val, 2),
                    "Supply Chain Cost": round(cost_val, 2)
                })
            except Exception:
                pass
    if summary_data:
        return pd.DataFrame(summary_data)
    return pd.DataFrame()

def get_year_wise_growth_summary(excel_data):
    """
    'Volume Summary' sheet ke Annexure-1 se direct Year-by-Year Growth data uthane ka robust function.
    """
    try:
        if "Volume Summary" in excel_data:
            df = excel_data["Volume Summary"]
            # Annexure 1 ka exact table structure extract karna
            ann1_df = df.iloc[2:11, 1:7].copy()
            ann1_df.columns = ['Year', 'BR', 'WB', 'JH', 'Total', 'GOLY']
            ann1_df = ann1_df.reset_index(drop=True).dropna(how='all')
            
            # Row index 0 par agar headers ya extra text hai toh use hata dein
            ann1_df = ann1_df[ann1_df['Year'].astype(str).str.contains("FY|20", case=False, na=False)]
            
            if not ann1_df.empty:
                # Numeric values me convert karna taaki chart aur table theek se chalein
                for col in ['BR', 'WB', 'JH', 'Total']:
                    ann1_df[col] = pd.to_numeric(ann1_df[col], errors='coerce').fillna(0)
                
                # App.py ke format ke mutabiq DataFrame ko reshape karna (State-wise row format)
                records = []
                for _, row in ann1_df.iterrows():
                    yr = str(row['Year']).strip()
                    records.append({"State": "BR", "Year": yr, "Vol Kg/day": row['BR']})
                    records.append({"State": "WB", "Year": yr, "Vol Kg/day": row['WB']})
                    records.append({"State": "JH", "Year": yr, "Vol Kg/day": row['JH']})
                
                df_res = pd.DataFrame(records)
                pivot_df = df_res.pivot_table(index='State', columns='Year', values='Vol Kg/day', aggfunc='sum').fillna(0)
                
                years = sorted([col for col in pivot_df.columns if 'FY' in str(col) or '20' in str(col)])
                if len(years) >= 2:
                    for i in range(1, len(years)):
                        prev_yr = years[i-1]
                        curr_yr = years[i]
                        growth_col = f"Growth {prev_yr} to {curr_yr} (%)"
                        pivot_df[growth_col] = (((pivot_df[curr_yr] - pivot_df[prev_yr]) / pivot_df[prev_yr].replace(0, 1)) * 100).round(2)
                
                return pivot_df.reset_index()
    except Exception as e:
        print(f"Error in get_year_wise_growth_summary: {e}")
        
    return pd.DataFrame()
