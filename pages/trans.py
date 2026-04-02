import streamlit as st
from datetime import date
from data_loader import get_data, get_categories, write_row
import pandas as pd

st.markdown("# 🧮 Внести транзакцию")

# Подгрузка данных из session_state
if 'period' in st.session_state:
    period = st.session_state['period']
else:
    period = (date.today().replace(day=1), date.today())

df_raw = get_data()
df_filt = df_raw[(df_raw['date']>= period[0]) & (df_raw['date']<= period[1])]

df_in = df_filt[df_filt['type'] == 1]
df_out = df_filt[df_filt['type'] == 0]

cat_in = df_raw[df_raw['type'] == 1]['category'].unique()
cat_out = df_raw[df_raw['type'] == 0]['category'].unique()

type_choice = st.radio(
    "Тип операции:",
    ["Расход 💸", "Доход 💰"],
    horizontal=True,
    index=0 # По умолчанию Расход
)
is_income = type_choice == "Доход 💰"
trans_type = 1 if is_income else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    f_date = st.date_input("Дата:", value=date.today(), format="DD.MM.YYYY")

with col2:
    f_amount = st.number_input("Сумма (₽):", min_value=0.0, step=100.0, value=0.0)

with col3:
    if not is_income:
        f_cat = st.selectbox("Категория:", options=sorted(cat_out))
    else:
        f_cat = st.selectbox("Категория:", options=sorted(cat_in))

with col4:
    f_info = st.text_input("Примечание:", placeholder="Всё для манула")

col1, col2, col3 = st.columns(3)

with col3:
    excluded_cats = st.multiselect(
         "Исключить из рассчёта среднего:",
         options=sorted(cat_out)
    )
df_out = df_out[~df_out['category'].isin(excluded_cats)]    
daily_inc = df_in.pivot_table(values='amount', index = 'date', aggfunc='sum')
daily_exp = df_out.pivot_table(values='amount', index = 'date', aggfunc='sum')

with col1: 
    daily_total = daily_exp['amount'].sum() if not daily_exp.empty else 0
    count = len(daily_exp) if not daily_exp.empty else 1
    avg = daily_total / count
    st.metric("Текущий средний расход:", f"{avg:,.2f} ₽".replace(",", " "))
with col2:
    if f_amount >= 0 and not is_income:
        last_date = date.today() if daily_exp.empty else daily_exp.index[-1]
        if f_date == last_date and f_cat not in excluded_cats:
            daily_total += f_amount
            avg = daily_total / count
            st.metric("Прогнозируемый средний расход:", f"{avg:,.2f} ₽".replace(",", " "))
        elif f_cat in excluded_cats:
            st.metric("Прогнозируемый средний расход:", f"{avg:,.2f} ₽".replace(",", " "))
        else:
            daily_total += f_amount
            count += 1
            avg = daily_total / count
            st.metric("Прогнозируемый средний расход:", f"{avg:,.2f} ₽".replace(",", " "))

if st.button("🚀 Внести!", use_container_width=True):
    df_cats = get_categories()
    cat_map = dict(zip(df_cats['category'], df_cats["category_id"]))
    selected_cat_id = cat_map.get(f_cat)
    
    new_row = pd.DataFrame([{
        "id": int(df_raw['id'].max() + 1) if not df_raw.empty else 1,
        "type": 1 if is_income else 0,
        "date": f_date.strftime('%d.%m.%Y'), # Сохраняем как текст в твоем формате
        "amount": float(f_amount),
        "category_id": int(selected_cat_id), # type: ignore
        "info": f_info
    }])

    if write_row(new_row):
        st.cache_data.clear()
        st.session_state['success'] = True
        st.rerun()
    else:
        st.error('Ошибка отправки!')

if st.session_state.get('success'):
    st.success("✅ Успешно!")
    del st.session_state['success']
    