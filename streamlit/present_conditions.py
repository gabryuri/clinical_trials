import streamlit as st
import duckdb
import pandas as pd

# Streamlit App Setup
st.title('LLm processed data')

con = duckdb.connect(database='airflow/db/duckdb.db')

query = """SELECT * FROM 
    clinical_trials_processed.dim_conditions_processed  
    where condition_term_raw != condition_term_processed"""

@st.cache_data(ttl=10)  
def fetch_data():
    result_df = con.execute(query).df()
    return result_df


data = fetch_data()
st.write('Data:')
st.dataframe(data)

con.close()
