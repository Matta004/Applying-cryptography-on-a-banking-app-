import tkinter as tk
from tkinter import messagebox
import csv
import os
import random
import string
import pyotp
import qrcode
from PIL import Image, ImageTk

class Account:
    def __init__(self, account_id, name, dob, address, phone, email, gov_id, password, balance=0, initial_balance=0, two_factor_enabled=False, two_factor_secret=None):
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
            self.transaction_history.append(f"Applied for loan of ${amount} at {interest_rate}% interest for {term_months} months")
        else:
            raise ValueError("Loan amount must be greater than 0.")

    def calculate_interest(self, rate):
        interest = self.balance * (rate / 100)
        self.balance += interest
        self.transaction_history.append(f"Interest of ${interest} added at rate {rate}%")

    def generate_one_time_card(self):
        card_number = ''.join(random.choices(string.digits, k=16))
        expiry_date = f"{random.randint(1, 12)}/{random.randint(24, 29)}"
        cvv = ''.join(random.choices(string.digits, k=3))
        return card_number, expiry_date, cvv

    def check_balance(self):
        return self.balance

class Bank:
    def __init__(self, accounts_file='accounts.csv', transactions_file='transactions.csv', requests_file='account_requests.csv'):
        self.accounts = {}
        self.accounts_file = accounts_file
        self.transactions_file = transactions_file
        self.requests_file = requests_file
        self.load_accounts()

    def load_accounts(self):
        if os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'r') as file:
                reader = csv.reader(file)
                header = next(reader, None)  # Get header
                for row in reader:
                    if len(row) == 12:
                        (account_id, name, dob, address, phone, email, gov_id, password,
                         balance, initial_balance, two_factor_enabled, two_factor_secret) = row
                    elif len(row) == 11:
                        (account_id, name, dob, address, phone, email, gov_id, password,
                         balance, initial_balance, two_factor_enabled) = row
                        two_factor_secret = ''
                    else:
                        # Handle error or skip the row
                        print(f"Skipping row with unexpected number of columns: {len(row)}")
                        continue

                    self.accounts[account_id] = Account(
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

    def create_account_request(self, name, dob, address, phone, email, id_number):
        account_id = self.generate_account_id()
        password = self.generate_random_password()
        file_exists = os.path.isfile(self.requests_file)
        with open(self.requests_file, 'a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Account ID', 'Name', 'DOB', 'Address', 'Phone', 'Email', 'Gov ID', 'Password'])
            writer.writerow([account_id, name, dob, address, phone, email, id_number, password])
        messagebox.showinfo("Request Submitted", f"Your account request has been submitted successfully!\nAccount ID: {account_id}\nPassword: {password}")

    def create_account(self, account_id, name, dob, address, phone, email, id_number, password, initial_balance=0):
        if account_id not in self.accounts:
            self.accounts[account_id] = Account(account_id, name, dob, address, phone, email, id_number, password, initial_balance)
            self.save_accounts_to_file()
        else:
            raise ValueError("Account ID already exists. Please choose a different ID.")

    def save_accounts_to_file(self):
        with open(self.accounts_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Account ID', 'Name', 'DOB', 'Address', 'Phone', 'Email', 'Gov ID', 'Password', 'Balance', 'Initial Balance', 'Two Factor Enabled', 'Two Factor Secret'])
            for account in self.accounts.values():
                writer.writerow([
                    account.account_id,
                    account.name,
                    account.dob,
                    account.address,
                    account.phone,
                    account.email,
                    account.gov_id,
                    account.password,
                    account.balance,
                    account.initial_balance,
                    'True' if account.two_factor_enabled else 'False',
                    account.two_factor_secret or ''
                ])

    def get_account(self, account_id):
        return self.accounts.get(account_id)

    def login(self, account_id, password, two_factor_code=None):
        account = self.get_account(account_id)
        if account and account.password == password:
            if account.two_factor_enabled:
                if not two_factor_code:
                    return '2fa_required'
                else:
                    totp = pyotp.TOTP(account.two_factor_secret)
                    if totp.verify(two_factor_code):
                        return account
                    else:
                        return 'invalid_2fa'
            else:
                return '2fa_setup_required'
        else:
            return None

    # Utility functions
    def generate_account_id(self):
        return ''.join(random.choices(string.digits, k=10))

    def generate_random_password(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=18))

class BankApp:
    def __init__(self, root, bank):
        self.bank = bank
        self.current_account = None
        self.root = root
        self.root.title("Banking System")

        # Set the window size and make it centered
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")

        # Load the background image
        self.load_background_image()

        # Start with the login screen
        self.show_login_screen()

    def load_background_image(self):
        try:
            self.background_image = Image.open("banklogo.jpg")  # Replace with your image path
            self.background_photo = ImageTk.PhotoImage(self.background_image.resize((800, 600), Image.LANCZOS))
            self.background_label = tk.Label(self.root, image=self.background_photo)
            self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        except FileNotFoundError:
            print("Background image not found.")

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.load_background_image()

    def show_login_screen(self):
        self.clear_screen()

        login_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        login_frame.place(relx=0.05, rely=0.1, anchor="nw")

        tk.Label(login_frame, text="Account ID:", font=("Arial", 12), bg="#ffffff").grid(row=0, column=0, sticky="w", pady=5)
        self.account_id_entry = tk.Entry(login_frame, font=("Arial", 12), width=25)
        self.account_id_entry.grid(row=0, column=1, pady=5)

        tk.Label(login_frame, text="Password:", font=("Arial", 12), bg="#ffffff").grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = tk.Entry(login_frame, show="*", font=("Arial", 12), width=25)
        self.password_entry.grid(row=1, column=1, pady=5)

        tk.Button(login_frame, text="Login", command=self.login, font=("Arial", 12), width=15, bg="#4caf50", fg="#ffffff").grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(login_frame, text="Request to Open Account", command=self.show_request_account_screen, font=("Arial", 12), width=20, bg="#2196f3", fg="#ffffff").grid(row=3, column=0, columnspan=2, pady=5)

    def login(self):
        account_id = self.account_id_entry.get()
        password = self.password_entry.get()
        account_or_status = self.bank.login(account_id, password)
        if account_or_status == '2fa_required':
            self.account_id = account_id
            self.password = password
            self.show_two_factor_prompt()
        elif account_or_status == '2fa_setup_required':
            self.current_account = self.bank.get_account(account_id)
            self.show_two_factor_setup()
        elif account_or_status == 'invalid_2fa':
            messagebox.showerror("Error", "Invalid Two-Factor Authentication code")
        elif account_or_status:
            self.current_account = account_or_status
            self.show_main_menu()
        else:
            messagebox.showerror("Error", "Invalid Account ID or Password")

    def show_two_factor_prompt(self):
        self.clear_screen()
        two_factor_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        two_factor_frame.place(relx=0.5, rely=0.3, anchor="n")

        tk.Label(two_factor_frame, text="Enter Two-Factor Authentication Code:", font=("Arial", 12), bg="#ffffff").pack(pady=5)
        self.two_factor_code_entry = tk.Entry(two_factor_frame, font=("Arial", 12), width=30)
        self.two_factor_code_entry.pack(pady=5)

        tk.Button(two_factor_frame, text="Verify", command=self.verify_two_factor_code, font=("Arial", 12), width=15, bg="#4caf50", fg="#ffffff").pack(pady=5)
        tk.Button(two_factor_frame, text="Back", command=self.show_login_screen, font=("Arial", 12), width=15, bg="#f44336", fg="#ffffff").pack(pady=5)

    def verify_two_factor_code(self):
        two_factor_code = self.two_factor_code_entry.get()
        account_or_status = self.bank.login(self.account_id, self.password, two_factor_code)
        if account_or_status == 'invalid_2fa':
            messagebox.showerror("Error", "Invalid Two-Factor Authentication code")
        elif account_or_status:
            self.current_account = account_or_status
            self.show_main_menu()
        else:
            messagebox.showerror("Error", "Invalid Account ID or Password")

    def show_two_factor_setup(self):
        self.clear_screen()
        setup_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        setup_frame.place(relx=0.5, rely=0.2, anchor="n")

        tk.Label(setup_frame, text="Two-Factor Authentication Setup", font=("Arial", 16), bg="#ffffff").pack(pady=10)

        # Generate a secret key
        secret = pyotp.random_base32()
        self.current_account.two_factor_secret = secret

        # Generate the provisioning URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=self.current_account.email, issuer_name="MyBankApp")

        # Generate QR code
        qr_img = qrcode.make(provisioning_uri)
        qr_img = qr_img.resize((200, 200), Image.LANCZOS)
        qr_photo = ImageTk.PhotoImage(qr_img)
        qr_label = tk.Label(setup_frame, image=qr_photo)
        qr_label.image = qr_photo  # Keep a reference
        qr_label.pack(pady=5)

        tk.Label(setup_frame, text="Scan this QR code with your Microsoft Authenticator app.", font=("Arial", 12), bg="#ffffff").pack(pady=5)
        tk.Label(setup_frame, text="Then enter the code generated by the app below:", font=("Arial", 12), bg="#ffffff").pack(pady=5)

        self.two_factor_code_entry = tk.Entry(setup_frame, font=("Arial", 12), width=30)
        self.two_factor_code_entry.pack(pady=5)

        tk.Button(setup_frame, text="Verify", command=self.verify_two_factor_setup_code, font=("Arial", 12), width=15, bg="#4caf50", fg="#ffffff").pack(pady=5)
        tk.Button(setup_frame, text="Back", command=self.show_login_screen, font=("Arial", 12), width=15, bg="#f44336", fg="#ffffff").pack(pady=5)

    def verify_two_factor_setup_code(self):
        two_factor_code = self.two_factor_code_entry.get()
        totp = pyotp.TOTP(self.current_account.two_factor_secret)
        if totp.verify(two_factor_code):
            self.current_account.two_factor_enabled = True
            self.bank.save_accounts_to_file()
            messagebox.showinfo("Success", "Two-Factor Authentication setup complete.")
            self.show_main_menu()
        else:
            messagebox.showerror("Error", "Invalid code. Please try again.")

    def show_request_account_screen(self):
        self.clear_screen()

        request_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        request_frame.place(relx=0.5, rely=0.2, anchor="n")

        tk.Label(request_frame, text="Name:", font=("Arial", 12), bg="#ffffff").grid(row=0, column=0, sticky="w", pady=5)
        self.new_account_name_entry = tk.Entry(request_frame, font=("Arial", 12), width=30)
        self.new_account_name_entry.grid(row=0, column=1, pady=5)

        tk.Label(request_frame, text="Date of Birth:", font=("Arial", 12), bg="#ffffff").grid(row=1, column=0, sticky="w", pady=5)
        self.new_account_dob_day = tk.Spinbox(request_frame, from_=1, to=31, width=5, font=("Arial", 12))
        self.new_account_dob_day.grid(row=1, column=1, sticky="w")
        self.new_account_dob_month = tk.Spinbox(request_frame, from_=1, to=12, width=5, font=("Arial", 12))
        self.new_account_dob_month.grid(row=1, column=1, padx=60, sticky="w")
        self.new_account_dob_year = tk.Spinbox(request_frame, from_=1900, to=2023, width=8, font=("Arial", 12))
        self.new_account_dob_year.grid(row=1, column=1, padx=120, sticky="w")

        tk.Label(request_frame, text="Address:", font=("Arial", 12), bg="#ffffff").grid(row=2, column=0, sticky="w", pady=5)
        self.new_account_address_entry = tk.Entry(request_frame, font=("Arial", 12), width=30)
        self.new_account_address_entry.grid(row=2, column=1, pady=5)

        tk.Label(request_frame, text="Phone Number:", font=("Arial", 12), bg="#ffffff").grid(row=3, column=0, sticky="w", pady=5)
        self.new_account_phone_entry = tk.Entry(request_frame, font=("Arial", 12), width=30)
        self.new_account_phone_entry.grid(row=3, column=1, pady=5)

        tk.Label(request_frame, text="Email Address:", font=("Arial", 12), bg="#ffffff").grid(row=4, column=0, sticky="w", pady=5)
        self.new_account_email_entry = tk.Entry(request_frame, font=("Arial", 12), width=30)
        self.new_account_email_entry.grid(row=4, column=1, pady=5)

        tk.Label(request_frame, text="Government ID Number:", font=("Arial", 12), bg="#ffffff").grid(row=5, column=0, sticky="w", pady=5)
        self.new_account_id_number_entry = tk.Entry(request_frame, font=("Arial", 12), width=30)
        self.new_account_id_number_entry.grid(row=5, column=1, pady=5)

        tk.Button(request_frame, text="Submit Request", command=self.request_account, font=("Arial", 12), width=20, bg="#4caf50", fg="#ffffff").grid(row=6, column=0, columnspan=2, pady=10)
        tk.Button(request_frame, text="Back", command=self.show_login_screen, font=("Arial", 12), width=20, bg="#f44336", fg="#ffffff").grid(row=7, column=0, columnspan=2, pady=5)

    def request_account(self):
        name = self.new_account_name_entry.get()
        dob = f"{self.new_account_dob_year.get()}-{self.new_account_dob_month.get()}-{self.new_account_dob_day.get()}"
        address = self.new_account_address_entry.get()
        phone = self.new_account_phone_entry.get()
        email = self.new_account_email_entry.get()
        id_number = self.new_account_id_number_entry.get()
        try:
            self.bank.create_account_request(name, dob, address, phone, email, id_number)
            self.show_login_screen()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_main_menu(self):
        self.clear_screen()

        main_menu_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        main_menu_frame.place(relx=0.5, rely=0.3, anchor="n")

        tk.Label(main_menu_frame, text=f"Welcome, {self.current_account.name}", font=("Arial", 16), bg="#ffffff").pack(pady=10)
        tk.Button(main_menu_frame, text="Check Balance", command=self.check_balance, font=("Arial", 12), width=20, bg="#2196f3", fg="#ffffff").pack(pady=5)
        tk.Button(main_menu_frame, text="Deposit", command=self.show_deposit_screen, font=("Arial", 12), width=20, bg="#4caf50", fg="#ffffff").pack(pady=5)
        tk.Button(main_menu_frame, text="Withdraw", command=self.show_withdraw_screen, font=("Arial", 12), width=20, bg="#ff9800", fg="#ffffff").pack(pady=5)
        tk.Button(main_menu_frame, text="Transfer Money", command=self.show_transfer_screen, font=("Arial", 12), width=20, bg="#9c27b0", fg="#ffffff").pack(pady=5)
        tk.Button(main_menu_frame, text="Apply for Loan", command=self.show_loan_screen, font=("Arial", 12), width=20, bg="#ff5722", fg="#ffffff").pack(pady=5)
        tk.Button(main_menu_frame, text="Change Password", command=self.change_password, font=("Arial", 12), width=20, bg="#f44336", fg="#ffffff").pack(pady=5)
        tk.Button(main_menu_frame, text="Generate One-Time Card", command=self.generate_one_time_card, font=("Arial", 12), width=20, bg="#795548", fg="#ffffff").pack(pady=5)
        tk.Button(main_menu_frame, text="Logout", command=self.logout, font=("Arial", 12), width=20, bg="#f44336", fg="#ffffff").pack(pady=5)

    def check_balance(self):
        balance = self.current_account.check_balance()
        messagebox.showinfo("Balance", f"Your current balance is: ${balance}")

    def show_deposit_screen(self):
        self.clear_screen()

        deposit_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        deposit_frame.place(relx=0.5, rely=0.3, anchor="n")

        tk.Label(deposit_frame, text="Deposit Amount:", font=("Arial", 12), bg="#ffffff").pack(pady=5)
        self.deposit_amount_entry = tk.Entry(deposit_frame, font=("Arial", 12), width=30)
        self.deposit_amount_entry.pack(pady=5)

        tk.Button(deposit_frame, text="Deposit", command=self.deposit, font=("Arial", 12), width=15, bg="#4caf50", fg="#ffffff").pack(pady=5)
        tk.Button(deposit_frame, text="Back", command=self.show_main_menu, font=("Arial", 12), width=15, bg="#f44336", fg="#ffffff").pack(pady=5)

    def deposit(self):
        try:
            amount = float(self.deposit_amount_entry.get())
            if amount <= 0:
                raise ValueError("Deposit amount must be greater than zero.")
            self.current_account.deposit(amount)
            self.bank.save_accounts_to_file()
            messagebox.showinfo("Success", f"Deposited ${amount} successfully.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_withdraw_screen(self):
        self.clear_screen()

        withdraw_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        withdraw_frame.place(relx=0.5, rely=0.3, anchor="n")

        tk.Label(withdraw_frame, text="Withdraw Amount:", font=("Arial", 12), bg="#ffffff").pack(pady=5)
        self.withdraw_amount_entry = tk.Entry(withdraw_frame, font=("Arial", 12), width=30)
        self.withdraw_amount_entry.pack(pady=5)

        tk.Button(withdraw_frame, text="Withdraw", command=self.withdraw, font=("Arial", 12), width=15, bg="#ff9800", fg="#ffffff").pack(pady=5)
        tk.Button(withdraw_frame, text="Back", command=self.show_main_menu, font=("Arial", 12), width=15, bg="#f44336", fg="#ffffff").pack(pady=5)

    def withdraw(self):
        try:
            amount = float(self.withdraw_amount_entry.get())
            self.current_account.withdraw(amount)
            self.bank.save_accounts_to_file()
            messagebox.showinfo("Success", f"Withdrew ${amount} successfully.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_transfer_screen(self):
        self.clear_screen()

        transfer_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        transfer_frame.place(relx=0.5, rely=0.3, anchor="n")

        tk.Label(transfer_frame, text="Receiver Account ID:", font=("Arial", 12), bg="#ffffff").pack(pady=5)
        self.receiver_id_entry = tk.Entry(transfer_frame, font=("Arial", 12), width=30)
        self.receiver_id_entry.pack(pady=5)

        tk.Label(transfer_frame, text="Transfer Amount:", font=("Arial", 12), bg="#ffffff").pack(pady=5)
        self.transfer_amount_entry = tk.Entry(transfer_frame, font=("Arial", 12), width=30)
        self.transfer_amount_entry.pack(pady=5)

        tk.Button(transfer_frame, text="Transfer", command=self.transfer_money, font=("Arial", 12), width=15, bg="#9c27b0", fg="#ffffff").pack(pady=5)
        tk.Button(transfer_frame, text="Back", command=self.show_main_menu, font=("Arial", 12), width=15, bg="#f44336", fg="#ffffff").pack(pady=5)

    def transfer_money(self):
        try:
            receiver_id = self.receiver_id_entry.get()
            amount = float(self.transfer_amount_entry.get())
            receiver_account = self.bank.get_account(receiver_id)
            if not receiver_account:
                raise ValueError("Receiver account not found.")
            self.current_account.transfer(receiver_account, amount)
            self.bank.save_accounts_to_file()
            messagebox.showinfo("Success", f"Transferred ${amount} to account {receiver_id} successfully.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_loan_screen(self):
        self.clear_screen()

        loan_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        loan_frame.place(relx=0.5, rely=0.3, anchor="n")

        tk.Label(loan_frame, text="Loan Amount:", font=("Arial", 12), bg="#ffffff").pack(pady=5)
        self.loan_amount_entry = tk.Entry(loan_frame, font=("Arial", 12), width=30)
        self.loan_amount_entry.pack(pady=5)

        tk.Label(loan_frame, text="Interest Rate (%):", font=("Arial", 12), bg="#ffffff").pack(pady=5)
        self.loan_interest_entry = tk.Entry(loan_frame, font=("Arial", 12), width=30)
        self.loan_interest_entry.pack(pady=5)

        tk.Label(loan_frame, text="Term (Months):", font=("Arial", 12), bg="#ffffff").pack(pady=5)
        self.loan_term_entry = tk.Entry(loan_frame, font=("Arial", 12), width=30)
        self.loan_term_entry.pack(pady=5)

        tk.Button(loan_frame, text="Apply for Loan", command=self.apply_for_loan, font=("Arial", 12), width=15, bg="#ff5722", fg="#ffffff").pack(pady=5)
        tk.Button(loan_frame, text="Back", command=self.show_main_menu, font=("Arial", 12), width=15, bg="#f44336", fg="#ffffff").pack(pady=5)

    def apply_for_loan(self):
        try:
            amount = float(self.loan_amount_entry.get())
            interest_rate = float(self.loan_interest_entry.get())
            term_months = int(self.loan_term_entry.get())
            self.current_account.apply_for_loan(amount, interest_rate, term_months)
            messagebox.showinfo("Success", f"Loan of ${amount} applied successfully at {interest_rate}% interest for {term_months} months.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def change_password(self):
        new_password = self.current_account.change_password()
        self.bank.save_accounts_to_file()
        messagebox.showinfo("Password Changed", f"Your new password is: {new_password}")

    def generate_one_time_card(self):
        card_number, expiry_date, cvv = self.current_account.generate_one_time_card()
        messagebox.showinfo("One-Time Card Generated", f"Card Number: {card_number}\nExpiry Date: {expiry_date}\nCVV: {cvv}")

    def logout(self):
        self.current_account = None
        self.show_login_screen()

# Initialize the GUI application
if __name__ == "__main__":
    bank = Bank()
    root = tk.Tk()

    # Set the bank logo as the icon of the window
    try:
        logo_image = Image.open("banklogo.jpg")  # Replace with the path to your logo image
        logo_photo = ImageTk.PhotoImage(logo_image)
        root.iconphoto(False, logo_photo)
    except FileNotFoundError:
        print("Logo image not found.")

    app = BankApp(root, bank)
    root.mainloop()
