import streamlit as st
import pandas as pd
from datetime import date
from data_loader import get_data, get_categories, update_rows, delete_rows

config_days={
    "date": st.column_config.DateColumn("Дата", format="DD.MM.YYYY"),
    "Расходы": st.column_config.NumberColumn("Расходы", format="%,.2f ₽"),
    "Доходы": st.column_config.NumberColumn("Доходы", format="%,.2f ₽")
}

config_months={
    "Расходы": st.column_config.NumberColumn("Расходы", format="%,.2f ₽"),
    "Доходы": st.column_config.NumberColumn("Доходы", format="%,.2f ₽")
}

config_raw={
    "id": st.column_config.NumberColumn("ID", disabled=True),
    "date": st.column_config.DateColumn("Дата", format="DD.MM.YYYY"),
    "type": st.column_config.SelectboxColumn("Тип", options=[0, 1]),
    "category": st.column_config.TextColumn("Категория"),
    "amount": st.column_config.NumberColumn("Сумма", format="%,.2f ₽"),
    "info": st.column_config.TextColumn("Примечание"),
}

st.markdown("# 📋 Просмотр списка транзакций")

months_list = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

if 'period' in st.session_state:
    period = st.session_state['period']
else:
    period = (date.today().replace(day=1), date.today())

period_choice = st.date_input(
    "Период:",
    value=(period[0], period[1]), 
    format="DD.MM.YYYY",
)

if len(period_choice) != 2:
    st.warning('Выберите конечный период!')
    st.stop()


start_date, end_date = period_choice # type: ignore


# Грузим данные
df_raw = get_data()
df_filt = df_raw[(df_raw['date'] >= start_date) & (df_raw['date'] <= end_date)].copy()

if df_filt.empty:
    st.warning("За этот период транзакций не найдено.")
    st.stop()

st.success(f"Транзакций: {len(df_filt)}")

# View mode
view_mode = st.radio(
    "Отображение:",
    ["Сырые данные", "По дням", "По месяцам"],
    horizontal=True
)

if view_mode == "По дням":
    df_grouped = (
        df_filt.groupby(['date', 'type'])['amount']
        .sum()
        .unstack(fill_value=0)
        .rename(columns={0: 'Расходы', 1: 'Доходы'})
        [['Доходы', 'Расходы']] 
        .reset_index()
        .sort_values('date', ascending=True)
    )
    st.dataframe(df_grouped, use_container_width=True, hide_index=True, column_config=config_days)

elif view_mode == "По месяцам":
    df_m = df_filt.copy()
    df_m['date'] = pd.to_datetime(df_m['date'])
    df_m = df_m.set_index(pd.DatetimeIndex(df_m['date']))

    df_grouped = (
        df_m.groupby([pd.Grouper(freq='MS'), 'type'])['amount']
        .sum()
        .unstack(fill_value=0)
        .rename(columns={0: 'Расходы', 1: 'Доходы'})
        [['Доходы', 'Расходы']] 
        .reset_index()
        .sort_values('date', ascending=True)
    )
    df_grouped['date'] = df_grouped['date'].apply(
        lambda d: f"{months_list[d.month]} {d.year}"
    )

    st.dataframe(df_grouped, use_container_width=True, hide_index=True, column_config=config_months)

else:
    edit_mode = st.toggle("✏️ Режим редактирования")

    display_cols = ['id', 'date', 'type', 'category', 'amount', 'info']
    df_display = df_filt[display_cols].sort_values('id', ascending=True)
    
    if not edit_mode:
        st.dataframe(df_display, use_container_width=True, hide_index=True, column_config=config_raw)
    else:
        df_cats = get_categories()
        cat_options = sorted(df_cats['category'].tolist())

        config_edt={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "date": st.column_config.DateColumn("Дата", format="DD.MM.YYYY"),
            "type": st.column_config.SelectboxColumn("Тип", options=[0, 1]),
            "category": st.column_config.SelectboxColumn("Категория", options=cat_options),
            "amount": st.column_config.NumberColumn("Сумма", min_value=0, step=1, format="%,.2f ₽"),
            "info": st.column_config.TextColumn("Примечание"),
        }

        edited = st.data_editor(
            df_display,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config=config_edt
        )

        if st.button("💾 Сохранить изменения", use_container_width=True):
            # Удаленные
            deleted_ids = list(set(df_display['id']) - set(edited['id']))

            # Изменённые
            df_changed = edited[edited['id'].isin(df_display['id'])]

            success = True
            if deleted_ids:
                success = success and delete_rows(deleted_ids)
            if not df_changed.empty:
                success = success and update_rows(df_changed, df_cats)

            if success:
                st.cache_data.clear()
                st.session_state['success'] = True
                st.rerun()
            else:
                st.error("Ошибка сохранения!")

        if st.session_state.get('success'):
            st.success("✅ Сохранено!")
            del st.session_state['success']
