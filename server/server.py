from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message
import jwt
import datetime
import pyotp
from config import (HOST, PORT, DEBUG, RSA_PUBLIC_KEY, JWT_SECRET_KEY, MAIL_SERVER, MAIL_PORT, 
                    MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD, CORS_ALLOWED_ORIGINS, TWO_FA_ISSUER)
from models import create_user, verify_user_password, get_user_by_username, get_user_balance, update_user_balance, create_transaction, get_user_totp_secret
from middleware import jwt_required, decrypt_rsa_data, decrypt_aes_data
from encryption import EncryptionManager

app = Flask(__name__)
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD

mail = Mail(app)

# CORS configuration
CORS(app, resources={r"/*": {"origins": CORS_ALLOWED_ORIGINS}})

encryption_manager = EncryptionManager()


@app.route("/public_key", methods=["GET"])
def public_key():
    # Return the server's RSA public key
    return RSA_PUBLIC_KEY, 200


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    # Decrypt RSA-encrypted userdata
    # Expect data: {"userdata": "<base64 RSA encrypted username:password:email>"}
    userdata_enc = data.get("userdata")
    if not userdata_enc:
        return jsonify({"error": "Missing registration data"}), 400

    decrypted = decrypt_rsa_data(userdata_enc)
    decrypted_str = decrypted.decode('utf-8')
    try:
        username, password, email = decrypted_str.split(":")
    except ValueError:
        return jsonify({"error": "Invalid registration data"}), 400

    if create_user(username, password, email):
        return jsonify({"message": "User registered successfully"}), 201
    else:
        return jsonify({"error": "User registration failed"}), 500


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    # Expect {"credentials": "<base64 RSA encrypted username:password>"}
    creds_enc = data.get("credentials")
    if not creds_enc:
        return jsonify({"error": "Missing credentials"}), 400

    decrypted = decrypt_rsa_data(creds_enc)
    decrypted_str = decrypted.decode('utf-8')

    try:
        username, password = decrypted_str.split(":")
    except ValueError:
        return jsonify({"error": "Invalid credentials"}), 400

    if verify_user_password(username, password):
        user = get_user_by_username(username)
        # Generate JWT token
        exp = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        token = jwt.encode({"user_id": user['id'], "exp": exp}, JWT_SECRET_KEY, algorithm="HS256")
        return jsonify({"token": token, "message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401


@app.route("/balance", methods=["GET"])
@jwt_required
def balance():
    user_id = request.user_id
    user_balance = get_user_balance(user_id)
    # Encrypt balance with AES before sending
    encrypted_balance = encryption_manager.aes_encrypt(str(user_balance).encode('utf-8'))
    return jsonify({"balance": encrypted_balance}), 200


@app.route("/transfer", methods=["POST"])
@jwt_required
def transfer():
    data = request.get_json()
    # Expect {"details": "<base64 AES encrypted recipient:amount>"}
    details_enc = data.get("details")
    if not details_enc:
        return jsonify({"error": "Missing transfer details"}), 400

    decrypted = decrypt_aes_data(details_enc)
    decrypted_str = decrypted.decode('utf-8')
    try:
        recipient, amount_str = decrypted_str.split(":")
        amount = float(amount_str)
    except ValueError:
        return jsonify({"error": "Invalid transfer data"}), 400

    # Check user balance
    user_id = request.user_id
    current_balance = get_user_balance(user_id)
    if current_balance < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    # Deduct from sender, add to recipient if valid
    recipient_user = get_user_by_username(recipient)
    if not recipient_user:
        return jsonify({"error": "Recipient not found"}), 400

    update_user_balance(user_id, current_balance - amount)
    recipient_balance = get_user_balance(recipient_user['id'])
    update_user_balance(recipient_user['id'], recipient_balance + amount)

    # Log transaction
    create_transaction(user_id, recipient, amount)

    return jsonify({"message": "Transfer successful"}), 200


@app.route("/2fa_key", methods=["GET"])
@jwt_required
def two_fa_key():
    # Return the user's 2FA key as a base32 string
    user_id = request.user_id
    totp_secret = get_user_totp_secret(user_id)
    if not totp_secret:
        return jsonify({"error": "2FA not configured"}), 400
    return jsonify({"2fa_key": totp_secret}), 200


@app.route("/2fa_verify", methods=["POST"])
@jwt_required
def two_fa_verify():
    data = request.get_json()
    # Expect {"otp": "123456"}
    otp = data.get("otp")
    if not otp:
        return jsonify({"error": "Missing OTP"}), 400

    user_id = request.user_id
    totp_secret = get_user_totp_secret(user_id)
    if not totp_secret:
        return jsonify({"error": "2FA not configured"}), 400

    totp = pyotp.TOTP(totp_secret)
    if totp.verify(otp):
        return jsonify({"message": "2FA verification successful"}), 200
    else:
        return jsonify({"error": "Invalid OTP"}), 400


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
