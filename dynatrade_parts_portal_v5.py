import streamlit as st
import pandas as pd
import datetime
import base64
import requests

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Dynatrade Parts Portal", layout="wide")

# Add custom CSS for light background image and logo
st.markdown(
    """
    <style>
    body {
        background-image: url('https://your-image-url/european-truck-car.jpg');
        background-size: cover;
        background-attachment: fixed;
        opacity: 0.95;
    }
    .logo {
        position: fixed;
        top: 10px;
        left: 10px;
        width: 150px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Display Dynatrade logo
st.markdown('<img src="https://your-logo-url/dynatrade-logo.png" class="logo">', unsafe_allow_html=True)

# -------------------- MULTIPAGE NAVIGATION --------------------
page = st.sidebar.radio("Navigate", ["Dynatrade – Customer Portal", "Admin Portal"])

# -------------------- SESSION STATE --------------------
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
if 'upload_times' not in st.session_state:
    st.session_state['upload_times'] = {"Price List": None, "Campaign": None, "User Credentials": None}

# Function to get real client IP using ipify
@st.cache_data(show_spinner=False)
def get_client_ip():
    try:
        return requests.get('https://api.ipify.org').text
    except:
        return 'UNKNOWN'

# -------------------- CUSTOMER PORTAL --------------------
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
            df = st.session_state['price_df']
            if search_term:
                results = df[df.apply(lambda row: search_term.lower() in str(row.values).lower(), axis=1)]
                if len(results) > 0:
                    st.write("### Matching Parts")
                    # Add headers including Required Qty and Add to Cart
                    header_cols = st.columns(len(results.columns) + 2)
                    for i, col_name in enumerate(results.columns):
                        header_cols[i].write(col_name)
                    header_cols[-2].write("Required Qty.")
                    header_cols[-1].write("Add to Cart")

                    for idx, row in results.iterrows():
                        cols = st.columns(len(row) + 2)
                        for i, val in enumerate(row):
                            # Format numeric values to 2 decimals
                            if isinstance(val, (int, float)):
                                cols[i].write(f"{val:.2f}")
                            else:
                                cols[i].write(val)
                        qty = cols[-2].number_input("Qty", min_value=1, value=1, key=f"qty_{idx}")
                        if cols[-1].button("Add", key=f"add_{idx}"):
                            item = row.to_dict()
                            item['Required Qty'] = qty
                            st.session_state['cart'].append(item)
                else:
                    st.warning("No matching parts found.")

            # Cart display
            st.write("### Your Cart")
            if st.session_state['cart']:
                cart_df = pd.DataFrame(st.session_state['cart'])
                # Format unit price to 2 decimals
                if 'Unit Price in AED' in cart_df.columns:
                    cart_df['Unit Price in AED'] = cart_df['Unit Price in AED'].apply(lambda x: f"{float(x):.2f}" if str(x).replace('.', '', 1).isdigit() else x)
                st.table(cart_df.style.hide(axis="index"))

                # WhatsApp link with full cart data
                cart_text = cart_df.to_string(index=False)
                whatsapp_link = f"https://wa.me/+97165132219?text=Inquiry%20for%20parts:%20{cart_text}"
                email_link = f"mailto:52etrk51@dynatradegroup.com?subject=Parts%20Inquiry&body={cart_text}"

                st.markdown(f"""
                Send your requirement in  
                **Business WhatsApp** - [Click Here]({whatsapp_link})  
                **OR Email to Sales Man** - [Click Here]({email_link})  
                **OR Contact Sales Man** – Mr. Binay +971 50 4815087
                """)

                if st.button("Clear Cart"):
                    st.session_state['cart'] = []
                    st.success("Cart cleared successfully!")
            else:
                st.write("Cart is empty.")

        if st.button("Logout"):
            st.session_state['customer_logged_in'] = False
            st.session_state['customer_username'] = ""
            st.success("Logged out successfully!")

# -------------------- ADMIN PORTAL --------------------
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
                st.session_state['upload_times']['Price List'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success("Price List uploaded successfully!")
            except Exception as e:
                st.error(f"Error reading file: {e}")

        # Upload Campaign File
        st.write("### Upload Campaign File")
        campaign_file = st.file_uploader("Upload Campaign File", type=["xlsx","xls","csv","pdf","png","jpeg","jpg","doc","docx"])
        if campaign_file:
            st.session_state['campaign_file'] = (campaign_file.name, campaign_file.read())
            st.session_state['upload_times']['Campaign'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success("Campaign File uploaded successfully! It will be visible to customers as a download link.")

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
                st.session_state['upload_times']['User Credentials'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success("User credentials updated successfully!")
                st.dataframe(udf)
            except Exception as e:
                st.error(f"Error reading user file: {e}")

        # Show last upload times
        st.write("### Last Upload Times")
        for key, val in st.session_state['upload_times'].items():
            st.write(f"{key}: {val if val else 'Not uploaded yet'}")

        # Logout option
        if st.button("Logout"):
            st.session_state['admin_logged_in'] = False
            st.success("Admin logged out successfully!")
