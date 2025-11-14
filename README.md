# Dynatrade Parts Portal v5 (Final Version)

## Features
- IP-based Login Validation using https://api.ipify.org.
- Excel-based Authentication for Username, Password, and IP.
- Customer Portal:
  - Secure login with explicit error messages for invalid credentials.
  - Added Login button for mobile and desktop (better UX).
  - Search parts by Reference, Manufacturing, or OE number.
  - Add to Cart, Clear Cart, and inquiry options via WhatsApp, Email, and Call.
  - Download campaign files uploaded by Admin.
- Admin Portal:
  - Secure login (admin/admin123).
  - Upload price list (Excel/CSV).
  - Upload campaign files (supports Excel, PDF, images, Word).
  - Upload user credentials for authentication.
  - Persistent Admin Session after login (no logout on file upload).
  - Logout button for Admin.

## What's New
- Error message for wrong username/password.
- Login button added for mobile.
- Admin login persistence fixed.
- Removed troubleshooting section.

## Setup Instructions
1. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2. Run the app:
    ```bash
    streamlit run dynatrade_parts_portal_v5.py
    ```

## Dependencies
- streamlit==1.39.0
- pandas==2.2.3
- openpyxl==3.1.5
- xlrd==2.0.1
- requests==2.31.0

## Notes
- Ensure user credentials file contains columns: Username, Password, IP.
- Campaign files can be in multiple formats: .xlsx, .xls, .csv, .pdf, .png, .jpeg, .jpg, .doc, .docx.
- Admin session persists until you click Logout.
