import tkinter as tk
from tkinter import messagebox
import csv
import os
import random
import string
from PIL import Image, ImageTk

class Account:
    def __init__(self, account_id, name, dob, address, phone, email, gov_id, password, balance=0, initial_balance=0, two_factor_enabled=False, two_factor_code=""):
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
        self.two_factor_enabled = two_factor_enabled
        self.two_factor_code = two_factor_code
        self.transaction_history = []
        self.loans = []

    def generate_two_factor_code(self):
        self.two_factor_code = ''.join(random.choices(string.digits, k=6))
        return self.two_factor_code

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
                next(reader, None)  # Skip header
                for row in reader:
                    account_id, name, dob, address, phone, email, gov_id, password, balance, initial_balance, two_factor_enabled, two_factor_code = row
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
                        two_factor_enabled=two_factor_enabled == "True",
                        two_factor_code=two_factor_code
                    )

    def save_account_to_file(self, account_id, name, dob, address, phone, email, gov_id, password, balance, two_factor_enabled=False, two_factor_code=""):
        file_exists = os.path.isfile(self.accounts_file)
        with open(self.accounts_file, 'a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Account ID', 'Name', 'DOB', 'Address', 'Phone', 'Email', 'Gov ID', 'Password', 'Balance', 'Initial Balance', 'Two Factor Enabled', 'Two Factor Code'])
            writer.writerow([account_id, name, dob, address, phone, email, gov_id, password, balance, balance, two_factor_enabled, two_factor_code])

    def get_account(self, account_id):
        return self.accounts.get(account_id)

    def login(self, account_id, password):
        account = self.get_account(account_id)
        if account and account.password == password:
            return account
        else:
            return None

class BankApp:
    def __init__(self, root, bank):
        self.bank = bank
        self.current_account = None
        self.root = root
        self.root.title("Banking System")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        self.load_background_image()
        self.show_login_screen()

    def load_background_image(self):
        try:
            self.background_image = Image.open("banklogo.jpg")
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

    def login(self):
        account_id = self.account_id_entry.get()
        password = self.password_entry.get()
        account = self.bank.login(account_id, password)
        if account:
            self.current_account = account
            if account.two_factor_enabled:
                self.show_2fa_verification_screen()
            else:
                self.show_2fa_setup_screen()
        else:
            messagebox.showerror("Error", "Invalid Account ID or Password")

    def show_2fa_setup_screen(self):
        self.clear_screen()
        setup_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        setup_frame.place(relx=0.5, rely=0.3, anchor="n")
        tk.Label(setup_frame, text="Two-Factor Authentication Setup", font=("Arial", 16), bg="#ffffff").pack(pady=10)
        tk.Button(setup_frame, text="Enable 2FA", command=self.setup_2fa, font=("Arial", 12), width=20, bg="#4caf50", fg="#ffffff").pack(pady=5)

    def setup_2fa(self):
        code = self.current_account.generate_two_factor_code()
        self.current_account.two_factor_enabled = True
        messagebox.showinfo("2FA Setup", f"Your 2FA code is: {code}")
        self.bank.save_account_to_file(
            self.current_account.account_id, self.current_account.name, self.current_account.dob, 
            self.current_account.address, self.current_account.phone, self.current_account.email, 
            self.current_account.gov_id, self.current_account.password, self.current_account.balance,
            self.current_account.two_factor_enabled, code
        )
        self.show_main_menu()

    def show_2fa_verification_screen(self):
        self.clear_screen()
        verification_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        verification_frame.place(relx=0.5, rely=0.3, anchor="n")
        tk.Label(verification_frame, text="Enter 2FA Code:", font=("Arial", 12), bg="#ffffff").pack(pady=5)
        self.two_factor_entry = tk.Entry(verification_frame, font=("Arial", 12), width=30)
        self.two_factor_entry.pack(pady=5)
        tk.Button(verification_frame, text="Verify", command=self.verify_2fa, font=("Arial", 12), width=15, bg="#4caf50", fg="#ffffff").pack(pady=5)

    def verify_2fa(self):
        entered_code = self.two_factor_entry.get()
        if entered_code == self.current_account.two_factor_code:
            messagebox.showinfo("Success", "2FA Verification successful!")
            self.show_main_menu()
        else:
            messagebox.showerror("Error", "Invalid 2FA code.")

    def show_main_menu(self):
        self.clear_screen()
        main_menu_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        main_menu_frame.place(relx=0.5, rely=0.3, anchor="n")
        tk.Label(main_menu_frame, text=f"Welcome, {self.current_account.name}", font=("Arial", 16), bg="#ffffff").pack(pady=10)
        tk.Button(main_menu_frame, text="Check Balance", command=self.check_balance, font=("Arial", 12), width=20, bg="#2196f3", fg="#ffffff").pack(pady=5)
        # Add other menu options similarly
        tk.Button(main_menu_frame, text="Logout", command=self.logout, font=("Arial", 12), width=20, bg="#f44336", fg="#ffffff").pack(pady=5)

    def logout(self):
        self.current_account = None
        self.show_login_screen()

# Initialize the GUI application
if __name__ == "__main__":
    bank = Bank()
    root = tk.Tk()
    app = BankApp(root, bank)
    root.mainloop()
