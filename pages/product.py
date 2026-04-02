import streamlit as st
import pandas as pd
from data_loader import get_prods, save_ingredients, save_recipes

st.markdown("# 🛒 Продукты и рецепты")
df_ingr, df_rec = get_prods()

edit_mode = st.toggle("✏️ Редактирование списка ингредиентов/рецептов")

if edit_mode:
    st.subheader("🥗 Ингредиенты")
    new_ingr = st.text_input("Новый ингредиент:")
    on_list = False
    if new_ingr.strip():
        if new_ingr.strip().lower() in df_ingr['ingr'].str.lower().values:
            st.warning(f"**{new_ingr}** уже есть в списке.")
            if st.button("🗑️ Удалить ингредиент", use_container_width=True):
                updated = df_ingr[df_ingr['ingr'].str.lower() != new_ingr.strip().lower()]
                if save_ingredients(updated):
                    st.cache_data.clear()
                    st.session_state['success'] = True
                    st.rerun()
                else:
                    st.error("Ошибка удаления!")
        else:
            st.success(f"**{new_ingr}** можно добавить.")
            if st.button("➕ Добавить ингредиент", use_container_width=True):
                new_id = int(df_ingr['ingr_id'].max()) + 1
                new_row = pd.DataFrame([{'ingr_id': new_id, 'ingr': new_ingr.strip()}])
                updated = pd.concat([df_ingr, new_row], ignore_index=True)
                if save_ingredients(updated):
                    st.cache_data.clear()
                    st.session_state['success'] = True
                    st.rerun()
                else:
                    st.error("Ошибка сохранения!")
    st.divider()

    st.subheader("🍳 Рецепты")
    new_dish = st.text_input("Название блюда:")
    new_prods = st.text_input("Ингредиенты (через запятую):")
    if new_dish.strip():
        exists = new_dish.strip().lower() in df_rec['dish'].str.lower().values
        if exists:
            st.warning(f"**{new_dish}** уже есть в списке.")
            if st.button("🗑️ Удалить рецепт", use_container_width=True):
                updated = df_rec[df_rec['dish'].str.lower() != new_dish.strip().lower()]
                if save_recipes(updated):
                    st.cache_data.clear()
                    st.session_state['success'] = True
                    st.rerun()
                else:
                    st.error("Ошибка удаления!")
        else:
            if not new_prods.strip():
                st.warning("Напишите список ингредиентов!")
            else:
                st.success(f"**{new_dish}** можно добавить.")
                if st.button("➕ Добавить рецепт", use_container_width=True):
                    new_id = int(df_rec['rec_id'].max()) + 1
                    new_row = pd.DataFrame([{'rec_id': new_id, 'dish': new_dish.strip(), 'prod_list': new_prods.strip()}])
                    updated = pd.concat([df_rec, new_row], ignore_index=True)
                    if save_recipes(updated):
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
        return f"{len(match)} / {len(needed)}", len(match) / len(needed), needed

    df_rec = df_rec.copy()
    df_rec[['score', 'score_raw', 'needed_set']] = pd.DataFrame(
        df_rec['prod_list'].apply(lambda x: pd.Series(score_recipe(x)))
    )

    df_rec = df_rec.sort_values('score_raw', ascending=False).head(10)

    # Блок 1: меню
    st.subheader("📋 Меню")

    if 'menu' not in st.session_state:
        st.session_state['menu'] = []

    quick_add = st.selectbox(
        "Добавить блюдо в меню:",
        options=["—"] + sorted(df_rec['dish'].tolist()),
    )
    if quick_add != "—":
        if quick_add not in st.session_state['menu']:
            if st.button("➕ Добавить в меню", use_container_width=True):
                st.session_state['menu'].append(quick_add)
                st.rerun()
        else:
            st.info(f"**{quick_add}** уже в меню.")

    if not st.session_state['menu']:
        st.info("Меню пусто — добавьте блюда.")
    else:
        for dish in st.session_state['menu']:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"• **{dish.upper()}**")
            with col2:
                if st.button("✕", key=f"del_{dish}"):
                    st.session_state['menu'].remove(dish)
                    st.rerun()

    # Блок 2: что приготовить?
    st.subheader("🍳 Что можно приготовить")

    def score_emoji(score):
        if score == 1.0:
            return "🟢"
        elif score >= 0.5:
            return "🟡"
        else:
            return "🔴"
    
    for _, row in df_rec.iterrows():
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"{score_emoji(row['score_raw'])} **{row['dish'].capitalize()}** — {row['score']}")
        with col2:
            if st.button("+ В меню", key=f"add_{row['rec_id']}"):
                if row['dish'] not in st.session_state['menu']:
                    st.session_state['menu'].append(row['dish'])
                    st.rerun()
    
    st.divider()

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


