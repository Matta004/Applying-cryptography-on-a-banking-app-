import os
import csv
from flask import Flask, request, jsonify
import pyotp
import json
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives import serialization

app = Flask(__name__)

ACCOUNTS_FILE = "accounts.csv"
REQUESTS_FILE = "account_requests.csv"
DENIED_FILE = "denied_users.csv"

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

# Load server's RSA private key for decryption
with open("server_private_key.pem", "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

def decrypt_data(encrypted_data):
    try:
        decrypted_data = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=SHA256()),
                algorithm=SHA256(),
                label=None
            )
        )
        return decrypted_data.decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing credentials"}), 400

    account_id = data.get("Account ID")
    password = data.get("Password")
    two_factor_code = data.get("Two Factor Code")

    # Check admin hard-coded credentials
    if account_id == "admin" and password == "admin":
        # Return dummy JWT token and admin details
        return jsonify({
            "Account ID": "admin",
            "Name": "Admin User",
            "DOB": "",
            "Address": "",
            "Phone": "",
            "Email": "",
            "Gov ID": "admin_gov_id",
            "Password": "admin",
            "Balance": 0.0,
            "Initial Balance": 0.0,
            "Two Factor Enabled": False,
            "Two Factor Secret": "",
            "access_token": DUMMY_JWT_TOKEN
        }), 200

    # Otherwise, check accounts file
    accounts_data = load_csv(ACCOUNTS_FILE)
    if len(accounts_data) < 2:
        return jsonify({"error": "No accounts found"}), 401

    header = accounts_data[0]
    idx_map = get_header_index_map(header)

    # Find account by ID and password
    target_row = None
    for row in accounts_data[1:]:
        if row and row[idx_map["Account ID"]] == account_id and row[idx_map["Password"]] == password:
            target_row = row
            break

    if not target_row:
        return jsonify({"error": "Invalid credentials"}), 401

    # Check 2FA
    two_factor_enabled = (target_row[idx_map["Two Factor Enabled"]].lower() == "true")
    two_factor_secret = target_row[idx_map["Two Factor Secret"]]

    if two_factor_enabled:
        if not two_factor_code:
            return jsonify({"message": "2fa_required"}), 401
        totp = pyotp.TOTP(two_factor_secret)
        if not totp.verify(two_factor_code):
            return jsonify({"message": "invalid_2fa"}), 401

    # Return account data
    acc_data = {
        "Account ID": target_row[idx_map["Account ID"]],
        "Name": target_row[idx_map["Name"]],
        "DOB": target_row[idx_map["DOB"]],
        "Address": target_row[idx_map["Address"]],
        "Phone": target_row[idx_map["Phone"]],
        "Email": target_row[idx_map["Email"]],
        "Gov ID": target_row[idx_map["Gov ID"]],
        "Password": target_row[idx_map["Password"]],
        "Balance": float(target_row[idx_map["Balance"]]),
        "Initial Balance": float(target_row[idx_map["Initial Balance"]]),
        "Two Factor Enabled": two_factor_enabled,
        "Two Factor Secret": two_factor_secret
    }
    return jsonify(acc_data), 200

@app.route("/secure_login", methods=["POST"])
def secure_login():
    encrypted_data = request.get_data()
    decrypted = decrypt_data(encrypted_data)

    if not decrypted:
        print("Decryption failed")
        return jsonify({"error": "Decryption failed"}), 400

    try:
        data = json.loads(decrypted)
        print("Decrypted data received:", data)
    except Exception as e:
        print("Failed to parse decrypted data:", e)
        return jsonify({"error": "Invalid decrypted data format"}), 400

    account_id = data.get("Account ID")
    password = data.get("Password")
    two_factor_code = data.get("Two Factor Code")

    print("Account ID:", account_id, "Password:", password, "2FA Code:", two_factor_code)

    # Check account credentials
    accounts_data = load_csv(ACCOUNTS_FILE)
    if len(accounts_data) < 2:
        return jsonify({"error": "No accounts found"}), 401

    header = accounts_data[0]
    idx_map = get_header_index_map(header)

    target_row = None
    for row in accounts_data[1:]:
        if row and row[idx_map["Account ID"]] == account_id and row[idx_map["Password"]] == password:
            target_row = row
            break

    if not target_row:
        return jsonify({"error": "Invalid credentials"}), 401

    # Check if 2FA is enabled
    two_factor_enabled = (target_row[idx_map["Two Factor Enabled"]].lower() == "true")
    two_factor_secret = target_row[idx_map["Two Factor Secret"]]

    if two_factor_enabled:
        if not two_factor_code:
            return jsonify({"message": "2fa_required"}), 401
        totp = pyotp.TOTP(two_factor_secret)
        if not totp.verify(two_factor_code):
            return jsonify({"message": "invalid_2fa"}), 401

    # Successful login
    acc_data = {
        "Account ID": target_row[idx_map["Account ID"]],
        "Name": target_row[idx_map["Name"]],
        "DOB": target_row[idx_map["DOB"]],
        "Address": target_row[idx_map["Address"]],
        "Phone": target_row[idx_map["Phone"]],
        "Email": target_row[idx_map["Email"]],
        "Gov ID": target_row[idx_map["Gov ID"]],
        "Password": target_row[idx_map["Password"]],
        "Balance": float(target_row[idx_map["Balance"]]),
        "Initial Balance": float(target_row[idx_map["Initial Balance"]]),
        "Two Factor Enabled": two_factor_enabled,
        "Two Factor Secret": two_factor_secret
    }
    return jsonify(acc_data), 200



@app.route("/verify_credentials", methods=["POST"])
def verify_credentials():
    data = request.get_json()
    account_id = data.get("Account ID")
    password = data.get("Password")

    accounts_data = load_csv(ACCOUNTS_FILE)
    if len(accounts_data) < 2:
        return jsonify({"error": "No accounts found"}), 401

    header = accounts_data[0]
    idx_map = get_header_index_map(header)

    for row in accounts_data[1:]:
        if row[idx_map["Account ID"]] == account_id and row[idx_map["Password"]] == password:
            two_factor_enabled = (row[idx_map["Two Factor Enabled"]].lower() == "true")
            account_data = {
                "Account ID": row[idx_map["Account ID"]],
                "Name": row[idx_map["Name"]],
                "DOB": row[idx_map["DOB"]],
                "Address": row[idx_map["Address"]],
                "Phone": row[idx_map["Phone"]],
                "Email": row[idx_map["Email"]],
                "Gov ID": row[idx_map["Gov ID"]],
                "Password": row[idx_map["Password"]],
                "Balance": float(row[idx_map["Balance"]]),
                "Initial Balance": float(row[idx_map["Initial Balance"]]),
                "Two Factor Enabled": two_factor_enabled,
                "Two Factor Secret": row[idx_map["Two Factor Secret"]]
            }
            return jsonify(account_data), 200

    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/view_accounts", methods=["GET"])
def view_accounts():
    accounts_data = load_csv(ACCOUNTS_FILE)
    if len(accounts_data) <= 1:
        # No accounts besides header
        return jsonify({"accounts": []})
    return jsonify({"accounts": accounts_data[1:]})

@app.route("/save_accounts", methods=["POST"])
def save_accounts():
    data = request.get_json()
    if "accounts" not in data:
        return jsonify({"error": "No accounts data provided"}), 400

    # Load existing accounts
    accounts_data = load_csv(ACCOUNTS_FILE)
    if not accounts_data:
        # Create a fresh header if the file is empty
        accounts_data = [["Account ID", "Name", "DOB", "Address", "Phone", "Email", "Gov ID", 
                          "Password", "Balance", "Initial Balance", "Two Factor Enabled", "Two Factor Secret"]]

    header = accounts_data[0]
    idx_map = get_header_index_map(header)

    # Create a dictionary of existing accounts for easier lookup
    existing_accounts = {row[idx_map["Account ID"]]: row for row in accounts_data[1:]}

    # Merge new data with existing accounts
    for new_account in data["accounts"]:
        account_id = new_account[idx_map["Account ID"]]
        existing_accounts[account_id] = new_account  # Update or add the account

    # Rebuild the accounts file content
    merged_data = [header] + list(existing_accounts.values())
    save_csv(ACCOUNTS_FILE, merged_data)

    return jsonify({"message": "Accounts data saved successfully."})

@app.route("/view_account_requests", methods=["GET"])
def view_account_requests():
    requests_data = load_csv(REQUESTS_FILE)
    if len(requests_data) <= 1:
        return jsonify({"account_requests": []})
    return jsonify({"account_requests": requests_data[1:]})

@app.route("/create_account_request", methods=["POST"])
def create_account_request():
    data = request.get_json()
    required_fields = ["Account ID","Name","DOB","Address","Phone","Email","Gov ID","Password"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    requests_data = load_csv(REQUESTS_FILE)
    if not requests_data:
        # Create a fresh header if file empty
        requests_data = [required_fields]

    # Check if account ID already requested
    idx_map = get_header_index_map(requests_data[0])
    for row in requests_data[1:]:
        if row[idx_map["Account ID"]] == data["Account ID"]:
            return jsonify({"error": "Account ID already requested"}), 400

    # Append new request
    new_row = [
        data["Account ID"],
        data["Name"],
        data["DOB"],
        data["Address"],
        data["Phone"],
        data["Email"],
        data["Gov ID"],
        data["Password"]
    ]
    requests_data.append(new_row)
    save_csv(REQUESTS_FILE, requests_data)
    return jsonify({"message": "Account request submitted successfully."})

@app.route("/verify_two_factor_code", methods=["POST"])
def verify_two_factor_code():
    data = request.get_json()
    account_id = data.get("Account ID")
    password = data.get("Password")
    two_factor_code = data.get("Two Factor Code")

    accounts_data = load_csv(ACCOUNTS_FILE)
    header = accounts_data[0]
    idx_map = get_header_index_map(header)

    for row in accounts_data[1:]:
        if row[idx_map["Account ID"]] == account_id and row[idx_map["Password"]] == password:
            two_factor_secret = row[idx_map["Two Factor Secret"]]
            totp = pyotp.TOTP(two_factor_secret)

            if totp.verify(two_factor_code):
                return jsonify({"message": "2FA verified successfully."}), 200
            else:
                return jsonify({"message": "Invalid 2FA code."}), 401

    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/delete_account_request", methods=["POST"])
def delete_account_request():
    data = request.get_json()
    account_id = data.get("account_id")
    if not account_id:
        return jsonify({"error": "No account_id provided"}), 400

    requests_data = load_csv(REQUESTS_FILE)
    if not requests_data:
        return jsonify({"error": "No requests data found"}), 404

    header = requests_data[0]
    idx_map = get_header_index_map(header)
    filtered = [header]
    found = False
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

@app.route("/save_denied_user", methods=["POST"])
def save_denied_user():
    data = request.get_json()
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

@app.route("/send_denial_email", methods=["POST"])
def send_denial_email():
    # Simulate sending an email
    data = request.get_json()
    email = data.get("email")
    name = data.get("name")
    reason = data.get("reason")
    if not email or not name or not reason:
        return jsonify({"error":"Missing email, name, or reason"}), 400
    # In practice, you'd integrate with an email service
    return jsonify({"message": f"Denial email sent to {email} with reason: {reason}."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
