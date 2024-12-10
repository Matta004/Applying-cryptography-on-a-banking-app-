import os
from encryption import EncryptionManager
from api_client import APIClient
from gui import Application

if __name__ == "__main__":
    # In a real scenario, fetch the public key from the server or a local trusted file.
    # For demonstration, we use a dummy RSA public key (2048-bit) generated beforehand.
    dummy_public_key = """-----BEGIN PUBLIC KEY-----
MIIBITANBgkqhkiG9w0BAQEFAAOCAQ4AMIIBCQKCAQBhAJ8G9JQy78HTYsOSjDwK
t6ehcVn2b2BDxbiCUy/pqbFGkgjyebIPkM185snsStDc5xhubIgr2YFElWulCPKa
KDkfCxuchdkfMl/pUF+BcRv2LBd8lHHi56CDRHMYa0YHqRMF2ZIhZDSzlRqBxgns
IOKaED9OEn4/98aKGlcnFh7doiGwrBHZ1/dvZ/hdIPBDXmA+LZ4duqXIcLkAXrCT
dGvpqF8cDgGh6juOLZ50ANopna6onNCFblSpw9H0KU3mTLHx+Kz7E7cAiAVoSn4+
6TUneQJm+k1Ceys0MbkzUycMwWrxQP1C9xw93KSiEOI/sj5V/Ty4seUYVU8/X7I7
AgMBAAE=
-----END PUBLIC KEY-----"""

    # AES key for demonstration (32 bytes for AES-256)
    aes_key = b'32_byte_long_key_for_demo_purpos'

    encryption_manager = EncryptionManager(server_public_key=dummy_public_key.strip(), aes_key=aes_key)
    
    # Adjust the base_url to match your server address
    # E.g., "http://156.213.92.15:5000"
    base_url = "http://156.213.151.70:5000"

    api_client = APIClient(base_url=base_url, encryption_manager=encryption_manager)

    app = Application(api_client=api_client)
    app.mainloop()
