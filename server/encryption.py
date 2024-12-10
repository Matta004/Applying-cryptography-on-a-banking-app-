import base64
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from config import RSA_PRIVATE_KEY, AES_KEY

class EncryptionManager:
    def __init__(self):
        self.private_key = RSA.import_key(RSA_PRIVATE_KEY)
        self.aes_key = AES_KEY.encode('utf-8') if isinstance(AES_KEY, str) else AES_KEY
        self.aes_iv = self.aes_key[:16]

    def rsa_decrypt(self, ciphertext_b64: str) -> bytes:
        ciphertext = base64.b64decode(ciphertext_b64)
        cipher = PKCS1_OAEP.new(self.private_key)
        return cipher.decrypt(ciphertext)

    def aes_encrypt(self, plaintext: bytes) -> str:
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv=self.aes_iv)
        pad_len = 16 - (len(plaintext) % 16)
        plaintext += bytes([pad_len]) * pad_len
        encrypted = cipher.encrypt(plaintext)
        return base64.b64encode(encrypted).decode('utf-8')

    def aes_decrypt(self, ciphertext_b64: str) -> bytes:
        ciphertext = base64.b64decode(ciphertext_b64)
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv=self.aes_iv)
        plaintext = cipher.decrypt(ciphertext)
        pad_len = plaintext[-1]
        return plaintext[:-pad_len]

    @staticmethod
    def base64_encode(data: bytes) -> str:
        return base64.b64encode(data).decode('utf-8')

    @staticmethod
    def base64_decode(data: str) -> bytes:
        return base64.b64decode(data)
