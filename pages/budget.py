import streamlit as st
import pandas as pd
from datetime import date
import calendar
from data_loader import get_data
import plotly.express as px
import plotly.graph_objects as go

st.markdown("# 🏠 Сведения о бюджете")

today = date.today()
months_list = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]
month_options = []
d = today.replace(day=1)
for i in range(9):
    label = f"{months_list[d.month]} {d.year}"
    month_options.append((label, d.year, d.month))
    if d.month == 1:
        d = d.replace(year=d.year-1, month=12)
    else:
        d = d.replace(month=d.month - 1)
    
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
    df_filt['date'] = pd.to_datetime(df_filt['date'])

    df_in = df_filt[df_filt['type'] == 1]
    df_out = df_filt[df_filt['type'] == 0]

    if not df_filt.empty:
        st.success(f"Транзакций: {len(df_filt)}")

        # Блок 1: Итоги
        inc = df_in['amount'].sum()
        exp = df_out['amount'].sum()
        savings = inc - exp
        col1, col2, col3 = st.columns(3)
        with col1:
            formatted_inc = f"{inc:,.2f} ₽".replace(",", " ")
            st.metric("Доходы", formatted_inc)

        with col2:
            formatted_exp = f"{exp:,.2f} ₽".replace(",", " ")
            st.metric("Расходы", formatted_exp)

        with col3:
            res_label = "остаток" if savings >= 0 else "перерасход"
            res_color = "normal" if savings >= 0 else "inverse"
            formatted_savings = f"{savings:,.2f} ₽".replace(",", " ")
            st.metric("Остаток / Накопления", formatted_savings, delta=res_label, delta_color=res_color)

        # Выбор группировки
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
        freq = group_map[group_choice]
        if freq == 'D':
            bar_caption = 'D1'
        else:
            bar_caption = 'M1'

        df_in_plot = df_in.copy()
        df_out_plot = df_out.copy()    

        per_inc = df_in_plot.set_index('date').resample(freq)['amount'].sum().reset_index()
        per_exp = df_out_plot.set_index('date').resample(freq)['amount'].sum().reset_index()

        # Блок 2: график бюджета
        st.subheader("📈 Динамика бюджета")
        all_pers = pd.date_range(start_date, end_date, freq=freq)
        df_pers = pd.DataFrame({'date': all_pers})
        df_plot = df_pers.merge(per_inc, on='date', how='left').rename(columns={'amount': 'inc'})
        df_plot = df_plot.merge(per_exp, on='date', how='left').rename(columns={'amount': 'exp'})
        df_plot = df_plot.fillna(0)

        df_plot = per_inc.rename(columns={'amount': 'inc'}).merge(
            per_exp.rename(columns={'amount': 'exp'}),
            on='date', how='outer'
        ).fillna(0).sort_values('date')

        df_plot['inc_cum'] = df_plot['inc'].cumsum()
        df_plot['exp_cum'] = df_plot['exp'].cumsum()

        fig_cum = go.Figure()
        # Новый
        fig_cum.add_trace(go.Scatter(
            x=df_plot['date'], 
            y=df_plot['inc_cum'],
            name='Доходы (нак.)',
            mode='lines',              # Убираем маркеры, чтобы не рябило
            line=dict(color='#2E7D32', width=4, shape='spline'), # Темно-зеленый, плавный
            fill='tozeroy',            # Заливка до нуля
            fillcolor='rgba(46, 125, 50, 0.1)' # Очень прозрачный зеленый
        ))

        # Линия расходов (с заливкой)
        fig_cum.add_trace(go.Scatter(
            x=df_plot['date'], 
            y=df_plot['exp_cum'],
            name='Расходы (нак.)',
            mode='lines',
            line=dict(color='#D32F2F', width=4, shape='spline'), # Насыщенный красный
            fill='tozeroy',
            fillcolor='rgba(211, 47, 47, 0.1)' # Очень прозрачный красный
        ))

        fig_cum.update_layout(
            plot_bgcolor='white',
            hovermode="x unified",
            # Настройка легенды сверху
            legend=dict(
                orientation="h", 
                yanchor="bottom", 
                y=1.05, 
                xanchor="center", 
                x=0.5,
                font=dict(size=12)
            ),
            xaxis=dict(
                type = 'date',
                showgrid=False,
                linecolor='#D0D0D0',
                dtick=bar_caption,
                tickformat='%d %b',
                tickmode = 'linear'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#F0F2F6',
                ticksuffix=' ₽',
                tickformat=',.0f',
                zeroline=False
            ),
            margin=dict(t=80, b=60, l=75, r=20), # Больше места для легенды
            font=dict(family="sans-serif", size=14)
        )
        st.image(fig_cum.to_image(format="png", scale=3))

        st.divider()

        # Блок 3: график расходов
        st.subheader("📊 Динамика расходов")
        fig = px.bar(
            per_exp,
            x='date',
            y='amount',
            text_auto=',.2f' # type: ignore
        )
        fig.update_traces(
            marker_color="#98CBE2",
            marker_line_width=0,
            opacity=0.85,
            textfont=dict(
                family="sans-serif",      
                size=18,            
                color="black",       
                weight="bold"        
            ),
            cliponaxis=False 
        )
        fig.update_layout(
            plot_bgcolor='white',
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(t=30, b=50, l=80, r=0),
            yaxis=dict(
                showgrid=True, 
                gridcolor='#F0F2F6', 
                zeroline=False,
                tickformat=',',
                ticksuffix=' ₽',
                showticklabels=True,
                range=[0, per_exp['amount'].max() * 1.2] 
            ),
            xaxis=dict(
                type='date',
                dtick=bar_caption,
                linecolor='#F0F2F6', 
                tickformat='%d %b',
                tickmode="linear",
                showgrid=False
            ),
            font=dict(size=13, family="sans-serif"),
            bargap=0.3
        )
        st.image(fig.to_image(format="png", scale=3))

        st.divider()

        # Блок 4: круговая диаграмма категорий
        st.subheader("🍕 Распределение трат")
        cat_exp = df_out.groupby('category')['amount'].sum().reset_index()
        cat_exp = cat_exp.sort_values(by='amount', ascending=True) # Asc=True для красивого топа на графике

        fig = px.bar(
            cat_exp,
            x='amount',
            y='category',
            orientation='h', 
            text='amount',   
            labels={'amount': 'Сумма', 'category': 'Категория'},
            color='amount',  
            color_continuous_scale='RdBu'
        )
        fig.update_traces(
            texttemplate='%{text:,.2f} ₽',
            textposition='outside',       
            cliponaxis=False             
        )
        fig.update_layout(
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
            coloraxis_showscale=False,     
            margin=dict(t=0, b=0, l=165, r=65),
            height=400 + (len(cat_exp) * 20) 
        )
        st.image(fig.to_image(format="png", scale=3))

        st.divider()

        # Блок 5: обеды на работе, бесплатные дни
        st.subheader("Дополнительны сведения 🧾")

        df_lunch = df_out[df_out['info'] == 'Столовая (работа)']
        sum_lunch = df_lunch['amount'].sum()
        avg_lucn = df_lunch['amount'].sum() / len(df_lunch)
        formatted_sum_lunch = f"{sum_lunch:,.2f} ₽".replace(",", " ")
        formatted_avg_lunch = f"{avg_lucn:,.2f} ₽".replace(",", " ")
        
        df_free = df_out[df_out['info'] == 'Бесплатный день']
        сount_free = len(df_free)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Сумма на обеды:", formatted_sum_lunch)
        with col2:
            st.metric("Средний чек за обед:", formatted_avg_lunch)
        with col3:
            st.metric("Количество бесплатных дней:", сount_free)

    else:
        st.warning("За этот период трат не найдено.")

else:
    st.info("Пожалуйста, выберите вторую дату в календаре (конечную).")