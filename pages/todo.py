import streamlit as st
import pandas as pd
from datetime import date
from data_loader import get_todos, save_todos

st.markdown("# 📌 Заметки")

df_todos = get_todos()

PRIORITY_ORDER = {'Высокий': 0, 'Средний': 1, 'Низкий': 2}
PRIORITY_EMOJI = {'Высокий': '🔴', 'Средний': '🟡', 'Низкий': '🟢'}
AUTHORS = ['Манул', 'Бобёр']
PRIORITIES = ['Высокий', 'Средний', 'Низкий']

# --- Add form ---
with st.expander("➕ Новая заметка", expanded=True):
    new_text = st.text_area("Текст:")
    col1, col2 = st.columns(2)
    with col1:
        new_priority = st.selectbox("Приоритет:", PRIORITIES)
    with col2:
        new_author = st.selectbox("Автор:", AUTHORS)

    if st.button("➕ Добавить", use_container_width=True, disabled=not new_text.strip()):
        new_id = int(df_todos['todo_id'].max()) + 1 if not df_todos.empty else 1
        new_row = pd.DataFrame([{
            'todo_id': new_id,
            'text': new_text.strip(),
            'date': date.today().strftime('%d.%m.%Y'),
            'priority': new_priority,
            'author': new_author
        }])
        upd = pd.concat([df_todos, new_row], ignore_index=True)
        if save_todos(upd):
            st.cache_data.clear()
            st.session_state['todo_success'] = True
            st.rerun()
        else:
            st.error("Ошибка сохранения!")

if st.session_state.get('todo_success'):
    st.success("✅ Заметка добавлена!")
    del st.session_state['todo_success']

st.divider()

# --- Display ---
if df_todos.empty:
    st.info("Заметок пока нет.")
else:
    df_sorted = df_todos.copy()
    df_sorted['priority_order'] = df_sorted['priority'].map(PRIORITY_ORDER)
    df_sorted = df_sorted.sort_values(['priority_order', 'date'], ascending=[True, False])

    for _, row in df_sorted.iterrows():
        emoji = PRIORITY_EMOJI.get(row['priority'], '⚪')
        col1, col2 = st.columns([10, 1])
        with col1:
            st.markdown(f"{emoji} **{row['text']}**")
            st.caption(f"{row['date']} · {row['author']}")
        with col2:
            if st.button("🗑️", key=f"del_todo_{row['todo_id']}"):
                upd = df_todos[df_todos['todo_id'] != row['todo_id']]
                if save_todos(upd):
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Ошибка удаления!")

        st.divider()