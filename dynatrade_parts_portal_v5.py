import streamlit as st
import pandas as pd
import requests

# Page config
st.set_page_config(page_title="Dynatrade Parts Portal", layout="wide")
st.title("Dynatrade Automotive LLC - Parts Portal")

# Function to get real IP (server-side fallback)
def get_client_ip():
    try:
        return requests.get('https://api.ipify.org').text
    except:
        return "UNKNOWN"

# Initialize session state for cart
if 'cart' not in st.session_state:
    st.session_state['cart'] = []

# Sidebar for file upload
st.sidebar.header("Upload Parts List")
uploaded_file = st.sidebar.file_uploader("Upload Parts List", type=["csv", "xlsx", "xls"])

# Admin login form
st.sidebar.subheader("Admin Login")
with st.sidebar.form("admin_login_form"):
    admin_user = st.text_input("Admin Username")
    admin_pass = st.text_input("Admin Password", type="password")
    admin_submit = st.form_submit_button("Login")

if admin_submit:
    if admin_user == "admin" and admin_pass == "admin123":
        st.sidebar.success("Admin Login Successful")
    else:
        st.sidebar.error(f"Invalid Username or Password (IP: {get_client_ip()})")

# Customer login form
st.subheader("Customer Login")
with st.form("customer_login_form"):
    username = st.text_input("Customer Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

if submitted:
    if username == "customer1" and password == "pass123":
        st.success("Login Successful")
    else:
        st.error(f"Invalid Username or Password (IP: {get_client_ip()})")

# File upload and search
if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, encoding="latin1")
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        else:
            df = pd.read_excel(uploaded_file, engine="xlrd")

        st.write("### Search for Parts")
        search_term = st.text_input("Enter Original Part No.")
        if search_term:
            if 'Original Part No.' in df.columns:
                results = df[df['Original Part No.'].astype(str).str.contains(search_term, case=False, na=False)]
                st.write(f"Found {len(results)} matching parts:")
                if len(results) > 0:
                    # Add 'Add to Cart' column
                    results = results.copy()
                    results['Add to Cart'] = ''
                    st.write("### Matching Parts")
                    for idx, row in results.iterrows():
                        cols = st.columns(len(row))
                        for i, val in enumerate(row[:-1]):
                            cols[i].write(val)
                        if cols[-1].button("Add", key=f"add_{idx}"):
                            st.session_state['cart'].append(row[:-1].to_dict())
                else:
                    st.warning("No matching parts found.")
            else:
                st.error("Column 'Original Part No.' not found in uploaded file.")
    except Exception as e:
        st.error(f"Error reading file: {e}")

# Display Cart
st.write("### Your Cart")
if st.session_state['cart']:
    cart_df = pd.DataFrame(st.session_state['cart'])
    st.table(cart_df)

    whatsapp_message = "Inquiry for parts: " + ", ".join(cart_df['Original Part No.'].tolist())
    whatsapp_number = "971501234567"
    whatsapp_link = f"https://wa.me/{whatsapp_number}?text={whatsapp_message}"
    email_body = "Inquiry for parts:\n" + cart_df.to_string(index=False)
    mailto_link = f"mailto:sales@dynatrade.com?subject=Parts Inquiry&body={email_body}"

    st.markdown(f"[Send via WhatsApp]({whatsapp_link})")
    st.markdown(f"[Send via Email]({mailto_link})")

    if st.button("Clear Cart"):
        st.session_state['cart'] = []
        st.experimental_rerun()
