import streamlit as st
import pandas as pd
from datetime import date
import calendar
import locale
from data_loader import get_data
import plotly.express as px
import plotly.graph_objects as go

locale.setlocale(locale.LC_TIME, 'ru_RU')

st.markdown("# Сведения о бюджете 🏠")

today = date.today()
month_options = []
for i in range(9):
    d = today.replace(day=1)
    month_name = f"{calendar.month_name[d.month]} {d.year}"
    month_options.append((month_name, d.year, d.month))
    if d.month == 1:
        today = d.replace(year=d.year-1, month=12)
    else:
        today = d.replace(day=1, month=d.month-1)

if 'month' in st.session_state:
    cindex = month_options.index(st.session_state['month'])
else:
    cindex = 0
    
res = st.selectbox(
    "Месяц:",
    month_options,
    cindex,
    format_func=lambda x: x[0]
) # type: ignore

st.session_state['month'] = res

selected_month_label, sel_year, sel_month = res # type: ignore

first_day = date(sel_year, sel_month, 1)
last_day = date(sel_year, sel_month, calendar.monthrange(sel_year, sel_month)[1])

st.session_state['month'] = (selected_month_label, sel_year, sel_month)

# Виджет календаря
period = st.date_input(
    "Точный период:",
    value=(first_day, last_day), 
    format="DD.MM.YYYY",
)

# Проверка: выбрал ли пользователь обе даты
if isinstance(period, tuple) and len(period) == 2:
    start_date, end_date = period
    st.session_state['period'] = period

    df_raw = get_data()
    df_filt = df_raw[(df_raw['date']>= start_date) & (df_raw['date']<= end_date)]

    df_in = df_filt[df_raw['type'] == 1]
    df_out = df_filt[df_raw['type'] == 0]

    if not df_filt.empty:
        st.success(f"Транзакций: {len(df_filt)}")

        # Блок 1: Итоги
        inc = df_in['amount'].sum()
        exp = df_out['amount'].sum()
        savings = inc - exp
        col1, col2, col3 = st.columns(3)
        with col1:
            formatted_inc = f"{inc:,.0f} ₽".replace(",", " ")
            st.metric("Доходы", formatted_inc)

        with col2:
            formatted_exp = f"{exp:,.0f} ₽".replace(",", " ")
            st.metric("Расходы", formatted_exp)

        with col3:
            res_label = "остаток" if savings >= 0 else "перерасход"
            res_color = "normal" if savings >= 0 else "inverse"
            formatted_savings = f"{savings:,.0f} ₽".replace(",", " ")
            st.metric("Остаток / Накопления", formatted_savings, delta=res_label, delta_color=res_color)

        group_choice = st.radio(
            "Группировать данные:",
            ["По дням", "По месяцам", "По годам"],
            index=0,
            horizontal=True
        )

        group_map = {
            "По дням": "D",
            "По месяцам": "MS",
            "По годам": "YS"
        }

        df_in_plot = df_in.copy()
        df_in_plot['date'] = pd.to_datetime(df_in_plot['date'])
        df_out_plot = df_out.copy()
        df_out_plot['date'] = pd.to_datetime(df_out_plot['date'])        

        per_inc = df_in_plot.set_index('date').resample(group_map[group_choice])['amount'].sum().reset_index()
        per_exp = df_out_plot.set_index('date').resample(group_map[group_choice])['amount'].sum().reset_index()

        # Блок 2: график бюджета
        st.subheader("📈 Динамика бюджета")
        all_pers = pd.date_range(start_date, end_date, freq=group_map[group_choice])
        df_pers = pd.DataFrame({'date': all_pers})
        df_plot = df_pers.merge(per_inc, on='date', how='left').rename(columns={'amount': 'inc'})
        df_plot = df_plot.merge(per_exp, on='date', how='left').rename(columns={'amount': 'exp'})
        df_plot = df_plot.fillna(0)
        df_plot['inc_cum'] = df_plot['inc'].cumsum()
        df_plot['exp_cum'] = df_plot['exp'].cumsum()
        fig_cum = go.Figure()
        # Линия доходов
        fig_cum.add_trace(go.Scatter(
            x=df_plot['date'], y=df_plot['inc_cum'],
            name='Доходы (нак.)', line=dict(color='green', width=3),
            mode='lines+markers'
        ))
        # Линия расходов
        fig_cum.add_trace(go.Scatter(
            x=df_plot['date'], y=df_plot['exp_cum'],
            name='Расходы (нак.)', line=dict(color='red', width=3),
            mode='lines+markers'
        ))
        fig_cum.update_layout(
            hovermode="x unified", # Показывает обе суммы при наведении на дату
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_cum, use_container_width=True)

        st.divider()
      
        # Блок 3: график расходов
        st.subheader("📈 Динамика расходов")
        fig = px.line(
            per_exp, 
            x='date', 
            y='amount',
            markers=True,        # Включаем точки
            text='amount',       # Данные для подписей
            line_shape='spline', # Делаем линию плавной (опционально)
            color_discrete_sequence=['#FF4B4B'] # Фирменный красный Streamlit
        )
        fig.update_traces(
            texttemplate='%{text:,.0f} ₽', # Формат: 10 500 ₽
            textposition='top center',      # Подпись над точкой
            textfont=dict(size=12),
            cliponaxis=False                # Чтобы крайние подписи не обрезались
        )
        fig.update_layout(
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(t=30, b=0, l=0, r=0),
            hovermode="x unified", # При наведении показывает данные за весь день
            yaxis=dict(showgrid=True, gridcolor='LightGray', zeroline=False),
            xaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Блок 4: круговая диаграмма категорий
        st.subheader("🍕 Распределение трат")
        cat_exp = df_out.groupby('category')['amount'].sum().reset_index()
        cat_exp = cat_exp.sort_values(by='amount', ascending=True) # Asc=True для красивого топа на графике

        fig = px.bar(
            cat_exp,
            x='amount',
            y='category',
            orientation='h', # Делаем горизонтальным
            text='amount',   # Добавляем числа на столбцы
            labels={'amount': 'Сумма', 'category': 'Категория'},
            color='amount',  # Цветовой градиент в зависимости от суммы
            color_continuous_scale='RdBu'
        )

        # Тонкая настройка внешнего вида
        fig.update_traces(
            texttemplate='%{text:,.0f} ₽', # Формат валюты
            textposition='outside',        # Выносим цифры за пределы столбца
            cliponaxis=False               # Чтобы цифры не обрезались
        )

        fig.update_layout(
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
            coloraxis_showscale=False,     # Прячем шкалу градиента (она тут лишняя)
            margin=dict(t=0, b=0, l=0, r=50), # Запас справа для подписей
            height=400 + (len(cat_exp) * 20)  # Динамическая высота под кол-во категорий
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("За этот период трат не найдено.")

else:
    st.info("Пожалуйста, выберите вторую дату в календаре (конечную).")