import os
import csv
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

ACCOUNTS_FILE = "accounts.csv"
REQUESTS_FILE = "account_requests.csv"
DENIED_FILE = "denied_users.csv"

# Dummy secret for JWT simulation
DUMMY_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.admin.payload.signature"

def load_csv(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    return reader

def save_csv(file_path, data):
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow(row)

def get_header_index_map(header_row):
    return {col: i for i, col in enumerate(header_row)}

def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        token = auth_header.split(" ")[1]
        if token != DUMMY_JWT_TOKEN:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing credentials"}), 400

    account_id = data.get("Account ID")
    password = data.get("Password")

    # Check admin hard-coded credentials
    if account_id == "admin" and password == "admin":
        # Return dummy JWT token
        return jsonify({"access_token": DUMMY_JWT_TOKEN})

    # Otherwise, check if it matches an existing account
    accounts_data = load_csv(ACCOUNTS_FILE)
    if len(accounts_data) < 2:
        return jsonify({"error": "No accounts found"}), 401

    header = accounts_data[0]
    idx_map = get_header_index_map(header)

    # Check credentials against accounts
    for row in accounts_data[1:]:
        if row and row[idx_map["Account ID"]] == account_id and row[idx_map["Password"]] == password:
            return jsonify({"access_token": DUMMY_JWT_TOKEN})

    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/view_accounts", methods=["GET"])
@authenticate
def view_accounts():
    accounts_data = load_csv(ACCOUNTS_FILE)
    # Return all accounts excluding header row
    if len(accounts_data) <= 1:
        # No accounts
        return jsonify({"accounts": []})
    return jsonify({"accounts": accounts_data[1:]})

@app.route("/save_accounts", methods=["POST"])
@authenticate
def save_accounts():
    data = request.get_json()
    if "accounts" not in data:
        return jsonify({"error": "No accounts data provided"}), 400

    # Load existing header
    accounts_data = load_csv(ACCOUNTS_FILE)
    if not accounts_data:
        # Create a fresh header if not exists
        header = ["Account ID","Name","DOB","Address","Phone","Email","Gov ID","Password","Balance","Initial Balance","Two Factor Enabled","Two Factor Secret"]
    else:
        header = accounts_data[0]

    # Overwrite with new accounts data
    new_data = [header]
    for row in data["accounts"]:
        # Ensure row length matches header length
        if len(row) < len(header):
            # Pad missing columns if any
            row += [""] * (len(header) - len(row))
        new_data.append(row)

    save_csv(ACCOUNTS_FILE, new_data)
    return jsonify({"message": "Accounts data saved successfully."})

@app.route("/view_account_requests", methods=["GET"])
@authenticate
def view_account_requests():
    requests_data = load_csv(REQUESTS_FILE)
    if len(requests_data) <= 1:
        return jsonify({"account_requests": []})
    # Return all requests except header
    return jsonify({"account_requests": requests_data[1:]})

@app.route("/delete_account_request", methods=["POST"])
@authenticate
def delete_account_request():
    data = request.get_json()
    account_id = data.get("account_id")
    if not account_id:
        return jsonify({"error": "No account_id provided"}), 400

    requests_data = load_csv(REQUESTS_FILE)
    if not requests_data:
        return jsonify({"error": "No requests data found"}), 404

    header = requests_data[0]
    filtered = [header]
    found = False
    idx_map = get_header_index_map(header)
    for row in requests_data[1:]:
        if row and row[idx_map["Account ID"]] != account_id:
            filtered.append(row)
        else:
            found = True

    save_csv(REQUESTS_FILE, filtered)
    if found:
        return jsonify({"message": f"Account request {account_id} deleted successfully."})
    else:
        return jsonify({"error": "Account request not found"}), 404

@app.route("/create_account", methods=["POST"])
@authenticate
def create_account():
    data = request.get_json()
    required_fields = ["Account ID", "Name", "DOB", "Address", "Phone", "Email", "Gov ID", "Password", "Balance", "Initial Balance"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    # Load accounts
    accounts_data = load_csv(ACCOUNTS_FILE)
    if not accounts_data:
        # Create a fresh header if file empty
        accounts_data = [["Account ID","Name","DOB","Address","Phone","Email","Gov ID","Password","Balance","Initial Balance","Two Factor Enabled","Two Factor Secret"]]

    header = accounts_data[0]
    idx_map = get_header_index_map(header)

    # Check if account with same ID already exists
    for row in accounts_data[1:]:
        if row and row[idx_map["Account ID"]] == data["Account ID"]:
            return jsonify({"error": "Account ID already exists"}), 400

    # Append new account
    new_row = [
        data["Account ID"],
        data["Name"],
        data["DOB"],
        data["Address"],
        data["Phone"],
        data["Email"],
        data["Gov ID"],
        data["Password"],
        data["Balance"],
        data["Initial Balance"],
        "false", # Two Factor Enabled by default false
        ""       # Two Factor Secret empty by default
    ]
    accounts_data.append(new_row)
    save_csv(ACCOUNTS_FILE, accounts_data)
    return jsonify({"message": "Account created successfully."})

# Additional endpoints to handle denial of requests and sending denial email if needed
@app.route("/save_denied_user", methods=["POST"])
@authenticate
def save_denied_user():
    data = request.get_json()
    # Expected: {"account_id":..., "name":..., "dob":..., "address":..., "phone":..., "email":..., "gov_id":..., "password":..., "reason":...}
    required = ["account_id","name","dob","address","phone","email","gov_id","password","reason"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Missing field: {r}"}), 400

    denied_data = load_csv(DENIED_FILE)
    if not denied_data:
        denied_data = [["Account ID","Name","DOB","Address","Phone","Email","Gov ID","Password","Reason"]]

    denied_data.append([
        data["account_id"],
        data["name"],
        data["dob"],
        data["address"],
        data["phone"],
        data["email"],
        data["gov_id"],
        data["password"],
        data["reason"]
    ])
    save_csv(DENIED_FILE, denied_data)
    return jsonify({"message": "Denied user saved successfully."})

# A dummy endpoint to simulate sending a denial email
@app.route("/send_denial_email", methods=["POST"])
@authenticate
def send_denial_email():
    # This would simulate sending an email. Here we just print/return a message.
    data = request.get_json()
    email = data.get("email")
    name = data.get("name")
    reason = data.get("reason")
    if not email or not name or not reason:
        return jsonify({"error":"Missing email, name, or reason"}), 400
    # In practice, you'd integrate with an email service here.
    return jsonify({"message": f"Denial email sent to {email} with reason: {reason}."})

if __name__ == "__main__":
    # Adjust host and port as needed
    app.run(host="0.0.0.0", port=5000, debug=True)
