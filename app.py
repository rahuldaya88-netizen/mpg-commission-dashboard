import os
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(page_title="MPG Commission Dashboard", layout="wide")

st.title("📊 MPG Commission Automated Web App (Bihar Clean View)")


@st.cache_data(ttl=600)
def load_and_process_data():
    potential_folders = [
        "FYI-26-27",
        "FYI-27-28",
        os.path.join("data", "FYI-26-27"),
        os.path.join("data", "FYI-27-28"),
    ]

    folders = [f for f in potential_folders if os.path.exists(f)]

    excluded_files = [
        "Farmer Master Kalayanpur.xlsb",
        "Farmer Master.xlsb",
        "Farmer Master_Kalayanpur.xlsb",
        "Farmer Master_Other.xlsb",
        "Farmer Master_Updated for kalayanpur.xlsb",
        "Farmer Master_Updated Kalayanpur.xlsb",
        "Farmer Master_Updated-v1.xlsb",
        "Farmer Master_Updated. (1).xlsb",
        "Farmer Master_Updated. (2).xlsb",
        "Farmer Master_Updated.-v2.xlsb",
        "Farmer Master_Updated..xlsb",
        "Farmer Master_Updated.2.xlsb",
        "Farmer Master_Updated.New ..xlsb",
        "Farmer Master_Updated.xlsb",
        "Rahul Sir.xlsb",
        "~$05. Farmer Payment-11-17 Apr.xlsb",
        "~$07. Farmer Payment-18-24 Apr.xlsb",
        "~$08. Farmer Payment-25-01 Apr.xlsb",
        "19. Farmer Payment-31-06 Aug.xlsb",
    ]

    all_dfs = []
    debug_info = []

    if not folders:
        debug_info.append("❌ Koi bhi FYI folder nahi mila!")

    for folder in folders:
        debug_info.append(f"✅ Folder mil gaya: {folder}")
        found_files_count = 0
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(
                    (".xlsb", ".xlsx")
                ) and not file.startswith("~$"):
                    found_files_count += 1
                    file_path = os.path.join(root, file)

                    if file in excluded_files:
                        continue

                    try:
                        engine = (
                            "pyxlsb"
                            if file.lower().endswith(".xlsb")
                            else "openpyxl"
                        )
                        # Bina header ke read karo pehle
                        df_raw = pd.read_excel(
                            file_path,
                            sheet_name="MPG Payment",
                            engine=engine,
                            header=None,
                        )

                        # Dynamic Header Row Find karna (jahan 'bmc code' ya 'mpg name' ho)
                        h_idx = 0
                        for idx, row in df_raw.head(10).iterrows():
                            vals = [
                                str(x).strip().lower()
                                for x in row.values
                                if pd.notna(x)
                            ]
                            if any("bmc code" in v or "bmc" in v for v in vals):
                                h_idx = idx
                                break

                        df = df_raw.iloc[h_idx + 1 :].copy()
                        df.columns = [
                            str(c).strip() if pd.notna(c) else f"Col_{i}"
                            for i, c in enumerate(df_raw.iloc[h_idx])
                        ]
                        df.reset_index(drop=True, inplace=True)

                        # FYI Year assign karna
                        if "26-27" in folder or "26-27" in file_path:
                            df["FYI"] = "26-27"
                        else:
                            df["FYI"] = "27-28"

                        # State / Location detection folder path se
                        root_lower = root.lower()
                        if "bihar" in root_lower:
                            df["Location"] = "Bihar"
                        elif "jharkhand" in root_lower:
                            df["Location"] = "Jharkhand"
                        elif "ramgarh" in root_lower:
                            df["Location"] = "Ramgarh"
                        else:
                            df["Location"] = "Other"

                        df["Source_File"] = file
                        all_dfs.append(df)
                    except Exception as e:
                        continue

        debug_info.append(
            f"📂 Total valid files read hui ({folder}): {found_files_count}"
        )

    return all_dfs, debug_info


# Run loading
all_dfs, debug_info = load_and_process_data()

with st.expander("🔍 Folder Connection Status"):
    for info in debug_info:
        st.write(info)

if all_dfs:
    master_df = pd.concat(all_dfs, ignore_index=True)
    master_df.columns = master_df.columns.astype(str).str.strip()

    # Sirf Bihar ka data lock
    if "Location" in master_df.columns:
        master_df = master_df[master_df["Location"] == "Bihar"]

    # --- SMART COLUMN FINDER ---
    def find_col(df, keywords):
        for col in df.columns:
            for kw in keywords:
                if kw.lower() in col.lower():
                    return col
        return None

    vol_col = find_col(master_df, ["bmc volume", "volume", "qty"])
    amt_col = find_col(master_df, ["bmc amount", "amount", "value"])
    sample_col = find_col(master_df, ["sample"])

    # Calculations with flexible columns
    master_df["BMC Volume"] = (
        pd.to_numeric(master_df[vol_col], errors="coerce").fillna(0)
        if vol_col
        else 0
    )
    master_df["BMC Amount"] = (
        pd.to_numeric(master_df[amt_col], errors="coerce").fillna(0)
        if amt_col
        else 0
    )
    sample_val = (
        pd.to_numeric(master_df[sample_col], errors="coerce").fillna(0)
        if sample_col
        else 0
    )

    master_df["Sahayak_Commission"] = master_df["BMC Volume"] * 0.75
    master_df["Std_gain"] = master_df["BMC Volume"] * 0.95
    master_df["Std_Gain_3"] = master_df["BMC Amount"] * 0.03
    amc_col = master_df["BMC Volume"] * 0.10

    master_df["Commission Final"] = (
        master_df["Sahayak_Commission"] + master_df["Std_gain"] + sample_val
    ) - amc_col

    # Unnamed / Unwanted technical columns drop karo jo sirf empty hain
    drop_cols = [
        c
        for c in master_df.columns
        if c.lower() == "nan"
        or c.lower() == "none"
        or c.startswith("Col_")
        and c.replace("Col_", "").isdigit()
    ]
    # Keep actual useful columns clean
    drop_excess = [
        c
        for c in master_df.columns
        if "unnamed" in c.lower()
        and master_df[c].dropna().astype(str).str.strip().eq("").all()
    ]
    master_df = master_df.drop(columns=drop_excess, errors="ignore")

    # Decimal rounding (2 decimals)
    numeric_cols = master_df.select_dtypes(include=["float64", "int64"]).columns
    master_df[numeric_cols] = master_df[numeric_cols].round(2)

    st.success(
        f"✅ Bihar Data Loaded & Cleaned! Total Records: {len(master_df):,}"
    )

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🔍 Filters & Search")
    search_box = st.sidebar.text_input("Search by Code / Name", "")

    # FYI Year Filter
    if "FYI" in master_df.columns:
        fyi_options = ["All"] + list(master_df["FYI"].dropna().unique())
        selected_fyi = st.sidebar.selectbox("Select FYI Year", fyi_options)
    else:
        selected_fyi = "All"

    # --- APPLY FILTERS ---
    filtered_df = master_df.copy()

    if selected_fyi != "All":
        filtered_df = filtered_df[filtered_df["FYI"] == selected_fyi]

    if search_box:
        mask = filtered_df.astype(str).apply(
            lambda row: row.str.contains(search_box, case=False).any(), axis=1
        )
        filtered_df = filtered_df[mask]

    # Metrics
    st.subheader("📈 Summary Metrics (Bihar)")
    col1, col2, col3 = st.columns(3)
    total_vol = filtered_df["BMC Volume"].sum()
    total_comm = filtered_df["Commission Final"].sum()

    col1.metric("Total BMC Volume", f"{total_vol:,.2f}")
    col2.metric("Total Final Commission", f"₹ {total_comm:,.2f}")
    col3.metric("Total Records", f"{len(filtered_df):,}")

    st.subheader("📋 Cleaned Processed Data Table (Bihar)")
    st.dataframe(filtered_df, use_container_width=True)

else:
    st.warning("⚠️ Bihar ka data nahi mila. Kripya check karein.")
