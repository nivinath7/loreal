import streamlit as st
import pandas as pd
import io

# Streamlit Page Configuration
st.set_page_config(page_title="Excel Modification", layout="wide")

# Sidebar: Model Selection & Settings
st.sidebar.header("Settings")
selected_model = st.sidebar.selectbox("Select Model:", ["llama-3.3-70b-versatile","deepseek-r1-distill-llama-70b"])

temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.3)
max_context_length = st.sidebar.number_input("Max Context Length (tokens):", 1000, 8000, 3000)
retrieve_mode = st.sidebar.selectbox("Retrieve Mode:", ["Text (Hybrid)", "Vector Only", "Text Only"])

# Page Header
st.header("Excel Modification")

# File Uploader
uploaded_excel = st.file_uploader("Upload Excel File:", type="xlsx")

# Function to validate if mentioned columns exist
def validate_columns_exist(df, command):
    parts = command.split(":")
    if len(parts) > 1:
        columns = [col.strip() for col in parts[1].split(",")]
        missing_columns = [col for col in columns if col not in df.columns]
        if missing_columns:
            st.error(f"Error: The following columns are missing: {', '.join(missing_columns)}")
            return False
    return True

# Function to apply transformations based on user command
def process_excel(df, command):
    try:
        if "remove empty rows" in command.lower():
            df.dropna(how="all", inplace=True)
        elif "add column" in command.lower():
            col_name = command.split("add column")[-1].strip()
            df[col_name] = "New Data"
        elif "drop column" in command.lower():
            col_name = command.split("drop column")[-1].strip()
            if col_name in df.columns:
                df.drop(columns=[col_name], inplace=True)
        elif "filter rows where" in command.lower():
            condition = command.split("filter rows where")[-1].strip()
            df.query(condition, inplace=True)
        elif "rename column" in command.lower():
            old_name, new_name = command.split("rename column")[-1].strip().split(" to ")
            df.rename(columns={old_name.strip(): new_name.strip()}, inplace=True)
        elif "replace" in command.lower():
            parts = command.split("replace")[-1].strip().split(" with ")
            old_value, new_value = parts[0].strip(), parts[1].strip()
            df.replace(old_value, new_value, inplace=True)
        elif "check columns" in command.lower():
            if not validate_columns_exist(df, command):
                return df
        else:
            st.warning("Command not recognized. Please use structured instructions like 'remove empty rows' or 'rename column A to B'.")
    except Exception as e:
        st.error(f"Error processing the request: {str(e)}")
    return df

if uploaded_excel:
    df = pd.read_excel(uploaded_excel)
    custom_command = st.text_input("Enter your command:")
    
    if st.button("Submit"):
        df = process_excel(df, custom_command)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        
        st.download_button("Download Modified Excel File", output, "modified_file.xlsx")
