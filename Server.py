from flask import Flask, jsonify, request
import logging
import csv
import os
import random
import string

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Paths to CSV files
ACCOUNT_REQUESTS_FILE = 'account_requests.csv'
ACCOUNTS_FILE = 'accounts.csv'
DENIED_USERS_FILE = 'denied_users.csv'

# Utility function to read CSV file
def read_csv(file_path):
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        return list(reader)

# Utility function to write to CSV file
def write_csv(file_path, rows, mode='w'):
    with open(file_path, mode=mode, newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

# Log connection attempts
@app.before_request
def log_connection_attempt():
    ip_address = request.remote_addr
    method = request.method
    path = request.path
    logging.info(f"Connection attempt: {method} {path} from {ip_address}")

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "Server is up and running"}), 200

# Endpoint to submit a new account request
@app.route('/create_account_request', methods=['POST'])
def create_account_request():
    data = request.json
    new_request = [
        data.get('Account ID'),
        data.get('Name'),
        data.get('DOB'),
        data.get('Address'),
        data.get('Phone'),
        data.get('Email'),
        data.get('Gov ID'),
        data.get('Password')
    ]
    write_csv(ACCOUNT_REQUESTS_FILE, [new_request], mode='a')
    logging.info(f"Account request submitted for {data.get('Name')}")
    return jsonify({"message": "Account request submitted successfully"}), 200

# Endpoint to view account requests
@app.route('/view_account_requests', methods=['GET'])
def view_account_requests():
    account_requests = read_csv(ACCOUNT_REQUESTS_FILE)
    return jsonify({"account_requests": account_requests}), 200

# Endpoint to manage deposits
@app.route('/deposit', methods=['POST'])
def deposit():
    data = request.json
    account_id = data.get('Account ID')
    amount = float(data.get('Amount'))
    accounts = read_csv(ACCOUNTS_FILE)
    updated = False

    for account in accounts:
        if account[0] == account_id:
            account[8] = str(float(account[8]) + amount)  # Update balance
            updated = True
            break

    if updated:
        write_csv(ACCOUNTS_FILE, accounts)
        logging.info(f"Deposited ${amount} to account {account_id}")
        return jsonify({"message": f"Deposited ${amount} successfully"}), 200
    else:
        return jsonify({"error": "Account not found"}), 404

# Endpoint to handle withdrawals
@app.route('/withdraw', methods=['POST'])
def withdraw():
    data = request.json
    account_id = data.get('Account ID')
    amount = float(data.get('Amount'))
    accounts = read_csv(ACCOUNTS_FILE)
    updated = False

    for account in accounts:
        if account[0] == account_id and float(account[8]) >= amount:
            account[8] = str(float(account[8]) - amount)  # Update balance
            updated = True
            break

    if updated:
        write_csv(ACCOUNTS_FILE, accounts)
        logging.info(f"Withdrew ${amount} from account {account_id}")
        return jsonify({"message": f"Withdrew ${amount} successfully"}), 200
    else:
        return jsonify({"error": "Insufficient funds or account not found"}), 400

# Endpoint to handle transfers between accounts
@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.json
    sender_id = data.get('Sender ID')
    receiver_id = data.get('Receiver ID')
    amount = float(data.get('Amount'))
    accounts = read_csv(ACCOUNTS_FILE)
    sender = receiver = None

    for account in accounts:
        if account[0] == sender_id:
            sender = account
        elif account[0] == receiver_id:
            receiver = account

    if sender and receiver and float(sender[8]) >= amount:
        sender[8] = str(float(sender[8]) - amount)
        receiver[8] = str(float(receiver[8]) + amount)
        write_csv(ACCOUNTS_FILE, accounts)
        logging.info(f"Transferred ${amount} from {sender_id} to {receiver_id}")
        return jsonify({"message": f"Transferred ${amount} to account {receiver_id}"}), 200
    else:
        return jsonify({"error": "Transfer failed due to insufficient funds or account not found"}), 400

# Endpoint to generate a one-time card
@app.route('/generate_one_time_card', methods=['POST'])
def generate_one_time_card():
    card_number = ''.join(random.choices(string.digits, k=16))
    expiry_date = f"{random.randint(1, 12):02d}/{random.randint(24, 29)}"
    cvv = ''.join(random.choices(string.digits, k=3))
    logging.info(f"Generated one-time card {card_number} expiring {expiry_date}")
    return jsonify({"Card Number": card_number, "Expiry Date": expiry_date, "CVV": cvv}), 200

# Add additional endpoints as needed for account management, loan applications, etc.

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
