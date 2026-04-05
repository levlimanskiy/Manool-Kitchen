import streamlit as st

st.set_page_config(page_title="Бюджет Манулиного Домохозяйства", page_icon="📈")

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.markdown("# 🔐 Вход")
    password = st.text_input("Пароль:", type="password")
    if st.button('Войти'):
        if password == st.secrets["auth"]["password"]:
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("Неверный пароль!")
    st.navigation([st.Page("pages/budget.py", title="Бюджет", icon="🏠")], position="hidden")
    st.stop()

with st.sidebar:
    st.markdown("### 🔄 Данные")
    if st.button("Обновить из базы", use_container_width=True):
        st.cache_data.clear()
        st.success("Обновлено!")
        st.rerun()
    st.divider()

# Define the pages
budget = st.Page("pages/budget.py", title="Бюджет", icon="🏠")
trans = st.Page("pages/trans.py", title="Внести транзакцию", icon="🧮")
table = st.Page("pages/table.py", title="Список транзакций", icon="📋")
product = st.Page("pages/product.py", title="Продукты", icon = "🛒")

# Set up navigation
pg = st.navigation([budget, trans, table, product])

# Run the selected page
pg.run()