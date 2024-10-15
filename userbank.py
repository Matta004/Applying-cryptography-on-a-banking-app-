import tkinter as tk
from tkinter import messagebox
import csv
import os
from PIL import Image, ImageTk

class Account:
    def __init__(self, account_id, name, initial_balance=0):
        self.account_id = account_id
        self.name = name
        self.balance = initial_balance

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
        else:
            raise ValueError("Deposit amount must be greater than 0.")

    def withdraw(self, amount):
        if 0 < amount <= self.balance:
            self.balance -= amount
        else:
            raise ValueError("Insufficient funds or invalid amount.")

    def check_balance(self):
        return self.balance

class Bank:
    def __init__(self, accounts_file='accounts.csv', transactions_file='transactions.csv'):
        self.accounts = {}
        self.accounts_file = accounts_file
        self.transactions_file = transactions_file
        self.load_accounts()

    def create_account(self, account_id, name, initial_balance=0):
        if account_id not in self.accounts:
            self.accounts[account_id] = Account(account_id, name, initial_balance)
            self.save_account_to_file(account_id, name, initial_balance)
        else:
            raise ValueError("Account ID already exists. Please choose a different ID.")

    def get_account(self, account_id):
        return self.accounts.get(account_id, None)

    def transfer_money(self, sender_id, receiver_id, amount):
        sender = self.get_account(sender_id)
        receiver = self.get_account(receiver_id)
        if sender and receiver:
            if sender.balance >= amount:
                sender.withdraw(amount)
                receiver.deposit(amount)
                self.save_transaction_to_file(sender_id, receiver_id, amount)
            else:
                raise ValueError("Insufficient funds in the sender's account.")
        else:
            raise ValueError("Invalid sender or receiver account ID.")

    def save_account_to_file(self, account_id, name, balance):
        with open(self.accounts_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([account_id, name, balance])

    def save_transaction_to_file(self, sender_id, receiver_id, amount):
        with open(self.transactions_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([sender_id, receiver_id, amount])

    def load_accounts(self):
        if os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    account_id, name, balance = row
                    self.accounts[account_id] = Account(account_id, name, float(balance))

class BankApp:
    def __init__(self, root, bank):
        self.bank = bank
        self.current_account = None
        self.root = root
        self.root.title("Banking System")

        # Load the background image
        self.load_background_image()

        # Start with the login screen
        self.show_login_screen()

    def load_background_image(self):
        # Load the image using Pillow
        self.background_image = Image.open("banklogo.jpg")  # Replace with your image path
        self.background_photo = ImageTk.PhotoImage(self.background_image)

        # Create a label widget to display the image
        self.background_label = tk.Label(self.root, image=self.background_photo)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

    def clear_screen(self):
        # Hide all widgets, including the background image
        for widget in self.root.winfo_children():
            widget.destroy()
        self.load_background_image()  # Reload the background image for the new screen


    def show_login_screen(self):
        self.clear_screen()

        tk.Label(self.root, text="Account ID:").pack()
        self.account_id_entry = tk.Entry(self.root)
        self.account_id_entry.pack()

        tk.Button(self.root, text="Login", command=self.login).pack()
        tk.Button(self.root, text="Create Account", command=self.show_create_account_screen).pack()

    def login(self):
        account_id = self.account_id_entry.get()
        account = self.bank.get_account(account_id)
        if account:
            self.current_account = account
            self.show_main_menu()
        else:
            messagebox.showerror("Error", "Invalid Account ID")

    def show_create_account_screen(self):
        self.clear_screen()

        tk.Label(self.root, text="New Account ID:").pack()
        self.new_account_id_entry = tk.Entry(self.root)
        self.new_account_id_entry.pack()

        tk.Label(self.root, text="Name:").pack()
        self.new_account_name_entry = tk.Entry(self.root)
        self.new_account_name_entry.pack()

        tk.Label(self.root, text="Initial Balance:").pack()
        self.new_account_balance_entry = tk.Entry(self.root)
        self.new_account_balance_entry.pack()

        tk.Button(self.root, text="Create", command=self.create_account).pack()
        tk.Button(self.root, text="Back", command=self.show_login_screen).pack()

    def create_account(self):
        account_id = self.new_account_id_entry.get()
        name = self.new_account_name_entry.get()
        try:
            initial_balance = float(self.new_account_balance_entry.get())
            self.bank.create_account(account_id, name, initial_balance)
            messagebox.showinfo("Success", "Account created successfully!")
            self.show_login_screen()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_main_menu(self):
        self.clear_screen()

        tk.Label(self.root, text=f"Welcome, {self.current_account.name}").pack()
        tk.Button(self.root, text="Check Balance", command=self.check_balance).pack()
        tk.Button(self.root, text="Deposit", command=self.show_deposit_screen).pack()
        tk.Button(self.root, text="Withdraw", command=self.show_withdraw_screen).pack()
        tk.Button(self.root, text="Transfer Money", command=self.show_transfer_screen).pack()
        tk.Button(self.root, text="Logout", command=self.logout).pack()

    def check_balance(self):
        balance = self.current_account.check_balance()
        messagebox.showinfo("Balance", f"Your current balance is: ${balance}")

    def show_deposit_screen(self):
        self.clear_screen()

        tk.Label(self.root, text="Deposit Amount:").pack()
        self.deposit_amount_entry = tk.Entry(self.root)
        self.deposit_amount_entry.pack()

        tk.Button(self.root, text="Deposit", command=self.deposit).pack()
        tk.Button(self.root, text="Back", command=self.show_main_menu).pack()

    def deposit(self):
        try:
            amount = float(self.deposit_amount_entry.get())
            self.current_account.deposit(amount)
            self.bank.save_account_to_file(self.current_account.account_id, self.current_account.name, self.current_account.balance)
            messagebox.showinfo("Success", f"Deposited ${amount} successfully.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_withdraw_screen(self):
        self.clear_screen()

        tk.Label(self.root, text="Withdraw Amount:").pack()
        self.withdraw_amount_entry = tk.Entry(self.root)
        self.withdraw_amount_entry.pack()

        tk.Button(self.root, text="Withdraw", command=self.withdraw).pack()
        tk.Button(self.root, text="Back", command=self.show_main_menu).pack()

    def withdraw(self):
        try:
            amount = float(self.withdraw_amount_entry.get())
            self.current_account.withdraw(amount)
            self.bank.save_account_to_file(self.current_account.account_id, self.current_account.name, self.current_account.balance)
            messagebox.showinfo("Success", f"Withdrew ${amount} successfully.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_transfer_screen(self):
        self.clear_screen()

        tk.Label(self.root, text="Receiver Account ID:").pack()
        self.receiver_id_entry = tk.Entry(self.root)
        self.receiver_id_entry.pack()

        tk.Label(self.root, text="Transfer Amount:").pack()
        self.transfer_amount_entry = tk.Entry(self.root)
        self.transfer_amount_entry.pack()

        tk.Button(self.root, text="Transfer", command=self.transfer_money).pack()
        tk.Button(self.root, text="Back", command=self.show_main_menu).pack()

    def transfer_money(self):
        try:
            receiver_id = self.receiver_id_entry.get()
            amount = float(self.transfer_amount_entry.get())
            self.bank.transfer_money(self.current_account.account_id, receiver_id, amount)
            self.bank.save_account_to_file(self.current_account.account_id, self.current_account.name, self.current_account.balance)
            messagebox.showinfo("Success", f"Transferred ${amount} to account {receiver_id}.")
            self.show_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def logout(self):
        self.current_account = None
        self.show_login_screen()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

# Initialize the GUI application
if __name__ == "__main__":
    bank = Bank()
    root = tk.Tk()

    # Set the bank logo as the icon of the window
    logo_image = Image.open("banklogo.jpg")  # Replace with the path to your logo image
    logo_photo = ImageTk.PhotoImage(logo_image)
    root.iconphoto(False, logo_photo)

    app = BankApp(root, bank)
    root.mainloop()