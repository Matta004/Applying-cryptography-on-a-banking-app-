import base64
import os
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

class EncryptionManager:
    def __init__(self, server_public_key: str, aes_key: bytes):
        self.server_public_key = server_public_key
        self.aes_key = aes_key
        self.aes_iv = aes_key[:16]  # Derive IV from AES key for demonstration

    @staticmethod
    def load_rsa_public_key(key_data: str):
        return RSA.import_key(key_data)

    def rsa_encrypt(self, plaintext: bytes) -> bytes:
        key = self.load_rsa_public_key(self.server_public_key)
        cipher = PKCS1_OAEP.new(key)
        return cipher.encrypt(plaintext)

    def aes_encrypt(self, plaintext: bytes) -> bytes:
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv=self.aes_iv)
        # PKCS7 padding
        pad_len = 16 - (len(plaintext) % 16)
        plaintext += bytes([pad_len]) * pad_len
        return cipher.encrypt(plaintext)

    def aes_decrypt(self, ciphertext: bytes) -> bytes:
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv=self.aes_iv)
        plaintext = cipher.decrypt(ciphertext)
        # Remove PKCS7 padding
        pad_len = plaintext[-1]
        return plaintext[:-pad_len]

    @staticmethod
    def base64_encode(data: bytes) -> str:
        return base64.b64encode(data).decode('utf-8')

    @staticmethod
    def base64_decode(encoded: str) -> bytes:
        return base64.b64decode(encoded)

