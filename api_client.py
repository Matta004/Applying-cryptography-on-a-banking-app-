import requests
import os
from encryption import EncryptionManager

class APIClient:
    def __init__(self, base_url: str, encryption_manager: EncryptionManager):
        self.base_url = base_url
        self.encryption = encryption_manager
        self.jwt_token = None

    def set_jwt_token(self, token: str):
        self.jwt_token = token

    def get_headers(self):
        headers = {
            'Content-Type': 'application/json'
        }
        if self.jwt_token:
            headers['Authorization'] = f"Bearer {self.jwt_token}"
        return headers

    def fetch_public_key(self):
        # In a real scenario, fetch from server endpoint: GET /public_key
        # For demonstration, we’ll assume this method is called before init.
        # Example:
        # response = requests.get(f"{self.base_url}/public_key")
        # return response.text
        pass

    def login(self, username: str, password: str):
        # Encrypt credentials with RSA
        credentials = f"{username}:{password}".encode('utf-8')
        encrypted = self.encryption.rsa_encrypt(credentials)
        response = requests.post(
            f"{self.base_url}/login",
            headers=self.get_headers(),
            json={"credentials": self.encryption.base64_encode(encrypted)}
        )
        if response.status_code == 200:
            data = response.json()
            self.jwt_token = data.get('token')
            return True, data.get('message', 'Login successful')
        return False, response.text

    def register(self, username: str, password: str, email: str):
        # Similar to login, RSA encrypt sensitive data
        user_data = f"{username}:{password}:{email}".encode('utf-8')
        encrypted = self.encryption.rsa_encrypt(user_data)
        response = requests.post(
            f"{self.base_url}/register",
            headers=self.get_headers(),
            json={"userdata": self.encryption.base64_encode(encrypted)}
        )
        if response.status_code == 201:
            return True, "Registration successful"
        return False, response.text

    def get_balance(self):
        # Balance is sensitive, encrypted by server
        response = requests.get(f"{self.base_url}/balance", headers=self.get_headers())
        if response.status_code == 200:
            data = response.json()
            encrypted_balance = self.encryption.base64_decode(data['balance'])
            balance = self.encryption.aes_decrypt(encrypted_balance).decode('utf-8')
            return True, balance
        return False, response.text

    def transfer_funds(self, to_user: str, amount: str):
        # Encrypt details with AES
        plaintext = f"{to_user}:{amount}".encode('utf-8')
        encrypted = self.encryption.aes_encrypt(plaintext)
        response = requests.post(
            f"{self.base_url}/transfer",
            headers=self.get_headers(),
            json={"details": self.encryption.base64_encode(encrypted)}
        )
        if response.status_code == 200:
            return True, response.json().get('message', 'Transfer successful')
        return False, response.text

    def fetch_2fa_key(self):
        # For demonstration, just return a mock base64 encoded key
        # In practice, request from server: /2fa_key
        return "MockBase64Encoded2FAKey"
