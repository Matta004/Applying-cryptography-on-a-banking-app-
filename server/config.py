import os

# Server configuration
HOST = "0.0.0.0"
PORT = 5000
DEBUG = True

# Database configuration
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "secure_app")

# RSA Keys (Replace with Secure Keys in Production)
RSA_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQBhAJ8G9JQy78HTYsOSjDwKt6ehcVn2b2BDxbiCUy/pqbFGkgjy
ebIPkM185snsStDc5xhubIgr2YFElWulCPKaKDkfCxuchdkfMl/pUF+BcRv2LBd8
lHHi56CDRHMYa0YHqRMF2ZIhZDSzlRqBxgnsIOKaED9OEn4/98aKGlcnFh7doiGw
rBHZ1/dvZ/hdIPBDXmA+LZ4duqXIcLkAXrCTdGvpqF8cDgGh6juOLZ50ANopna6o
nNCFblSpw9H0KU3mTLHx+Kz7E7cAiAVoSn4+6TUneQJm+k1Ceys0MbkzUycMwWrx
QP1C9xw93KSiEOI/sj5V/Ty4seUYVU8/X7I7AgMBAAECggEAQqRrnRqxKmF/11t2
I5uGsJJGb2rxtJYGG+md/qNqOm0j5ujzjqq/A2SnWFUyis1Hu0xlg4+66e1Pmy/Q
uZxxGCnkPIikGp/2cDFqpV9bjhGIdVMLe8J8j7g0lZqUPEWO4jptYEp+08QFVQ9u
G5RUQs7A/7mD1H5uEEKJO14nXClDn4bMHjw53umE6oOj7AkYOElhWgF9vGHiK0YO
05vFcwVBeqtRpjg96y1/U75QBsPcv81kU6Ffn/fXAk2A6vIyLf1I0ValBIdOSsbr
DNEpM7o+8Z/DOAXwwK0S3iGnSxqhH5XqsD5u0PsYu8QFoz/8gpg3hdsaDGqgpJPB
DbTo0QKBgQCvShpVVcu5aepNX69wzt5TqZDhjQZpUs91nr4V7FtqNsOVh0NSKgDG
o72KK9KvL9JBDhHE75IlGMR9ukohHWShsfZ8E/XnlPmNhWSJS8Q2/6JTWSrCbuKi
NZOqbKlAB+IFXeI/am85E1EaHAc5qdmofnetOSYy4XVhrp5+8w9paQKBgQCNqpbi
cCxSwaLC77CfteU0gRhFHbkagKdjazl8I3UgJkNQ6Yo9Ntxq69MJledyiEfYcV8w
M/gHxSjAO0TXNZmS+c4iiyfeUvfGmCVhD2rvfocwhRYk3FtHSPsQhl8louZI5XdF
6zwA/h7dpz66Bb6E18qTCLV+QM4f4hFAw9EGAwKBgQCDcvSQbchagLy9zTWJSPic
kJofKlxWe00sDSDK2/YpjmvZJBgt82WlkIDAruBNk3T+aAiXQHi97PbcueiBMMOY
JhaLMYTEZ4lEwXWFKBY6kDUwf7t7FyBJOBhGQzog1EiAcckKeUxy5rN4+u/IJEEf
A8fHVQX6PeyClioxVSCHkQKBgHIcJ59LhZg/WtA0a4up427QUXFSyMfdO3dsZghl
MzHrQCvLgctfBlqli/7bnWt29JAWefsE0VPI7tMwqnnDNenah7zxY/LD18tCwFEX
LyasP07I1JZqXKfl1D1yTu+s8FtlYhaSrWmLR+d4kKEcgWLVwtl+mVqR7rZlzUni
sNprAoGAI2N1epsGjxaDeQb1Vi2Z/ZaTCBUtxyONryZpcU/B1TO8Xek16tdalZZw
G2D+2bqLYu3xlDig+W+Q6N8uHcSVPDFd2IxBlakISRxK5DXPb38jyjTeDZBX4H8z
jQGfAv0KKSrljOgCI9RBe/yN0VkSggooTq6IF9GCDPtHCmlIrlc=
-----END RSA PRIVATE KEY-----"""

RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBITANBgkqhkiG9w0BAQEFAAOCAQ4AMIIBCQKCAQBhAJ8G9JQy78HTYsOSjDwK
t6ehcVn2b2BDxbiCUy/pqbFGkgjyebIPkM185snsStDc5xhubIgr2YFElWulCPKa
KDkfCxuchdkfMl/pUF+BcRv2LBd8lHHi56CDRHMYa0YHqRMF2ZIhZDSzlRqBxgns
IOKaED9OEn4/98aKGlcnFh7doiGwrBHZ1/dvZ/hdIPBDXmA+LZ4duqXIcLkAXrCT
dGvpqF8cDgGh6juOLZ50ANopna6onNCFblSpw9H0KU3mTLHx+Kz7E7cAiAVoSn4+
6TUneQJm+k1Ceys0MbkzUycMwWrxQP1C9xw93KSiEOI/sj5V/Ty4seUYVU8/X7I7
AgMBAAE=
-----END PUBLIC KEY-----"""

# AES Key (32 bytes for AES-256)
AES_KEY = os.environ.get("AES_KEY", "32_byte_long_key_for_demo_purpos")

# JWT Secret Key (Replace with a securely generated random key)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "supersecretjwtkey")

# Mail configuration (for email notifications)
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = "kambucharestaurant@gmail.com"
MAIL_PASSWORD = "nguo xchl yxep dfma"  # Consider using an App Password if using Gmail

# 2FA Issuer
TWO_FA_ISSUER = "SecureApp"

# CORS allowed origins (adjust to your actual client origins)
CORS_ALLOWED_ORIGINS = ["http://localhost:5000", "http://156.213.151.70:5000"]
