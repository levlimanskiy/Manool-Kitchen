import streamlit as st
import pandas as pd
from data_loader import get_prods, save_ingredients, save_recipes

st.markdown("# 🛒 Продукты и рецепты")
df_ingr, df_rec = get_prods()

edit_mode = st.toggle("✏️ Редактирование списка ингредиентов/рецептов")

if edit_mode:
    st.subheader("🥗 Ингредиенты")
    edited_ingr = st.data_editor(
        df_ingr,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "ingr_id": None,
            "ingr": st.column_config.TextColumn("Ингредиент"),
        }
    )
    st.subheader("🍳 Рецепты")
    edited_rec = st.data_editor(
        df_rec,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "rec_id": None,
            "dish": st.column_config.TextColumn("Блюдо"),
            "prod_list": st.column_config.TextColumn("Ингредиенты (через запятую)"),
        }
    )
    if st.button("💾 Сохранить", use_container_width=True):
        ok1 = save_ingredients(edited_ingr)
        ok2 = save_recipes(edited_rec)
        if ok1 and ok2:
            st.cache_data.clear()
            st.session_state['success'] = True
            st.rerun()
        else:
            st.error("Ошибка сохранения!")

    if st.session_state.get('success'):
        st.success("✅ Сохранено!")
        del st.session_state['success']
else:
    available = set(df_ingr['ingr'].str.strip().str.lower())

    def score_recipe(prod_list_str):
        needed = set(p.strip().lower() for p in str(prod_list_str).split(', '))
        if not needed:
            return 0.0, needed
        match = needed & available
        return len(match) / len(needed), needed

    df_rec = df_rec.copy()
    df_rec[['score', 'needed_set']] = pd.DataFrame(
        df_rec['prod_list'].apply(lambda x: pd.Series(score_recipe(x)))
    )

    df_rec = df_rec.sort_values('score', ascending=False).head(10)

    # Блок 1: что приготовить?
    st.subheader("🍳 Что можно приготовить")

    def score_emoji(score):
        if score == 1.0:
            return "🟢"
        elif score >= 0.5:
            return "🟡"
        else:
            return "🔴"

    if 'menu' not in st.session_state:
        st.session_state['menu'] = []
    
    for _, row in df_rec.iterrows():
        col1, col2, col3 = st.columns([1, 6, 2])
        with col1:
            st.write(score_emoji(row['score']))
        with col2:
            st.write(f"**{row['dish']}** — {int(row['score'] * 100)}%")
        with col3:
            if st.button("+ В меню", key=f"add_{row['rec_id']}"):
                if row['dish'] not in st.session_state['menu']:
                    st.session_state['menu'].append(row['dish'])
    
    st.divider()

    # Блок 2: меню
    st.subheader("📋 Меню")
    if not st.session_state['menu']:
        st.info("Меню пусто — добавьте блюда выше.")
    else:
        for dish in st.session_state['menu']:
            col1, col2 = st.columns([8, 1])
            with col1:
                st.write(f"• {dish}")
            with col2:
                if st.button("✕", key=f"del_{dish}"):
                    st.session_state['menu'].remove(dish)
                    st.rerun()

    # Блок 3: список покупок
    st.subheader("🛒 Список покупок")

    if not st.session_state['menu']:
        st.info("Добавьте блюда в меню, чтобы увидеть список покупок.")
    else:
        to_buy = {}
        for dish in st.session_state['menu']:
            row = df_rec[df_rec['dish'] == dish]
            if not row.empty:
                needed = row.iloc[0]['needed_set']
                missing = needed - available
                for ingr in missing:
                    if ingr not in to_buy:
                        to_buy[ingr] = []
                    to_buy[ingr].append(dish)

        if not to_buy:
            st.success("Все ингредиенты уже есть! 🎉")
        else:
            for ingr, dishes in sorted(to_buy.items()):
                dishes_str = ", ".join(dishes)
                st.write(f"• **{ingr.capitalize()}** ({dishes_str})")


