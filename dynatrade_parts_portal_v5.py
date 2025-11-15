from flask import Flask, request, redirect, flash
from flask import render_template_string
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -------- Users and allowed IPs --------
users = {
    "customer1": {"password": "password123", "allowed_ip": "123.45.67.89"},
    "customer2": {"password": "pass456", "allowed_ip": None}  # None = any IP
}

# -------- Flask-Login Setup --------
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.allowed_ip = users[id]['allowed_ip']

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

# -------- Helper to get public IP --------
def get_public_ip():
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://checkip.amazonaws.com",
        "https://ident.me"
    ]
    for url in services:
        try:
            ip = requests.get(url, timeout=5).text.strip()
            if ip:
                return ip
        except:
            continue
    return None

# -------- Login Page --------
login_html = """
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Login</title></head>
<body>
<h2>Customer Login</h2>
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <ul>
    {% for category, message in messages %}
      <li style="color:red">{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
<form method="POST">
    Username: <input type="text" name="username" required><br>
    Password: <input type="password" name="password" required><br>
    <button type="submit">Login</button>
</form>
</body>
</html>
"""

# -------- Dashboard Page --------
dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Dashboard</title></head>
<body>
<h2>Welcome {{ user }}</h2>
<a href="{{ url_for('logout') }}">Logout</a>
<h3>Stock Data</h3>
<table border="1">
<tr>
{% for col in data[0].keys() %}
    <th>{{ col }}</th>
{% endfor %}
</tr>
{% for row in data %}
<tr>
{% for value in row.values() %}
    <td>{{ value }}</td>
{% endfor %}
</tr>
{% endfor %}
</table>
</body>
</html>
"""

# -------- Routes --------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username in users and users[username]["password"] == password:
            user_ip = get_public_ip()
            allowed_ip = users[username]["allowed_ip"]
            
            if allowed_ip and user_ip != allowed_ip:
                flash(f"Access denied. Your IP: {user_ip} is not allowed.", "danger")
                return render_template_string(login_html)
            
            user = User(username)
            login_user(user)
            return redirect("/dashboard")
        else:
            flash("Invalid username or password", "danger")
    return render_template_string(login_html)

@app.route("/dashboard")
@login_required
def dashboard():
    df = pd.read_excel("stock.xlsx")
    data = df.to_dict(orient="records")
    return render_template_string(dashboard_html, data=data, user=current_user.id)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

# -------- Run App --------
if __name__ == "__main__":
    app.run(debug=True)
