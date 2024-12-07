import tkinter as tk
from tkinter import messagebox
import csv
import io
import random
import string
import pyotp
import qrcode
from PIL import Image, ImageTk, ImageDraw
from tkinter import ttk
import requests
import re
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives import serialization
import json

class Account:
    def __init__(self, account_id, name, dob, address, phone, email, gov_id, password,
                 balance=0, initial_balance=0, two_factor_enabled=False, two_factor_secret=None):
        self.account_id = account_id
        self.name = name
        self.dob = dob
        self.address = address
        self.phone = phone
        self.email = email
        self.gov_id = gov_id
        self.password = password
        self.balance = balance
        self.initial_balance = initial_balance
        self.transaction_history = []
        self.loans = []
        self.two_factor_enabled = two_factor_enabled
        self.two_factor_secret = two_factor_secret

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.transaction_history.append(f"Deposited ${amount}")
        else:
            raise ValueError("Deposit amount must be greater than 0.")

    def withdraw(self, amount):
        if 0 < amount <= self.balance:
            self.balance -= amount
            self.transaction_history.append(f"Withdrew ${amount}")
        else:
            raise ValueError("Insufficient funds or invalid amount.")

    def transfer(self, receiver, amount):
        if 0 < amount <= self.balance:
            self.withdraw(amount)
            receiver.deposit(amount)
            self.transaction_history.append(f"Transferred ${amount} to account {receiver.account_id}")
            receiver.transaction_history.append(f"Received ${amount} from account {self.account_id}")
        else:
            raise ValueError("Insufficient funds or invalid amount.")

    def change_password(self):
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=18))
        self.password = new_password
        return new_password

    def apply_for_loan(self, amount, interest_rate, term_months):
        if amount > 0:
            loan_details = {
                "amount": amount,
                "interest_rate": interest_rate,
                "term_months": term_months,
                "monthly_payment": (amount * (1 + interest_rate / 100)) / term_months
            }
            self.loans.append(loan_details)
            self.transaction_history.append(
                f"Applied for loan of ${amount} at {interest_rate}% interest for {term_months} months")
        else:
            raise ValueError("Loan amount must be greater than 0.")

    def calculate_interest(self, rate):
        interest = self.balance * (rate / 100)
        self.balance += interest
        self.transaction_history.append(f"Interest of ${interest} added at rate {rate}%")

    def generate_one_time_card(self):
        card_number = ''.join(random.choices(string.digits, k=16))
        expiry_date = f"{random.randint(1, 12):02d}/{random.randint(24, 29)}"
        cvv = ''.join(random.choices(string.digits, k=3))
        return card_number, expiry_date, cvv

    def check_balance(self):
        return self.balance

class Bank:
    def __init__(self, server_url="http://156.213.92.15:5000"):
        self.server_url = server_url
        self.accounts = {}
        self.current_account = None

        # Load server's public key for encryption
        with open("server_public_key.pem", "rb") as f:
            self.public_key = serialization.load_pem_public_key(f.read())

    def encrypt_data(self, data_str):
        try:
            encrypted = self.public_key.encrypt(
                data_str.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=SHA256()),
                    algorithm=SHA256(),
                    label=None
                )
            )
            return encrypted
        except Exception as e:
            print(f"Encryption error: {e}")
            return None

    def fetch_accounts(self):
        """
        Fetch accounts data from the server.
        """
        response = requests.get(f"{self.server_url}/view_accounts")
        if response.status_code == 200:
            csv_content = response.json()["accounts"]
            self.accounts = self.parse_accounts_csv(csv_content)
            print("Accounts loaded successfully from server.")
        else:
            print(f"Failed to load accounts data: {response.text}")

    def parse_accounts_csv(self, csv_content):
        """
        Parse CSV content into account objects.
        """
        accounts = {}
        for row in csv_content:
            if len(row) >= 12:
                account_id, name, dob, address, phone, email, gov_id, password, balance, initial_balance, two_factor_enabled, two_factor_secret = row
            else:
                raise ValueError("Invalid account data format.")

            accounts[account_id] = Account(
                account_id=account_id,
                name=name,
                dob=dob,
                address=address,
                phone=phone,
                email=email,
                gov_id=gov_id,
                password=password,
                balance=float(balance),
                initial_balance=float(initial_balance),
                two_factor_enabled=(two_factor_enabled.lower() == 'true'),
                two_factor_secret=two_factor_secret or None
            )
        return accounts

    def create_account_request(self, name, dob, address, phone, email, id_number):
            """
            Create a new account request on the server.
            """
            account_id = self.generate_account_id()
            password = self.generate_random_password()
            request_data = {
                'Account ID': account_id,
                'Name': name,
                'DOB': dob,
                'Address': address,
                'Phone': phone,
                'Email': email,
                'Gov ID': id_number,
                'Password': password
            }
            response = requests.post(f"{self.server_url}/create_account_request", json=request_data)
            if response.status_code == 200:
                messagebox.showinfo("Request Submitted",
                                    f"Your account request has been submitted successfully!\n"
                                    f"Account ID: {account_id}\nPassword: {password}")
            else:
                messagebox.showerror("Error", f"Failed to submit account request: {response.text}")

    def secure_login(self, account_id, password, two_factor_code=None):
        """
        Log in to the server with RSA encryption (secure_login endpoint).
        """
        login_data = {
            "Account ID": account_id,
            "Password": password,
            "Two Factor Code": two_factor_code
        }
        data_str = json.dumps(login_data)
        print("Data being encrypted:", data_str)

        encrypted_data = self.encrypt_data(data_str)
        if encrypted_data is None:
            print("Encryption failed.")
            return None

        response = requests.post(f"{self.server_url}/secure_login", data=encrypted_data)
        print("Secure login response:", response.status_code, response.text)

        if response.status_code == 200:
            account_data = response.json()
            self.current_account = Account(
                account_id=account_data['Account ID'],
                name=account_data['Name'],
                dob=account_data['DOB'],
                address=account_data['Address'],
                phone=account_data['Phone'],
                email=account_data['Email'],
                gov_id=account_data['Gov ID'],
                password=account_data['Password'],
                balance=float(account_data['Balance']),
                two_factor_enabled=account_data['Two Factor Enabled'],
                two_factor_secret=account_data['Two Factor Secret']
            )
            return self.current_account
        elif response.status_code == 401:
            if response.json().get("message") == "2fa_required":
                return "2fa_required"
            elif response.json().get("message") == "invalid_2fa":
                return "invalid_2fa"
        return None




    def verify_two_factor_code(self, account_id, password, two_factor_code):
        # Second step: Validate 2FA code
        login_data = {
            "Account ID": account_id,
            "Password": password,
            "Two Factor Code": two_factor_code
        }
        response = requests.post(f"{self.server_url}/verify_two_factor_code", json=login_data)

        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            return False
        else:
            print(f"Error verifying 2FA code: {response.text}")
            return False
        
    def verify_credentials(self, account_id, password):
        # First step: Check credentials
        login_data = {
            "Account ID": account_id,
            "Password": password
        }
        response = requests.post(f"{self.server_url}/verify_credentials", json=login_data)

        if response.status_code == 200:
            account_data = response.json()
            return Account(
                account_id=account_data["Account ID"],
                name=account_data["Name"],
                dob=account_data["DOB"],
                address=account_data["Address"],
                phone=account_data["Phone"],
                email=account_data["Email"],
                gov_id=account_data["Gov ID"],
                password=account_data["Password"],
                balance=account_data["Balance"],
                initial_balance=account_data["Initial Balance"],
                two_factor_enabled=account_data["Two Factor Enabled"],
                two_factor_secret=account_data["Two Factor Secret"]
            )
        elif response.status_code == 401:
            return "invalid_credentials"
        else:
            print(f"Error verifying credentials: {response.text}")
        return None

    def save_accounts_to_server(self):
        """
        Save only the updated account(s) to the server.
        """
        if not self.current_account:
            print("No account logged in to save.")
            return

        account_data = [
            [
                self.current_account.account_id,
                self.current_account.name,
                self.current_account.dob,
                self.current_account.address,
                self.current_account.phone,
                self.current_account.email,
                self.current_account.gov_id,
                self.current_account.password,
                self.current_account.balance,
                self.current_account.initial_balance,
                'True' if self.current_account.two_factor_enabled else 'False',
                self.current_account.two_factor_secret or ''
            ]
        ]

        response = requests.post(f"{self.server_url}/save_accounts", json={"accounts": account_data})
        if response.status_code == 200:
            print("Account changes saved successfully to the server.")
        else:
            print(f"Failed to save account changes: {response.text}")

    # Utility functions
    def generate_account_id(self):
        return ''.join(random.choices(string.digits, k=10))

    def generate_random_password(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=18))

    def get_account(self, account_id):
        return self.accounts.get(account_id)

class BankApp:
    def __init__(self, root, bank):
        self.bank = bank
        self.current_account = None
        self.root = root
        self.root.title("New Capital Bank")

        # Set the window to maximized state
        self.root.state('zoomed')

        self.root.configure(bg="#f0f0f0")

        # Initialize ttk Style
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Set custom styles
        self.style.configure('TFrame', background='#ffffff')
        self.style.configure('TLabel', background='#ffffff', font=('Helvetica', 12))
        self.style.configure('TButton', font=('Helvetica', 12), padding=6)
        self.style.configure('TEntry', font=('Helvetica', 12))
        self.style.configure('Header.TLabel', background='#ffffff', font=('Helvetica', 16, 'bold'))

        # Create gradient background
        self.gradient_photo = None  # Initialize as None
        self.gradient_label = ttk.Label(self.root)
        self.gradient_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.create_gradient_background()

        # Handle window resize to adjust the background
        self.resize_pending = False
        self.root.bind('<Configure>', self.on_resize)

        # Start with the login screen
        self.show_login_screen()

    def create_gradient_background(self):
        # Update the window to get the correct size
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()

        if width <= 1 or height <= 1:
            width = self.root.winfo_screenwidth()
            height = self.root.winfo_screenheight()

        gradient = Image.new('RGB', (width, height), color=0)
        draw = ImageDraw.Draw(gradient)

        # Define start and end colors
        start_color = (6, 83, 52)     # Hex: #065334
        end_color = (255, 227, 80)    # Hex: #FFE350

        for i in range(height):
            ratio = i / height
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            draw.line([(0, i), (width, i)], fill=(r, g, b))

        self.gradient_photo = ImageTk.PhotoImage(gradient)
        self.gradient_label.configure(image=self.gradient_photo)
        self.gradient_label.lower()

    def on_resize(self, event):
        if self.resize_pending:
            return
        self.resize_pending = True
        self.root.after(100, self.resize_background)

    def resize_background(self):
        self.create_gradient_background()
        self.resize_pending = False

    def clear_screen(self):
        for widget in self.root.winfo_children():
            if widget != self.gradient_label:
                widget.destroy()

    def show_login_screen(self):
        self.clear_screen()

        login_frame = ttk.Frame(self.root, padding=30)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(login_frame, text="Welcome to New Capital Bank", style='Header.TLabel').grid(
            row=0, column=0, columnspan=2, pady=10)

        ttk.Label(login_frame, text="Account ID:").grid(row=1, column=0, sticky="e", pady=5)
        self.account_id_entry = ttk.Entry(login_frame, width=30)
        self.account_id_entry.grid(row=1, column=1, pady=5)

        ttk.Label(login_frame, text="Password:").grid(row=2, column=0, sticky="e", pady=5)
        self.password_entry = ttk.Entry(login_frame, show="*", width=30)
        self.password_entry.grid(row=2, column=1, pady=5)

        login_button = ttk.Button(login_frame, text="Login", command=self.login)
        login_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Add a secure login button
        secure_login_button = ttk.Button(login_frame, text="Secure Login (Encrypted)", command=self.secure_login)
        secure_login_button.grid(row=4, column=0, columnspan=2, pady=10)

        separator = ttk.Separator(login_frame, orient='horizontal')
        separator.grid(row=5, column=0, columnspan=2, sticky='ew', pady=10)

        open_account_button = ttk.Button(login_frame, text="Request to Open Account",
                                         command=self.show_request_account_screen)
        open_account_button.grid(row=6, column=0, columnspan=2, pady=5)

    def login(self):
        account_id = self.account_id_entry.get()
        password = self.password_entry.get()

        # Step 1: Check credentials
        account_or_status = self.bank.verify_credentials(account_id, password)

        if isinstance(account_or_status, Account):
            self.current_account = account_or_status

            if self.current_account.two_factor_enabled:
                messagebox.showinfo("Two-Factor Authentication Required",
                                    "Enter your 2FA code to complete the login.")
                self.account_id = account_id  # Save credentials for 2FA step
                self.password = password
                self.show_two_factor_prompt()
            else:
                # No 2FA required
                # Complete login using the standard (unencrypted) login
                result = self.bank.login(account_id, password)
                if isinstance(result, Account):
                    messagebox.showinfo("Success", "Login successful.")
                    self.show_main_menu()
                elif result == "2fa_required":
                    # Should not happen here since we just checked
                    pass
                else:
                    messagebox.showerror("Error", "Login failed unexpectedly.")

        elif account_or_status == "invalid_credentials":
            messagebox.showerror("Error", "Invalid Account ID or Password.")
        else:
            messagebox.showerror("Error", "Unexpected error occurred during login.")

    def secure_login(self):
        account_id = self.account_id_entry.get()
        password = self.password_entry.get()

        # Attempt secure login
        result = self.bank.secure_login(account_id, password)

        if isinstance(result, Account):
            self.current_account = result
            if self.current_account.two_factor_enabled:
                messagebox.showinfo("Two-Factor Authentication Required",
                                    "Enter your 2FA code to complete the login.")
                self.account_id = account_id
                self.password = password
                self.show_two_factor_prompt(secure=True)
            else:
                messagebox.showinfo("Success", "Secure login successful.")
                self.show_main_menu()
        elif result == "2fa_required":
            messagebox.showinfo("Two-Factor Authentication Required",
                                "Enter your 2FA code to complete the login.")
            self.account_id = account_id
            self.password = password
            self.show_two_factor_prompt(secure=True)
        elif result == "invalid_2fa":
            messagebox.showerror("Error", "Invalid 2FA code.")
        else:
            messagebox.showerror("Error", "Secure login failed. Check console for details.")



    def show_two_factor_prompt(self, secure=False):
        self.clear_screen()
        two_factor_frame = ttk.Frame(self.root, padding=20)
        two_factor_frame.place(relx=0.5, rely=0.4, anchor="center")

        self.secure_mode = secure

        ttk.Label(two_factor_frame, text="Two-Factor Authentication",
                  style='Header.TLabel').pack(pady=10)
        ttk.Label(two_factor_frame,
                  text="Enter the code from your authenticator app:").pack(pady=5)
        self.two_factor_code_entry = ttk.Entry(two_factor_frame, width=30)
        self.two_factor_code_entry.pack(pady=5)

        verify_button = ttk.Button(two_factor_frame, text="Verify", command=self.verify_two_factor_code)
        verify_button.pack(pady=10)

        back_button = ttk.Button(two_factor_frame, text="Back", command=self.show_login_screen)
        back_button.pack()

    def verify_two_factor_code(self):
        two_factor_code = self.two_factor_code_entry.get()

        if not two_factor_code.strip():
            messagebox.showerror("Error", "2FA code cannot be empty.")
            return

        # Use secure_login with the 2FA code
        result = self.bank.secure_login(self.account_id, self.password, two_factor_code)

        if isinstance(result, Account):
            self.current_account = result
            messagebox.showinfo("Success", "Login successful.")
            self.show_main_menu()
        elif result == "invalid_2fa":
            messagebox.showerror("Error", "Invalid 2FA code. Please try again.")
        else:
            messagebox.showerror("Error", "Login failed. Check console for details.")


    def show_two_factor_setup(self):
        self.clear_screen()
        setup_frame = ttk.Frame(self.root, padding=20)
        setup_frame.place(relx=0.5, rely=0.3, anchor="center")

        ttk.Label(setup_frame, text="Set Up Two-Factor Authentication",
                style='Header.TLabel').pack(pady=10)

        # Generate a secret key
        secret = pyotp.random_base32()
        self.current_account.two_factor_secret = secret

        # Generate the provisioning URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=self.current_account.email, issuer_name="New Capital Bank")

        # Generate QR code
        qr_img = qrcode.make(provisioning_uri)
        qr_img = qr_img.resize((200, 200), Image.LANCZOS)
        qr_photo = ImageTk.PhotoImage(qr_img)
        qr_label = ttk.Label(setup_frame, image=qr_photo)
        qr_label.image = qr_photo  # Keep a reference
        qr_label.pack(pady=10)

        ttk.Label(setup_frame, text="Scan the QR code with your authenticator app.").pack(pady=5)
        ttk.Label(setup_frame, text="Then enter the code generated by the app below:").pack(pady=5)

        self.two_factor_code_entry = ttk.Entry(setup_frame, width=30)
        self.two_factor_code_entry.pack(pady=5)

        verify_button = ttk.Button(setup_frame, text="Verify", command=self.verify_two_factor_setup_code)
        verify_button.pack(pady=10)

        back_button = ttk.Button(setup_frame, text="Back", command=self.show_main_menu)
        back_button.pack()

    def verify_two_factor_setup_code(self):
        two_factor_code = self.two_factor_code_entry.get()
        totp = pyotp.TOTP(self.current_account.two_factor_secret)
        if totp.verify(two_factor_code):
            self.current_account.two_factor_enabled = True
            self.bank.save_accounts_to_server()
            messagebox.showinfo("Success", "Two-Factor Authentication setup complete.")
            self.show_main_menu()
        else:
            messagebox.showerror("Error", "Invalid code. Please try again.")

    def show_request_account_screen(self):
        self.clear_screen()

        request_frame = ttk.Frame(self.root, padding=20)
        request_frame.place(relx=0.5, rely=0.1, anchor="n")

        ttk.Label(request_frame, text="Open a New Account", style='Header.TLabel').grid(
            row=0, column=0, columnspan=2, pady=10)

        ttk.Label(request_frame, text="Name:").grid(row=1, column=0, sticky="e", pady=5)
        self.new_account_name_entry = ttk.Entry(request_frame, width=30)
        self.new_account_name_entry.grid(row=1, column=1, pady=5)

        ttk.Label(request_frame, text="Date of Birth (YYYY-MM-DD):").grid(row=2, column=0, sticky="e", pady=5)
        self.new_account_dob_entry = ttk.Entry(request_frame, width=30)
        self.new_account_dob_entry.grid(row=2, column=1, pady=5)

        ttk.Label(request_frame, text="Address:").grid(row=3, column=0, sticky="e", pady=5)
        self.new_account_address_entry = ttk.Entry(request_frame, width=30)
        self.new_account_address_entry.grid(row=3, column=1, pady=5)

        ttk.Label(request_frame, text="Phone Number:").grid(row=4, column=0, sticky="e", pady=5)
        self.new_account_phone_entry = ttk.Entry(request_frame, width=30)
        self.new_account_phone_entry.grid(row=4, column=1, pady=5)

        ttk.Label(request_frame, text="Email Address:").grid(row=5, column=0, sticky="e", pady=5)
        self.new_account_email_entry = ttk.Entry(request_frame, width=30)
        self.new_account_email_entry.grid(row=5, column=1, pady=5)

        ttk.Label(request_frame, text="Government ID Number:").grid(row=6, column=0, sticky="e", pady=5)
        self.new_account_id_number_entry = ttk.Entry(request_frame, width=30)
        self.new_account_id_number_entry.grid(row=6, column=1, pady=5)

        submit_button = ttk.Button(request_frame, text="Submit Request", command=self.request_account)
        submit_button.grid(row=7, column=0, columnspan=2, pady=15)

        back_button = ttk.Button(request_frame, text="Back", command=self.show_login_screen)
        back_button.grid(row=8, column=0, columnspan=2)

    def request_account(self):
        name = self.new_account_name_entry.get()
        dob = self.new_account_dob_entry.get()
        address = self.new_account_address_entry.get()
        phone = self.new_account_phone_entry.get()
        email = self.new_account_email_entry.get()
        id_number = self.new_account_id_number_entry.get()

        # Input validation
        if not name.strip():
            messagebox.showerror("Error", "Name cannot be empty.")
            return
        if not self.is_valid_date(dob):
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
            return
        if not address.strip():
            messagebox.showerror("Error", "Address cannot be empty.")
            return
        if not self.is_valid_phone(phone):
            messagebox.showerror("Error", "Invalid phone number. Use digits only (7-15 digits).")
            return
        if not self.is_valid_email(email):
            messagebox.showerror("Error", "Invalid email address.")
            return
        if not id_number.strip():
            messagebox.showerror("Error", "Government ID cannot be empty.")
            return

        try:
            self.bank.create_account_request(name, dob, address, phone, email, id_number)
            self.show_login_screen()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_main_menu(self):
        self.clear_screen()

        main_menu_frame = ttk.Frame(self.root, padding=30)
        main_menu_frame.place(relx=0.5, rely=0.3, anchor="center")

        ttk.Label(main_menu_frame, text=f"Welcome, {self.current_account.name}", style='Header.TLabel').pack(pady=10)

        ttk.Button(main_menu_frame, text="Check Balance", command=self.check_balance).pack(pady=5, fill='x')
        ttk.Button(main_menu_frame, text="Deposit", command=self.show_deposit_screen).pack(pady=5, fill='x')
        ttk.Button(main_menu_frame, text="Withdraw", command=self.show_withdraw_screen).pack(pady=5, fill='x')
        ttk.Button(main_menu_frame, text="Transfer Money", command=self.show_transfer_screen).pack(pady=5, fill='x')
        ttk.Button(main_menu_frame, text="Apply for Loan", command=self.show_loan_screen).pack(pady=5, fill='x')
        ttk.Button(main_menu_frame, text="Change Password", command=self.change_password).pack(pady=5, fill='x')
        ttk.Button(main_menu_frame, text="Generate One-Time Card", command=self.generate_one_time_card).pack(pady=5, fill='x')
        ttk.Button(main_menu_frame, text="Logout", command=self.logout).pack(pady=5, fill='x')

    def check_balance(self):
        balance = self.current_account.check_balance()
        messagebox.showinfo("Balance", f"Your current balance is: ${balance}")

    def show_deposit_screen(self):
        self.clear_screen()

        deposit_frame = ttk.Frame(self.root, padding=20)
        deposit_frame.place(relx=0.5, rely=0.3, anchor="center")

        ttk.Label(deposit_frame, text="Deposit Funds", style='Header.TLabel').pack(pady=10)

        ttk.Label(deposit_frame, text="Amount:").pack(pady=5)
        self.deposit_amount_entry = ttk.Entry(deposit_frame, width=30)
        self.deposit_amount_entry.pack(pady=5)

        deposit_button = ttk.Button(deposit_frame, text="Deposit", command=self.deposit)
        deposit_button.pack(pady=10)

        back_button = ttk.Button(deposit_frame, text="Back", command=self.show_main_menu)
        back_button.pack()

    def deposit(self):
        try:
            amount = float(self.deposit_amount_entry.get())
            if amount <= 0:
                raise ValueError("Deposit amount must be greater than zero.")
            self.current_account.deposit(amount)
            self.bank.save_accounts_to_server()
            messagebox.showinfo("Success", f"Deposited ${amount} successfully.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_withdraw_screen(self):
        self.clear_screen()

        withdraw_frame = ttk.Frame(self.root, padding=20)
        withdraw_frame.place(relx=0.5, rely=0.3, anchor="center")

        ttk.Label(withdraw_frame, text="Withdraw Funds", style='Header.TLabel').pack(pady=10)

        ttk.Label(withdraw_frame, text="Amount:").pack(pady=5)
        self.withdraw_amount_entry = ttk.Entry(withdraw_frame, width=30)
        self.withdraw_amount_entry.pack(pady=5)

        withdraw_button = ttk.Button(withdraw_frame, text="Withdraw", command=self.withdraw)
        withdraw_button.pack(pady=10)

        back_button = ttk.Button(withdraw_frame, text="Back", command=self.show_main_menu)
        back_button.pack()

    def withdraw(self):
        try:
            amount = float(self.withdraw_amount_entry.get())
            self.current_account.withdraw(amount)
            self.bank.save_accounts_to_server()
            messagebox.showinfo("Success", f"Withdrew ${amount} successfully.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_transfer_screen(self):
        self.clear_screen()

        transfer_frame = ttk.Frame(self.root, padding=20)
        transfer_frame.place(relx=0.5, rely=0.3, anchor="center")

        ttk.Label(transfer_frame, text="Transfer Funds", style='Header.TLabel').pack(pady=10)

        ttk.Label(transfer_frame, text="Receiver Account ID:").pack(pady=5)
        self.receiver_id_entry = ttk.Entry(transfer_frame, width=30)
        self.receiver_id_entry.pack(pady=5)

        ttk.Label(transfer_frame, text="Amount:").pack(pady=5)
        self.transfer_amount_entry = ttk.Entry(transfer_frame, width=30)
        self.transfer_amount_entry.pack(pady=5)

        transfer_button = ttk.Button(transfer_frame, text="Transfer", command=self.transfer_money)
        transfer_button.pack(pady=10)

        back_button = ttk.Button(transfer_frame, text="Back", command=self.show_main_menu)
        back_button.pack()

    def transfer_money(self):
        try:
            receiver_id = self.receiver_id_entry.get()
            amount = float(self.transfer_amount_entry.get())
            receiver_account = self.bank.get_account(receiver_id)
            if not receiver_account:
                raise ValueError("Receiver account not found.")
            self.current_account.transfer(receiver_account, amount)
            self.bank.save_accounts_to_server()
            messagebox.showinfo("Success",
                                f"Transferred ${amount} to account {receiver_id} successfully.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_loan_screen(self):
        self.clear_screen()

        loan_frame = ttk.Frame(self.root, padding=20)
        loan_frame.place(relx=0.5, rely=0.3, anchor="center")

        ttk.Label(loan_frame, text="Apply for a Loan", style='Header.TLabel').pack(pady=10)

        ttk.Label(loan_frame, text="Loan Amount:").pack(pady=5)
        self.loan_amount_entry = ttk.Entry(loan_frame, width=30)
        self.loan_amount_entry.pack(pady=5)

        ttk.Label(loan_frame, text="Interest Rate (%):").pack(pady=5)
        self.loan_interest_entry = ttk.Entry(loan_frame, width=30)
        self.loan_interest_entry.pack(pady=5)

        ttk.Label(loan_frame, text="Term (Months):").pack(pady=5)
        self.loan_term_entry = ttk.Entry(loan_frame, width=30)
        self.loan_term_entry.pack(pady=5)

        apply_button = ttk.Button(loan_frame, text="Apply", command=self.apply_for_loan)
        apply_button.pack(pady=10)

        back_button = ttk.Button(loan_frame, text="Back", command=self.show_main_menu)
        back_button.pack()

    def apply_for_loan(self):
        try:
            amount = float(self.loan_amount_entry.get())
            interest_rate = float(self.loan_interest_entry.get())
            term_months = int(self.loan_term_entry.get())
            self.current_account.apply_for_loan(amount, interest_rate, term_months)
            self.bank.save_accounts_to_server()
            messagebox.showinfo("Success",
                                f"Loan of ${amount} applied successfully at {interest_rate}% interest for {term_months} months.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def is_valid_email(self, email):
        """
        Validate email format using regex.
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None

    def is_valid_date(self, date):
        """
        Validate date format YYYY-MM-DD.
        """
        try:
            year, month, day = map(int, date.split('-'))
            assert 1 <= month <= 12
            assert 1 <= day <= 31  # Simplistic check
            return True
        except (ValueError, AssertionError):
            return False

    def is_valid_phone(self, phone):
        """
        Validate phone number (digits only, length 7-15).
        """
        return phone.isdigit() and 7 <= len(phone) <= 15

    def deposit(self):
        try:
            amount = self.deposit_amount_entry.get()
            if not self.is_positive_number(amount):
                raise ValueError("Invalid deposit amount. Enter a positive number.")
            self.current_account.deposit(float(amount))
            self.bank.save_accounts_to_server()
            messagebox.showinfo("Success", f"Deposited ${amount} successfully.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def withdraw(self):
        try:
            amount = self.withdraw_amount_entry.get()
            if not self.is_positive_number(amount):
                raise ValueError("Invalid withdrawal amount. Enter a positive number.")
            self.current_account.withdraw(float(amount))
            self.bank.save_accounts_to_server()
            messagebox.showinfo("Success", f"Withdrew ${amount} successfully.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def transfer_money(self):
        try:
            receiver_id = self.receiver_id_entry.get()
            amount = self.transfer_amount_entry.get()

            if not receiver_id.strip():
                raise ValueError("Receiver account ID cannot be empty.")
            if not self.is_positive_number(amount):
                raise ValueError("Invalid transfer amount. Enter a positive number.")

            receiver_account = self.bank.get_account(receiver_id)
            if not receiver_account:
                raise ValueError("Receiver account not found.")

            self.current_account.transfer(receiver_account, float(amount))
            self.bank.save_accounts_to_server()
            messagebox.showinfo("Success", f"Transferred ${amount} to account {receiver_id} successfully.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def apply_for_loan(self):
        try:
            amount = self.loan_amount_entry.get()
            interest_rate = self.loan_interest_entry.get()
            term_months = self.loan_term_entry.get()

            if not self.is_positive_number(amount):
                raise ValueError("Loan amount must be a positive number.")
            if not self.is_positive_number(interest_rate):
                raise ValueError("Interest rate must be a positive number.")
            if not term_months.isdigit() or int(term_months) <= 0:
                raise ValueError("Term must be a positive integer.")

            self.current_account.apply_for_loan(float(amount), float(interest_rate), int(term_months))
            self.bank.save_accounts_to_server()
            messagebox.showinfo("Success",
                                f"Loan of ${amount} applied successfully at {interest_rate}% interest for {term_months} months.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def change_password(self):
        new_password = self.current_account.change_password()
        self.bank.save_accounts_to_server()
        messagebox.showinfo("Password Changed", f"Your new password is: {new_password}")

    def generate_one_time_card(self):
        card_number, expiry_date, cvv = self.current_account.generate_one_time_card()
        messagebox.showinfo("One-Time Card Generated",
                            f"Card Number: {card_number}\nExpiry Date: {expiry_date}\nCVV: {cvv}")

    def logout(self):
        self.current_account = None
        self.show_login_screen()

    def is_positive_number(self, value):
        try:
            return float(value) > 0
        except ValueError:
            return False

if __name__ == "__main__":
    root = tk.Tk()
    bank = Bank(server_url="http://156.213.92.15:5000")

    # Set the bank logo as the icon of the window (optional)
    try:
        logo_image = Image.open("banklogo.jpg")  # Replace with the path to your logo image if available
        logo_photo = ImageTk.PhotoImage(logo_image)
        root.iconphoto(False, logo_photo)
    except FileNotFoundError:
        print("Logo image not found.")

    app = BankApp(root, bank)
    root.mainloop()
