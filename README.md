# Cryptographic Banking Application

## Overview
A secure banking platform that uses advanced cryptography to protect sensitive data and ensure safe transactions.

## Features
- **User Registration and Login**: Secure credentials with SHA-256 hashing.
- **Two-Factor Authentication (TOTP)**: Adds an extra security layer.
- **End-to-End Encryption**: RSA for key exchange and AES for session data.
- **Account Management**: View balances and transfer funds securely.

## Installation

### Prerequisites
- Python 3.8+
- MySQL
- Required Python libraries (install via `requirements.txt`).

### Setup Steps
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/cryptographic-banking-app.git
   cd cryptographic-banking-app
2. **Extract the Public Key**:
   ```bash
   openssl rsa -in private_key.pem -pubout -out public_key.pem
3. **Place the Keys**:
   Save the generated `private_key.pem` and `public_key.pem` files in the `keys` directory located at the root of the project. If the `keys` directory doesn’t exist, create it:
   ```bash
   mkdir keys
4. **Update the `.env` File**:
   Add or update the environment variables in your `.env` file to include the following paths and configurations:
   ```text
   DB_HOST=localhost
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_NAME=banking_app
   SECRET_KEY=your_secret_key
   RSA_PRIVATE_KEY_PATH=keys/private_key.pem
   RSA_PUBLIC_KEY_PATH=keys/public_key.pem
5. **Test the Environment**:
   After setting up the `.env` file and placing the RSA keys, verify that the environment is configured correctly:
   - Run the following command to check the server:
     ```bash
     python server.py
     ```
     - Ensure the server starts without errors and listens on `http://localhost:5000`.

   - Run the client application:
     ```bash
     python client.py
     ```
     - The client GUI should launch and connect to the server successfully.

---

## Debugging Tips
- **Database Connection Issues**:
  - Ensure your MySQL database is running and the credentials in the `.env` file are correct.
  - Test the connection manually using a database client tool or command line:
    ```bash
    mysql -u your_database_user -p banking_app
    ```

- **Key File Errors**:
  - Check that `private_key.pem` and `public_key.pem` exist in the specified paths.
  - If keys are missing or invalid, regenerate them as described earlier.

- **Server Not Responding**:
  - Ensure no other application is using port `5000`.
  - If required, change the port in `server.py`:
    ```python
    app.run(host="0.0.0.0", port=8080)
    ```

---

## Final Notes
1. Always use a secure environment for running the application, especially in production.
2. Regularly update cryptographic keys and secrets to maintain strong security.
3. Monitor application logs to identify and troubleshoot issues.

---
