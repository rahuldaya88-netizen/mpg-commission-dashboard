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
                        # header=1 use kiya taaki BMC Code sahi header bane
                        df = pd.read_excel(
                            file_path,
                            sheet_name="MPG Payment",
                            engine=engine,
                            header=1,
                        )

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

    # Sirf 'nan' ya blank technical columns hatao, data columns nahi
    drop_cols = [c for c in master_df.columns if c.lower() == "nan"]
    master_df = master_df.drop(columns=drop_cols, errors="ignore")

    # --- SIRF BIHAR KA DATA LOCK ---
    if "Location" in master_df.columns:
        master_df = master_df[master_df["Location"] == "Bihar"]

    # Calculations
    if "BMC Volume" in master_df.columns:
        master_df["BMC Volume"] = pd.to_numeric(
            master_df["BMC Volume"], errors="coerce"
        ).fillna(0)
        master_df["Sahayak_Commission"] = master_df["BMC Volume"] * 0.75
        master_df["Std_gain"] = master_df["BMC Volume"] * 0.95

    if "BMC Amount" in master_df.columns:
        master_df["BMC Amount"] = pd.to_numeric(
            master_df["BMC Amount"], errors="coerce"
        ).fillna(0)
        master_df["Std_Gain_3"] = master_df["BMC Amount"] * 0.03

    if (
        "Sahayak_Commission" in master_df.columns
        and "Std_gain" in master_df.columns
    ):
        sample_val = (
            pd.to_numeric(master_df["Sample Am"], errors="coerce").fillna(0)
            if "Sample Am" in master_df.columns
            else 0
        )
        amc_col = (
            master_df["BMC Volume"] * 0.10
            if "BMC Volume" in master_df.columns
            else 0
        )
        master_df["Commission Final"] = (
            master_df["Sahayak_Commission"] + master_df["Std_gain"] + sample_val
        ) - amc_col

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
    total_vol = (
        filtered_df["BMC Volume"].sum()
        if "BMC Volume" in filtered_df.columns
        else 0
    )
    total_comm = (
        filtered_df["Commission Final"].sum()
        if "Commission Final" in filtered_df.columns
        else 0
    )

    col1.metric("Total BMC Volume", f"{total_vol:,.2f}")
    col2.metric("Total Final Commission", f"₹ {total_comm:,.2f}")
    col3.metric("Total Records", f"{len(filtered_df):,}")

    st.subheader("📋 Cleaned Processed Data Table (Bihar)")
    st.dataframe(filtered_df, use_container_width=True)

else:
    st.warning("⚠️ Bihar ka data nahi mila. Kripya check karein.")
