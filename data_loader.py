import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=1200)
def get_data():
    df_trans = conn.read(spreadsheet=sheet_url, worksheet="transactions")
    df_cats = conn.read(spreadsheet=sheet_url, worksheet="categories")

    df_trans['date'] = pd.to_datetime(df_trans['date'], dayfirst=True).dt.date
    
    if not df_trans.empty:
        df_raw = pd.merge(df_trans, df_cats, on='category_id')
        return df_raw
    
    return pd.DataFrame() 

@st.cache_data(ttl=1200)
def get_categories():
    df_cats = conn.read(spreadsheet=sheet_url, worksheet="categories")
    
    if not df_cats.empty:
        return df_cats
    
    return pd.DataFrame() 

def write_row(row):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_trans = conn.read(spreadsheet=sheet_url, worksheet="transactions", ttl=0)
    upd = pd.concat([df_trans, row], ignore_index=True)
    try:
        conn.update(worksheet="transactions", data=upd)
        return True
    except Exception as e:
        return False

    
