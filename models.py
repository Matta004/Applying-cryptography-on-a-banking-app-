import hashlib
import pyotp
from database import get_db_connection
from encryption import EncryptionManager

encryption_manager = EncryptionManager()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def create_user(username: str, password: str, email: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    pw_hash = hash_password(password)
    encrypted_email = encryption_manager.aes_encrypt(email.encode('utf-8'))

    # Encrypt default balance
    initial_balance = 100.0
    encrypted_balance = encryption_manager.aes_encrypt(str(initial_balance).encode('utf-8'))

    # Generate a TOTP secret
    totp_secret = pyotp.random_base32()

    query = """
    INSERT INTO users (username, password_hash, email, totp_secret, balance)
    VALUES (%s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(query, (username, pw_hash, encrypted_email, totp_secret, encrypted_balance))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error creating user: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_user_by_username(username: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def verify_user_password(username: str, password: str) -> bool:
    user = get_user_by_username(username)
    if not user:
        return False
    return user['password_hash'] == hash_password(password)

def get_user_balance(user_id: int) -> float:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        encrypted_balance = result['balance']
        decrypted_balance = encryption_manager.aes_decrypt(encrypted_balance).decode('utf-8')
        return float(decrypted_balance)
    return 0.0

def update_user_balance(user_id: int, new_balance: float):
    conn = get_db_connection()
    cursor = conn.cursor()
    encrypted_balance = encryption_manager.aes_encrypt(str(new_balance).encode('utf-8'))
    cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (encrypted_balance, user_id))
    conn.commit()
    cursor.close()
    conn.close()


def create_transaction(user_id: int, recipient_username: str, amount: float) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Encrypt transaction details
    recipient_enc = encryption_manager.aes_encrypt(recipient_username.encode('utf-8'))
    amount_str = str(amount)
    amount_enc = encryption_manager.aes_encrypt(amount_str.encode('utf-8'))

    # Insert into transactions table
    query = "INSERT INTO transactions (user_id, recipient, amount) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (user_id, recipient_enc, amount_enc))
        conn.commit()
        return True
    except:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_user_totp_secret(user_id: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT totp_secret FROM users WHERE id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['totp_secret'] if result else None
