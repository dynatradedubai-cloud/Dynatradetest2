st.write("### Search for Parts")

search_term = st.text_input("Enter Part Number (Reference / Manufacturing / OE)", key="search_box")
check_search = st.button("Check", key="check_button")

df = st.session_state['price_df']

if check_search and search_term:
    st.session_state['search_results'] = df[df.apply(
        lambda row: search_term.lower() in str(row.values).lower(),
        axis=1
    )]

if 'search_results' in st.session_state and not st.session_state['search_results'].empty:
    results = st.session_state['search_results']
    st.write("### Matching Parts")

    header_cols = st.columns(len(results.columns) + 2)
    for i, col_name in enumerate(results.columns):
        header_cols[i].write(col_name)
    header_cols[-2].write("Required Qty.")
    header_cols[-1].write("Add to Cart")

    for idx, row in results.iterrows():
        cols = st.columns(len(row) + 2)
        for i, val in enumerate(row):
            cols[i].write(val)

        qty = cols[-2].number_input("Qty", min_value=1, value=1, key=f"qty_{idx}")
        if cols[-1].button("Add", key=f"add_{idx}"):
            item = row.to_dict()
            if 'Unit Price' in item:
                item['Unit Price'] = round(float(item['Unit Price']), 2)
            item['Required Qty'] = qty
            st.session_state['cart'].append(item)

elif check_search:
    st.warning("No matching parts found.")
