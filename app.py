import streamlit as st
import pandas as pd

def read_excel(file):
    try:
        return pd.read_excel(file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def clean_data(df, column_name):
    return df.drop_duplicates(subset=column_name)

def compare_data(df1, df2, id_column, compare_columns, additional_columns):
    columns_df1 = [id_column] + compare_columns
    columns_df2 = [id_column] + compare_columns + [col for col in additional_columns if col != 'Reason']

    # Merge the two dataframes on the ID column with appropriate suffixes
    merged_df = pd.merge(df1[columns_df1], df2[columns_df2], on=id_column, suffixes=('_old', '_new'))

    # Initialize an empty DataFrame for changed data
    changed_data = pd.DataFrame()

    # Iterate over each compare_column to detect changes
    for col in compare_columns:
        old_col = col + '_old'
        new_col = col + '_new'

        # Detect changes and append to changed_data DataFrame
        changes = merged_df[merged_df[old_col] != merged_df[new_col]]
        if not changes.empty:
            changed_data = pd.concat([changed_data, changes])

    # Drop duplicate rows based on the ID column
    changed_data = changed_data.drop_duplicates(subset=id_column)

    # Rename columns for readability
    renamed_columns = {id_column: 'ASN', **{col+'_old': 'Old ' + col for col in compare_columns}, **{col+'_new': 'New ' + col for col in compare_columns}}
    result_df = changed_data.rename(columns=renamed_columns).copy()

    # Add additional columns that are present in both dataframes
    for col in additional_columns:
        if col in df1.columns and col in df2.columns and col != 'Reason':
            result_df[col] = merged_df[col]

        if col == 'Nupco PO No':
                result_df[col] = result_df[col].astype(str).str.replace(',', '')

    # Map 'Reason' column from the second dataframe (df2)
    if 'Reason' in df2.columns:
        reason_map = df2.set_index(id_column)['Reason']
        result_df['Reason'] = result_df['ASN'].map(reason_map)

    # Reordering columns
    old_new_columns = ['Old ' + col for col in compare_columns] + ['New ' + col for col in compare_columns]
    reordered_columns = ['ASN'] + [col for col in additional_columns if col != 'Reason' and col in df1.columns and col in df2.columns] + old_new_columns + ['Reason']
    result_df = result_df[reordered_columns]

    return result_df

def st_set_table_width():
    st.markdown(
        """
        <style>
        .dataframe th, .dataframe td {
            white-space: nowrap;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def main():
    st_set_table_width()
    st.title(":floppy_disk: Excel Comparison App")
    st.markdown("##")

    file1 = st.file_uploader("Upload :red[OLD] Excel file:", type=['xlsx'])
    file2 = st.file_uploader("Upload :green[NEWEST] Excel file:", type=['xlsx'])

    if file1 and file2:
        df1, df2 = read_excel(file1), read_excel(file2)
        if df1 is not None and df2 is not None:
            df1_cleaned = clean_data(df1, 'Request ID')
            df2_cleaned = clean_data(df2, 'Request ID')

            id_column = 'Request ID'
            additional_columns_delivery = ['Nupco PO No', 'Shipped to Location']
            additional_columns_status = ['Nupco PO No', 'Shipped to Location', 'Reason']  # Include 'Reason' here

            delivery_changes = compare_data(df1_cleaned, df2_cleaned, id_column, ['Delivery Date'], additional_columns_delivery)
            status_changes = compare_data(df1_cleaned, df2_cleaned, id_column, ['Request Status'], additional_columns_status)
            if not delivery_changes.empty:
                st.markdown("""---""")
                st.markdown(''':blue[Changes in Delivery Dates:]''')
                st.dataframe(delivery_changes, hide_index=True)
            else:
                st.success("No changes in Delivery Dates found.")

            if not status_changes.empty:
                st.markdown("""---""")
                st.markdown(''':blue[Changes in Request Status:]''')
                st.dataframe(status_changes, hide_index=True)
            else:
                st.success("No changes in Request Status found.")
    else:
        st.info("Please upload both Excel files to proceed.")

if __name__ == "__main__":
    main()
