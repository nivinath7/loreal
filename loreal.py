import streamlit as st
import pandas as pd
import io
from rapidfuzz import process, fuzz

def rule_based_mapping(df_portal, df_catalogue):
    # Ensure both files have the necessary columns
    required_columns = {"ASIN", "New EAN", "VENDOR 8 DIGIT"}
    if not required_columns.issubset(df_portal.columns) or not required_columns.issubset(df_catalogue.columns):
        st.error("Both files must contain 'ASIN', 'New EAN', and 'VENDOR 8 DIGIT' columns.")
        return None
    
    # Merge the portal file with the catalogue file on ASIN, EAN, and VENDOR 8 DIGIT
    df_mapped = pd.merge(df_portal, df_catalogue, on=["ASIN", "New EAN", "VENDOR 8 DIGIT"], how="left")
    return df_mapped

def fuzzy_mapping(df_portal, df_catalogue, threshold=90):
    required_columns = {"ASIN", "New EAN", "VENDOR 8 DIGIT"}
    if not required_columns.issubset(df_portal.columns) or not required_columns.issubset(df_catalogue.columns):
        st.error("Both files must contain 'ASIN', 'New EAN', and 'VENDOR 8 DIGIT' columns.")
        return None
    
    catalogue_entries = df_catalogue[["ASIN", "New EAN", "VENDOR 8 DIGIT"]].values.tolist()
    
    def match_entry(row):
        match = process.extractOne(
            (row["ASIN"], row["New EAN"], row["VENDOR 8 DIGIT"]), 
            catalogue_entries, 
            scorer=fuzz.ratio
        )
        return match[0] if match and match[1] >= threshold else None
    
    df_portal[["Matched ASIN", "Matched New EAN", "Matched VENDOR 8 DIGIT"]] = df_portal.apply(match_entry, axis=1, result_type='expand')
    return df_portal

def main():
    st.title("ASIN, New EAN, and VENDOR 8 DIGIT Mapping Tool")
    st.markdown("""
    **Instructions:**
    1. Upload your daily portal file (containing ASIN, New EAN, and VENDOR 8 DIGIT).
    2. Upload the master catalogue file (mapping ASIN, New EAN, and VENDOR 8 DIGIT).
    3. Choose the mapping method:
       - **Rule-Based:** Performs an exact join on ASIN, New EAN, and VENDOR 8 DIGIT.
       - **Fuzzy Matching:** Uses fuzzy logic (with a threshold) to match records.
    4. Download the mapped file.
    """)

    uploaded_portal_file = st.file_uploader("Upload Portal File", type=["xlsx", "xls", "csv"], key="portal")
    uploaded_catalogue_file = st.file_uploader("Upload Catalogue File", type=["xlsx", "xls", "csv"], key="catalogue")

    mapping_method = st.selectbox("Select Mapping Method", ["Rule-Based", "Fuzzy Matching"])

    if uploaded_portal_file and uploaded_catalogue_file:
        df_portal = pd.read_csv(uploaded_portal_file) if uploaded_portal_file.name.endswith("csv") else pd.read_excel(uploaded_portal_file)
        df_catalogue = pd.read_csv(uploaded_catalogue_file) if uploaded_catalogue_file.name.endswith("csv") else pd.read_excel(uploaded_catalogue_file)

        st.subheader("Portal File Preview")
        st.dataframe(df_portal.head())
        st.subheader("Catalogue File Preview")
        st.dataframe(df_catalogue.head())

        if mapping_method == "Rule-Based":
            df_mapped = rule_based_mapping(df_portal, df_catalogue)
        else:
            threshold = st.slider("Fuzzy Matching Threshold", 50, 100, 90)
            df_mapped = fuzzy_mapping(df_portal, df_catalogue, threshold)

        if df_mapped is not None:
            st.subheader("Mapped Data Preview")
            st.dataframe(df_mapped.head())
            
            # Save the processed data to an Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_mapped.to_excel(writer, index=False, sheet_name="Mapped_Data")
            
            processed_data = output.getvalue()

            st.download_button(
                label="Download Mapped Excel",
                data=processed_data,
                file_name="mapped_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == '__main__':
    main()
