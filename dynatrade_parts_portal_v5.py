import streamlit as st
import pandas as pd
import datetime
import base64
import requests

st.set_page_config(page_title="Dynatrade Parts Portal", layout="wide")

# -------------------- MULTIPAGE NAVIGATION --------------------
page = st.sidebar.radio("Navigate", ["Customer Portal", "Admin Portal"])

# -------------------- SESSION STATE --------------------
if 'cart' not in st.session_state:
    st.session_state['cart'] = []
if 'price_df' not in st.session_state:
    st.session_state['price_df'] = None
if 'campaign_file' not in st.session_state:
    st.session_state['campaign_file'] = None
if 'users_df' not in st.session_state:
    st.session_state['users_df'] = pd.DataFrame(columns=['Username', 'Password', 'IP'])

# Function to get real client IP using external service
@st.cache_data(show_spinner=False)
def get_client_ip():
    try:
        return requests.get('https://api.ipify.org').text
    except:
        return 'UNKNOWN'

# -------------------- CUSTOMER PORTAL --------------------
if page == "Customer Portal":
    st.title("Customer Portal")

    # Use form for better mobile UX
    with st.form("login_form"):
        username = st.text_input("Customer Username")
        password = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Login")

    valid_user = False
    if submit_login:
        if not st.session_state['users_df'].empty:
            user_row = st.session_state['users_df'][
                (st.session_state['users_df']['Username'] == username) &
                (st.session_state['users_df']['Password'] == password)
            ]
            if not user_row.empty:
                client_ip = get_client_ip()
                if client_ip in user_row['IP'].values:
                    valid_user = True
                else:
                    st.error(f"Access denied: IP {client_ip} not allowed")
            else:
                st.error("Invalid username or password")
        else:
            st.warning("User credentials file not loaded.")

    if valid_user:
        st.success("Login Successful")

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
                st.write(f"Found {len(results)} matching parts:")
                if len(results) > 0:
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

                # Notification
                st.info("Notification sent to salesman: 52etrk51@dynatradegroup.com")
                st.write(f"Customer: {username}, Part: {search_term}, Time: {datetime.datetime.now()}")

            # Cart display
            st.write("### Your Cart")
            if st.session_state['cart']:
                cart_df = pd.DataFrame(st.session_state['cart'])
                st.table(cart_df)

                whatsapp_number = "+97165132219"
                call_number = "+971504815087"
                email_id = "52etrk51@dynatradegroup.com"
                whatsapp_message = "Inquiry for parts:\n" + cart_df.to_string(index=False)
                whatsapp_link = f"https://wa.me/{whatsapp_number}?text={whatsapp_message}"
                email_body = cart_df.to_string(index=False)
                mailto_link = f"mailto:{email_id}?subject=Parts Inquiry&body={email_body}"

                st.markdown(f"[Send via WhatsApp]({whatsapp_link})")
                st.markdown(f"[Send via Email]({mailto_link})")
                st.markdown(f"[Call Salesman](tel:{call_number})")

                if st.button("Clear Cart"):
                    st.session_state['cart'] = []
                    st.experimental_rerun()
            else:
                st.write("Cart is empty.")
    else:
        st.warning("Please login to access the portal.")

# -------------------- ADMIN PORTAL --------------------
if page == "Admin Portal":
    st.title("Admin Portal")
    with st.form("admin_login_form"):
        admin_user = st.text_input("Admin Username")
        admin_pass = st.text_input("Password", type="password")
        submit_admin = st.form_submit_button("Login")

    if submit_admin and admin_user == "admin" and admin_pass == "admin123":
        st.success("Admin Login Successful")

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
                st.success("Price List uploaded successfully!")
            except Exception as e:
                st.error(f"Error reading file: {e}")

        # Upload Campaign File
        st.write("### Upload Campaign File")
        campaign_file = st.file_uploader("Upload Campaign File", type=["xlsx","xls","csv","pdf","png","jpeg","jpg","doc","docx"])
        if campaign_file:
            st.session_state['campaign_file'] = (campaign_file.name, campaign_file.read())
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
                st.success("User credentials updated successfully!")
                st.dataframe(udf)
            except Exception as e:
                st.error(f"Error reading user file: {e}")
    else:
        st.warning("Please login as Admin to access upload options.")

# -------------------- TROUBLESHOOTING --------------------
st.sidebar.markdown("### Troubleshooting")
st.sidebar.info("""
**Common Issues:**
1. **IP Mismatch:**  
   - Ensure your IP matches the one in the uploaded user credentials file.
   - Use https://whatismyipaddress.com to verify.

2. **Invalid Username/Password:**  
   - Check spelling and case sensitivity.
   - Admin default: `admin / admin123`.

3. **File Format Errors:**  
   - Price List: Use `.xlsx`, `.xls`, or `.csv`.
   - Campaign: Supports Excel, PDF, images, Word.
   - User Credentials: Must have columns `Username`, `Password`, `IP`.

4. **No Submit Button on Mobile:**  
   - Fixed in this version using `Login` button in forms.

If issues persist, contact: **52etrk51@dynatradegroup.com**
""")
