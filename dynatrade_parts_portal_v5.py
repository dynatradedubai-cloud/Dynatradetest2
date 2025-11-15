import streamlit as st
import pandas as pd
import datetime
import base64
import requests

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Dynatrade Parts Portal", layout="wide")

# ---------------- MULTIPAGE NAVIGATION ----------------
page = st.sidebar.radio("Navigate", ["Dynatrade – Customer Portal", "Admin Portal"])

# ---------------- SESSION STATE ----------------
if 'cart' not in st.session_state:
    st.session_state['cart'] = []
if 'price_df' not in st.session_state:
    st.session_state['price_df'] = None
if 'campaign_file' not in st.session_state:
    st.session_state['campaign_file'] = None
if 'users_df' not in st.session_state:
    st.session_state['users_df'] = pd.DataFrame(columns=['Username', 'Password', 'IP'])
if 'admin_logged_in' not in st.session_state:
    st.session_state['admin_logged_in'] = False
if 'customer_logged_in' not in st.session_state:
    st.session_state['customer_logged_in'] = False
if 'customer_username' not in st.session_state:
    st.session_state['customer_username'] = ""

# Function to get real client IP using ipify
@st.cache_data(show_spinner=False)
def get_client_ip():
    try:
        return requests.get('https://api.ipify.org').text
    except:
        return 'UNKNOWN'

# ---------------- CUSTOMER PORTAL ----------------
if page == "Dynatrade – Customer Portal":
    st.title("Dynatrade – Customer Portal")

    if not st.session_state['customer_logged_in']:
        with st.form("login_form"):
            username = st.text_input("Customer Username")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")

        if submit_login:
            if not st.session_state['users_df'].empty:
                user_row = st.session_state['users_df'][
                    (st.session_state['users_df']['Username'] == username) &
                    (st.session_state['users_df']['Password'] == password)
                ]
                if not user_row.empty:
                    client_ip = get_client_ip()
                    if client_ip in user_row['IP'].values:
                        st.session_state['customer_logged_in'] = True
                        st.session_state['customer_username'] = username
                        st.success("Login Successful")
                    else:
                        st.error(f"Access denied: IP {client_ip} not allowed")
                else:
                    st.error(f"Invalid username or password (IP: {get_client_ip()})")
            else:
                st.warning("User credentials file not loaded.")
    else:
        st.success(f"Welcome, {st.session_state['customer_username']}!")

        # Campaign file download
        if st.session_state['campaign_file']:
            st.write("### Special Campaign")
            file_name, file_bytes = st.session_state['campaign_file']
            b64 = base64.b64encode(file_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">Download Campaign File</a>'
            st.markdown(href, unsafe_allow_html=True)

        # Price list search
        if st.session_state['price_df'] is not None:
            st.write("### Search for Parts")
            search_term = st.text_input("Enter Part Number (Reference / Manufacturing / OE)")
            check_search = st.button("Check")  # ✅ Added Check button

            df = st.session_state['price_df']

            # ✅ Persist search results in session state
            if check_search and search_term:
                st.session_state['search_results'] = df[df.apply(lambda row: search_term.lower() in str(row.values).lower(), axis=1)]

            # ✅ Display results if available
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

        # Cart display
        st.write("### Your Cart")
        if st.session_state['cart']:
            cart_df = pd.DataFrame(st.session_state['cart'])
            if 'Unit Price' in cart_df.columns:
                cart_df['Unit Price'] = cart_df['Unit Price'].apply(lambda x: f"{float(x):.2f}")
            st.dataframe(cart_df)

            st.markdown("""
            Send your requirement in **Business WhatsApp** - https://wa.me/+97165132219?text=Inquiry  
            **OR Email to Sales Man** - 52etrk51@dynatradegroup.com  
            **OR Contact Sales Man** – Mr. Binay +971 50 4815087
            """)

            if st.button("Clear Cart"):
                st.session_state['cart'] = []
                st.session_state.pop('search_results', None)  # ✅ Clear matching parts
                st.success("Cart and search results cleared successfully!")
        else:
            st.write("Cart is empty.")

        if st.button("Logout"):
            st.session_state['customer_logged_in'] = False
            st.session_state['customer_username'] = ""
            st.success("Logged out successfully!")

# ---------------- ADMIN PORTAL ----------------
if page == "Admin Portal":
    st.title("Admin Portal")

    if not st.session_state['admin_logged_in']:
        with st.form("admin_login_form"):
            admin_user = st.text_input("Admin Username")
            admin_pass = st.text_input("Password", type="password")
            submit_admin = st.form_submit_button("Login")

        if submit_admin and admin_user == "admin" and admin_pass == "admin123":
            st.session_state['admin_logged_in'] = True
            st.success("Admin Login Successful")
    else:
        st.success("Admin Logged In")

    # Upload Price List
    st.write("### Upload Price List")
    price_file = st.file_uploader("Upload Price List", type=["xlsx", "xls", "csv"])
    if price_file:
        try:
            if price_file.name.endswith(".csv"):
                df = pd.read_csv(price_file, encoding="latin1")
            elif price_file.name.endswith(".xlsx"):
                df = pd.read_excel(price_file, engine="openpyxl")
            else:
                df = pd.read_excel(price_file, engine="xlrd")
            st.session_state['price_df'] = df
            st.session_state['price_upload_time'] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            st.success("Price List uploaded successfully!")
        except Exception as e:
            st.error(f"Error reading file: {e}")

    if 'price_upload_time' in st.session_state:
        st.write(f"Last uploaded: {st.session_state['price_upload_time']}")

    # Upload Campaign File
    st.write("### Upload Campaign File")
    campaign_file = st.file_uploader("Upload Campaign File", type=["xlsx","xls","csv","pdf","png","jpeg","jpg","doc","docx"])
    if campaign_file:
        st.session_state['campaign_file'] = (campaign_file.name, campaign_file.read())
        st.session_state['campaign_upload_time'] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        st.success("Campaign File uploaded successfully! It will be visible to customers as a download link.")

    if 'campaign_upload_time' in st.session_state:
        st.write(f"Last uploaded: {st.session_state['campaign_upload_time']}")

    # Upload User Credentials
    st.write("### Upload User Credentials")
    user_file = st.file_uploader("Upload User Credentials Excel", type=["xlsx","xls","csv"])
    if user_file:
        try:
            if user_file.name.endswith(".csv"):
                udf = pd.read_csv(user_file)
            else:
                udf = pd.read_excel(user_file, engine="openpyxl")
            st.session_state['users_df'] = udf
           e'] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            st.success("User credentials updated successfully!")
            st.dataframe(udf)
        except Exception as e:
            st.error(f"Error reading user file: {e}")

    if 'user_upload_time' in st.session_state:
        st.write(f"Last uploaded: {st.session_state['user_upload_time']}")

    # Logout option
    if st.button("Logout"):
        st.session_state['admin_logged_in'] = False
        st.success("Admin logged out successfully!")
