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
    def __init__(self, server_url="http://mattahome.tplinkdns.com:5000"):
        self.accounts = {}
        self.server_url = server_url
        self.load_accounts()

    def load_accounts(self):
        # Fetch accounts data from the server endpoint
        response = requests.get(f"{self.server_url}/view_accounts")
        if response.status_code == 200:
            csv_content = response.json()["accounts"]
            
            # Skip header row if present
            header = csv_content[0]
            if header[0] == "Account ID":
                csv_content = csv_content[1:]  # Exclude the header

            for row in csv_content:
                if len(row) >= 12:
                    account_id, name, dob, address, phone, email, gov_id, password, balance, initial_balance, two_factor_enabled, two_factor_secret = row[:12]
                elif len(row) >= 11:
                    account_id, name, dob, address, phone, email, gov_id, password, balance, initial_balance, two_factor_enabled = row[:11]
                    two_factor_secret = ''

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
            print("Accounts loaded successfully from server.")
        else:
            print(f"Failed to load accounts data: {response.text}")


    def create_account_request(self, name, dob, address, phone, email, id_number):
        account_id = self.generate_account_id()
        password = self.generate_random_password()
        # Prepare account request data
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
        # Send account request to the server
        response = requests.post(f"{self.server_url}/create_account_request", json=request_data)
        if response.status_code == 200:
            messagebox.showinfo("Request Submitted",
                                f"Your account request has been submitted successfully!\nAccount ID: {account_id}\nPassword: {password}")
        else:
            messagebox.showerror("Error", f"Failed to submit account request: {response.text}")

    def create_account(self, account_id, name, dob, address, phone, email, id_number, password,
                       initial_balance=0):
        if account_id not in self.accounts:
            self.accounts[account_id] = Account(account_id, name, dob, address, phone, email,
                                                id_number, password, initial_balance)
            self.save_accounts_to_server()
        else:
            raise ValueError("Account ID already exists. Please choose a different ID.")

    def save_accounts_to_server(self):
        # Convert accounts data to CSV format
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ['Account ID', 'Name', 'DOB', 'Address', 'Phone', 'Email', 'Gov ID', 'Password',
             'Balance', 'Initial Balance', 'Two Factor Enabled', 'Two Factor Secret'])
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
        csv_data = output.getvalue()
        # Send the CSV data to the server
        response = requests.post(f"{self.server_url}/save_accounts", data=csv_data)
        if response.status_code == 200:
            print("Accounts data saved successfully to server.")
        else:
            print(f"Failed to save accounts data: {response.text}")

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
        login_button.grid(row=3, column=0, columnspan=2, pady=15)

        separator = ttk.Separator(login_frame, orient='horizontal')
        separator.grid(row=4, column=0, columnspan=2, sticky='ew', pady=10)

        open_account_button = ttk.Button(login_frame, text="Request to Open Account",
                                         command=self.show_request_account_screen)
        open_account_button.grid(row=5, column=0, columnspan=2, pady=5)

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
        two_factor_frame = ttk.Frame(self.root, padding=20)
        two_factor_frame.place(relx=0.5, rely=0.4, anchor="center")

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

        back_button = ttk.Button(setup_frame, text="Back", command=self.show_login_screen)
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

# Initialize the GUI application
if __name__ == "__main__":
    bank = Bank()
    root = tk.Tk()

    # Set the bank logo as the icon of the window (optional)
    # You can remove or comment out this block if you don't have a logo image
    try:
        logo_image = Image.open("banklogo.jpg")  # Replace with the path to your logo image
        logo_photo = ImageTk.PhotoImage(logo_image)
        root.iconphoto(False, logo_photo)
    except FileNotFoundError:
        print("Logo image not found.")

    app = BankApp(root, bank)
    root.mainloop()
