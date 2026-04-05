import streamlit as st
import pandas as pd
from data_loader import get_prods, save_ingredients, save_recipes, get_menu, update_menu

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
                    
    if st.session_state.get('success'):
        st.success("✅ Сохранено!")
        del st.session_state['success']
        
    st.divider()

    st.subheader("🍳 Рецепты")
    new_dish = st.text_input("Название блюда:")
    
    if new_dish.strip():
        exists = new_dish.strip().lower() in df_rec['dish'].str.lower().values
        if exists:
            default_prods = df_rec[df_rec['dish'].str.lower() == new_dish.strip().lower()]['prod_list'].values[0]
            calculated_height = max(100, 50 + (len(default_prods) // 2))
            new_prods = st.text_area("Ингредиенты (через запятую):", value=default_prods, height=calculated_height)
            st.warning(f"**{new_dish}** уже есть в списке.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Удалить рецепт", use_container_width=True):
                    updated = df_rec[df_rec['dish'].str.lower() != new_dish.strip().lower()]
                    if save_recipes(updated):
                        st.cache_data.clear()
                        st.session_state['success'] = True
                        st.rerun()
                    else:
                        st.error("Ошибка удаления!")
            with col2:
                no_changes = default_prods.strip() == new_prods.strip() # type: ignore
                if st.button("📜Изменить рецепт", use_container_width=True, disabled=no_changes):
                    df_rec.loc[df_rec['dish'].str.lower() == new_dish.lower(), 'prod_list'] = new_prods
                    updated = df_rec
                    if save_recipes(updated):
                        st.cache_data.clear()
                        st.session_state['success'] = True
                        st.rerun()
                    else:
                        st.error("Ошибка сохранения!")

        else:
            new_prods = st.text_area("Ингредиенты (через запятую):", height=100)
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

    st.subheader("🔍 Просмотр данных")
    table = st.radio(
            "Источник:",
            ["Ингредиенты", "Рецепты"],
            index=0,
            horizontal=True
        )
    if 'show_recipes' not in st.session_state:
        st.session_state.show_recipes = False

    if st.button("📑 Показать/Скрыть", use_container_width=True):
        st.session_state.show_recipes = not st.session_state.show_recipes
        st.rerun()

    if st.session_state.show_recipes:
        if table == 'Ингредиенты':
            st.dataframe(df_ingr, use_container_width=True, hide_index=True,
                         column_config={"ingr_id": st.column_config.Column(width=10),
                                        "ingr": st.column_config.Column(width="large")})
        else:
            st.dataframe(df_rec, use_container_width=True, hide_index=True)
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

    df_rec_10 = df_rec.sort_values('score_raw', ascending=False).head(10)

    # Блок 1: меню
    st.subheader("📋 Меню")

    menu = get_menu()

    if 'menu' not in st.session_state:
        st.session_state['menu'] = menu['dish_list'].to_list()

    quick_add = st.selectbox(
        "Добавить блюдо в меню:",
        options=[""] + sorted(df_rec['dish'].tolist())
    )
    if quick_add != "":
        if quick_add not in st.session_state['menu']:
            if st.button("➕ Добавить в меню", use_container_width=True):
                st.session_state['menu'].append(quick_add)
                st.rerun()
        else:
            st.info(f"**{quick_add}** добавлен в меню.")


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

    if st.button("📌 Сохранить", use_container_width=True):
        menu = pd.DataFrame({'dish_list': st.session_state['menu']})
        if update_menu(menu):
            st.cache_data.clear()
            st.session_state['success'] = True
            st.rerun()
        else:
            st.error("Ошибка сохранения!")

    if st.session_state.get('success'):
        st.success("✅ Сохранено!")
        del st.session_state['success']

    st.divider()
    # Блок 2: что приготовить?
    st.subheader("🍳 Что можно приготовить")

    def score_emoji(score):
        if score == 1.0:
            return "🟢"
        elif score >= 0.5:
            return "🟡"
        else:
            return "🔴"
    
    for _, row in df_rec_10.iterrows():
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
        if 'checks' not in st.session_state:
            st.session_state['checks'] = set()

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
                dish_label = f" **{ingr.capitalize()}** ({dishes_str})"
                is_checked = st.checkbox(dish_label, key=f"check_{ingr}", value=(ingr in st.session_state['checks']))

                if is_checked:
                    st.session_state['checks'].add(ingr)
                else:
                    st.session_state['checks'].discard(ingr)

        if st.session_state['checks']:
            selected_list = list(st.session_state['checks'])
            if st.button("☑️ Куплено", use_container_width=True):
                last_id = int(df_ingr['ingr_id'].max()) if not df_ingr.empty else 0
                new_rows_list = []
                for i, ingr in enumerate(selected_list):
                    new_rows_list.append({
                        'ingr_id': last_id + 1 + i,
                        'ingr': ingr
                    })
                new_df = pd.DataFrame(new_rows_list)
                upd = pd.concat([df_ingr, new_df], ignore_index=True)

                if save_ingredients(upd):
                    st.session_state.to_buy_checked = set()
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Ошибка!")




