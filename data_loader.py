import sqlite3
import streamlit as st
import pandas as pd
from datetime import date
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "manool-kitchen.db")

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# --- Transactions ---

@st.cache_data(ttl=1200)
def get_data():
    with get_conn() as conn:
        df_trans = pd.read_sql("SELECT * FROM transactions", conn)
        df_cats = pd.read_sql("SELECT * FROM categories", conn)
    df_trans['date'] = pd.to_datetime(df_trans['date'], dayfirst=True).dt.date
    df_trans['amount'] = df_trans['amount'].astype(float)
    if not df_trans.empty:
        return pd.merge(df_trans, df_cats, on='category_id')
    return pd.DataFrame()

@st.cache_data(ttl=1200)
def get_categories():
    with get_conn() as conn:
        df = pd.read_sql("SELECT * FROM categories", conn)
    return df if not df.empty else pd.DataFrame()

def write_row(row):
    try:
        with get_conn() as conn:
            row.to_sql("transactions", conn, if_exists='append', index=False)
        return True
    except Exception as e:
        return False

def update_rows(df_upd, df_cats):
    cat_map = dict(zip(df_cats['category'], df_cats['category_id']))
    df_upd = df_upd.copy()
    df_upd['category_id'] = df_upd['category'].map(cat_map)
    df_upd['date'] = pd.to_datetime(df_upd['date'], dayfirst=True).dt.strftime('%d.%m.%Y')
    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            for _, row in df_upd.iterrows():
                cursor.execute("""
                    UPDATE transactions
                    SET date=?, amount=?, info=?, category_id=?
                    WHERE id=?
                """, (row['date'], row['amount'], row['info'], row['category_id'], row['id']))
        return True
    except Exception as e:
        return False

def delete_rows(ids: list):
    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "DELETE FROM transactions WHERE id=?",
                [(i,) for i in ids]
            )
        return True
    except Exception as e:
        return False

# --- Products ---

@st.cache_data(ttl=1200)
def get_prods():
    with get_conn() as conn:
        df_ingr = pd.read_sql("SELECT * FROM ingredients", conn)
        df_rec = pd.read_sql("SELECT * FROM recipes", conn)
    return df_ingr, df_rec

def save_ingredients(df):
    try:
        with get_conn() as conn:
            df.to_sql("ingredients", conn, if_exists='replace', index=False)
        return True
    except Exception as e:
        return False

def save_recipes(df):
    try:
        with get_conn() as conn:
            df.to_sql("recipes", conn, if_exists='replace', index=False)
        return True
    except Exception as e:
        return False

# --- Menu ---

@st.cache_data(ttl=1200)
def get_menu():
    with get_conn() as conn:
        df = pd.read_sql("SELECT * FROM menu", conn)
    return df if not df.empty else pd.DataFrame(columns=['dish_list'])

def update_menu(menu):
    try:
        with get_conn() as conn:
            menu.to_sql("menu", conn, if_exists='replace', index=False)
        return True
    except Exception as e:
        return False

# --- Todos ---

@st.cache_data(ttl=1200)
def get_todos():
    with get_conn() as conn:
        df = pd.read_sql("SELECT * FROM todos", conn)
    return df if not df.empty else pd.DataFrame(columns=['todo_id', 'text', 'date', 'priority', 'author'])

def save_todos(df):
    try:
        with get_conn() as conn:
            df.to_sql("todos", conn, if_exists='replace', index=False)
        return True
    except Exception as e:
        return False



    
