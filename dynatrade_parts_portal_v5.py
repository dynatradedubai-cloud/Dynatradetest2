import streamlit as st
import pandas as pd
from datetime import datetime
import base64
from io import BytesIO
import pytz

# Initialize Dubai timezone
dubai_tz = pytz.timezone("Asia/Dubai")

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Dynatrade Parts Portal", layout="wide")

# =====================================================
# =========== CACHED PERSISTENT USER STORAGE ==========
# =====================================================
@st.cache_data
def save_users(df):
    """Save user list persistently across sessions."""
    return df

@st.cache_data
def load_users():
    """Load previously saved user list."""
    return save_users()

# =====================================================
# ============= REAL CLIENT IP DETECTION ==============
# =====================================================
def get_client_ip():
    """Detect client IP using Streamlit proxy headers."""
    try:
        ctx = st.context
        if ctx and ctx.headers:
            ip = ctx.headers.get("X-Forwarded-For", "")
            if ip:
                return ip.split(",")[0].strip()
    except:
        pass
    return ""  # fallback

# =====================================================
# ================= SESSION STATE ======================
# =====================================================
default_vals = {
    "cart": [],
    "price_df": None,
    "campaign_file": None,
    "users_df": pd.DataFrame(),
    "admin_logged_in": False,
    "customer_logged_in": False,
    "customer_username": "",
}

for key, val in default_vals.items():
    if key not in st.session_state:
        st.session_state[key] = val

for k in [
    "price_upload_time",
    "campaign_upload_time",
    "user_upload_time",
    "last_price_file",
    "last_campaign_file",
    "last_user_file",
]:
    if k not in st.session_state:
        st.session_state[k] = None

# =====================================================
# ================= NAVIGATION MENU ====================
# =====================================================
page = st.sidebar.radio(
    "Navigate",
    ["Dynatrade – Customer Portal", "Admin Portal"]
)

# =====================================================
# ================= CUSTOMER PORTAL ====================
# =====================================================
if page == "Dynatrade – Customer Portal":
    st.title("Dynatrade – Customer Portal")

    # Detect IP
    client_ip = get_client_ip()
    st.markdown(
        f"<div style='font-weight:bold;color:green;margin-bottom:10px;'>Detected IP: {client_ip}</div>",
        unsafe_allow_html=True,
    )

    # Load users if empty
    if st.session_state["users_df"].empty:
        try:
            st.session_state["users_df"] = load_users()
        except:
            pass

    # ---------------- LOGIN SECTION ----------------
    if not st.session_state["customer_logged_in"]:
        username = st.text_input("Customer Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", key="login_button"):
            if st.session_state["users_df"].empty:
                st.error("User credentials file not uploaded.")
            else:
                user_row = st.session_state["users_df"][
                    (st.session_state["users_df"]["Username"] == username)
                    & (st.session_state["users_df"]["Password"] == password)
                ]

                if user_row.empty:
                    st.error("Invalid username or password.")
                else:
                    allowed_ip = str(user_row["IP"].values[0]).strip()

                    if client_ip == allowed_ip:
                        st.session_state["customer_logged_in"] = True
                        st.session_state["customer_username"] = username
                        st.success("Login Successful!")
                        st.rerun()
                    else:
                        st.error(f"Access denied: IP {client_ip} not allowed.")
    else:
        st.success(f"Welcome, {st.session_state['customer_username']}!")

    # ---------------- CONTENT AFTER LOGIN ----------------
    if st.session_state["customer_logged_in"]:

        # Download Campaign File
        if st.session_state["campaign_file"]:
            st.write("### Special Campaign")
            file_name, file_bytes = st.session_state["campaign_file"]
            b64 = base64.b64encode(file_bytes).decode()
            st.markdown(
                f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">Download Campaign File</a>',
                unsafe_allow_html=True,
            )

        # ---------------- SEARCH SYSTEM ----------------
        if st.session_state["price_df"] is not None:
            st.write("### Search for Parts")

            search_term = st.text_input(
                "Enter Part Number (Reference / Manufacturing / OE)", key="search_box"
            )

            check_search = st.button("Check", key="check_button")

            df = st.session_state["price_df"]

            if check_search and search_term:
                st.session_state["search_results"] = df[
                    df.apply(
                        lambda row: search_term.lower()
                        in str(row.values).lower(),
                        axis=1,
                    )
                ]

            # Display results
            if (
                "search_results" in st.session_state
                and not st.session_state["search_results"].empty
            ):
                results = st.session_state["search_results"]
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

                    qty = cols[-2].number_input(
                        "Qty", min_value=1, value=1, key=f"qty_{idx}"
                    )

                    if cols[-1].button("Add", key=f"add_{idx}"):
                        item = row.to_dict()
                        if "Unit Price" in item:
                            item["Unit Price"] = round(float(item["Unit Price"]), 2)
                        item["Required Qty"] = qty
                        st.session_state["cart"].append(item)

            elif check_search:
                st.warning("No matching parts found.")

        # ---------------- CART ----------------
        st.write("### Your Cart")

        if st.session_state["cart"]:
            cart_df = pd.DataFrame(st.session_state["cart"])
            st.dataframe(cart_df)

            output = BytesIO()
            cart_df.to_excel(output, index=False)
            excel_data = output.getvalue()
            b64 = base64.b64encode(excel_data).decode()

            st.markdown(
                f'<a href="data:application/octet-stream;base64,{b64}" download="cart.xlsx">Download Cart as Excel</a>',
                unsafe_allow_html=True,
            )
        else:
            st.write("Cart is empty.")

        if st.button("Clear Cart", key="clear_cart"):
            st.session_state["cart"] = []
            st.session_state.pop("search_results", None)
            st.success("Cart cleared!")

        if st.button("Logout", key="logout_cust"):
            st.session_state["customer_logged_in"] = False
            st.session_state["customer_username"] = ""
            st.session_state.pop("search_results", None)
            st.session_state["cart"] = []
            st.rerun()

    else:
        st.warning("Please log in to access search and cart features.")

    st.markdown(
        """
        ---
        **Send your requirement in:**
        - **Business WhatsApp:** https://wa.me/+97165132219?text=Inquiry  
        - **Email:** 52etrk51@dynatradegroup.com  
        - **Sales:** Mr. Binay +971 50 4815087  
        ---
        """
    )

# =====================================================
# ==================== ADMIN PORTAL ===================
# =====================================================
if page == "Admin Portal":
    st.title("Admin Portal")

    if not st.session_state["admin_logged_in"]:
        admin_user = st.text_input("Admin Username")
        admin_pass = st.text_input("Password", type="password")

        if st.button("Admin Login", key="admin_login_btn"):
            if admin_user == "admin" and admin_pass == "admin123":
                st.session_state["admin_logged_in"] = True
                st.success("Admin Login Successful!")
                st.rerun()
            else:
                st.error("Invalid Admin Credentials")

    else:
        st.success("Admin Logged In")

        # ---------------- PRICE UPLOAD ----------------
        st.write("### Upload Price List")
        price_file = st.file_uploader(
            "Upload Price List", type=["xlsx", "xls", "csv"], key="price_upload"
        )

        if price_file is not None:
            try:
                if price_file.name.endswith(".csv"):
                    df = pd.read_csv(price_file)
                else:
                    df = pd.read_excel(price_file, engine="openpyxl")

                st.session_state["price_df"] = df
                st.session_state["price_upload_time"] = datetime.now(
                    dubai_tz
                ).strftime("%d-%m-%Y %H:%M:%S")
                st.success("Price List Uploaded Successfully!")
            except Exception as e:
                st.error(f"Error reading price file: {e}")

        # ---------------- CAMPAIGN UPLOAD ----------------
        st.write("### Upload Campaign File")
        campaign_file = st.file_uploader(
            "Upload Campaign File",
            type=["xlsx", "xls", "csv", "pdf", "png", "jpeg", "jpg", "doc", "docx"],
            key="campaign_upload",
        )

        if campaign_file:
            st.session_state["campaign_file"] = (
                campaign_file.name,
                campaign_file.read(),
            )
            st.session_state["campaign_upload_time"] = datetime.now(
                dubai_tz
            ).strftime("%d-%m-%Y %H:%M:%S")
            st.success("Campaign File Uploaded Successfully!")

        # ---------------- USER CREDENTIALS UPLOAD ----------------
        st.write("### Upload User Credentials (Excel/CSV)")
        user_file = st.file_uploader(
            "Upload User Credentials", type=["xlsx", "xls", "csv"], key="user_upload"
        )

        if user_file:
            try:
                if user_file.name.endswith(".csv"):
                    udf = pd.read_csv(user_file)
                else:
                    udf = pd.read_excel(user_file, engine="openpyxl")

                save_users.clear()  # remove old version
                save_users(udf)  # save new version

                st.session_state["users_df"] = udf
                st.session_state["user_upload_time"] = datetime.now(
                    dubai_tz
                ).strftime("%d-%m-%Y %H:%M:%S")

                st.success("User Credentials Uploaded Successfully!")
            except Exception as e:
                st.error(f"Error reading user file: {e}")

        if st.button("Logout", key="logout_admin"):
            st.session_state["admin_logged_in"] = False
            st.rerun()
