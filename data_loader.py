import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=1200)
def get_data():
    df_trans = conn.read(spreadsheet=sheet_url, worksheet="transactions", ttl=0)
    df_cats = conn.read(spreadsheet=sheet_url, worksheet="categories", ttl=0)

    df_trans['date'] = pd.to_datetime(df_trans['date'], dayfirst=True).dt.date
    
    if not df_trans.empty:
        df_raw = pd.merge(df_trans, df_cats, on='category_id')
        return df_raw
    
    return pd.DataFrame() 

@st.cache_data(ttl=1200)
def get_categories():
    df_cats = conn.read(spreadsheet=sheet_url, worksheet="categories", ttl=0)
    
    if not df_cats.empty:
        return df_cats
    
    return pd.DataFrame() 

def write_row(row):
    df_trans = conn.read(spreadsheet=sheet_url, worksheet="transactions", ttl=0)
    upd = pd.concat([df_trans, row], ignore_index=True)
    try:
        conn.update(worksheet="transactions", data=upd)
        return True
    except Exception as e:
        return False

def update_rows(df_upd, df_cats):
    df_trans = conn.read(spreadsheet=sheet_url, worksheet="transactions", ttl=0)

    cat_map = dict(zip(df_cats['category'], df_cats['category_id']))
    df_upd = df_upd.copy()
    df_upd['category_id'] = df_upd['category'].map(cat_map)

    df_trans = df_trans.set_index('id')
    df_upd = df_upd.set_index('id')
    cols_to_update = ['date', 'amount', 'info', 'category_id']
    df_trans.loc[df_upd.index, cols_to_update] = df_upd[cols_to_update]
    df_trans = df_trans.reset_index()

    df_trans['date'] = pd.to_datetime(df_trans['date'], dayfirst=True).dt.strftime('%d.%m.%Y')

    try:
        conn.update(worksheet="transactions", data = df_trans)
        return True
    except Exception as e:
        return False
    
def delete_rows(ids: list):
    df_trans = conn.read(spreadsheet=sheet_url, worksheet="transactions", ttl=0)
    df_trans = df_trans[~df_trans['id'].isin(ids)]
    try:
        conn.update(worksheet="transactions", data=df_trans)
        return True
    except Exception as e:
        return False

@st.cache_data(ttl=1200)
def get_prods():
    df_ingr = conn.read(spreadsheet=sheet_url, worksheet='ingredients')
    df_rec = conn.read(spreadsheet=sheet_url, worksheet='recipes')
    return df_ingr, df_rec

def save_ingredients(df):
    try:
        conn.update(worksheet="ingredients", data=df)
        return True
    except Exception as e:
        return False

def save_recipes(df):
    try:
        conn.update(worksheet="recipes", data=df)
        return True
    except Exception as e:
        return False

@st.cache_data(ttl=1200)
def get_menu():
    menu = conn.read(spreadsheet=sheet_url, worksheet='menu')
    if not menu.empty:
        return menu
    else:
        return pd.DataFrame(columns=['dish_list'])

def update_menu(menu):
    try:
        conn.update(worksheet='menu', data=menu)
        return True
    except Exception as e:
        return False







    
