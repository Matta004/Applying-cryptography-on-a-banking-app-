import jwt
from functools import wraps
from flask import request, jsonify
from config import JWT_SECRET_KEY
from encryption import EncryptionManager

encryption_manager = EncryptionManager()

def jwt_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization token missing"}), 401
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            request.user_id = payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return wrapper

def decrypt_rsa_data(key: str) -> bytes:
    # key is base64-encoded ciphertext
    return encryption_manager.rsa_decrypt(key)

def decrypt_aes_data(key: str) -> bytes:
    return encryption_manager.aes_decrypt(key)
