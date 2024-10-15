from PIL import Image, ImageTk  # Import Image and ImageTk from Pillow
import tkinter as tk
from tkinter import messagebox
import csv
import os

class Account:
    def __init__(self, account_id, name, initial_balance=0):
        self.account_id = account_id
        self.name = name
        self.balance = initial_balance

class Bank:
    def __init__(self, accounts_file='accounts.csv'):
        self.accounts = {}
        self.accounts_file = accounts_file
        self.load_accounts()

    def create_account(self, account_id, name, initial_balance=0):
        if account_id not in self.accounts:
            self.accounts[account_id] = Account(account_id, name, initial_balance)
            self.save_account_to_file(account_id, name, initial_balance)
        else:
            raise ValueError("Account ID already exists. Please choose a different ID.")

    def remove_account(self, account_id):
        if account_id in self.accounts:
            del self.accounts[account_id]
            self.save_all_accounts_to_file()
        else:
            raise ValueError("Account ID does not exist.")

    def save_account_to_file(self, account_id, name, balance):
        with open(self.accounts_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([account_id, name, balance])

    def save_all_accounts_to_file(self):
        with open(self.accounts_file, 'w', newline='') as file:
            writer = csv.writer(file)
            for account in self.accounts.values():
                writer.writerow([account.account_id, account.name, account.balance])

    def load_accounts(self):
        if os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    account_id, name, balance = row
                    self.accounts[account_id] = Account(account_id, name, float(balance))

class AdminApp:
    def __init__(self, root, bank):
        self.bank = bank
        self.root = root
        self.root.title("Admin Panel - Banking System")

        # Load the background image
        self.load_background_image()

        # Start with the admin main menu screen
        self.show_admin_menu()

    def load_background_image(self):
        # Get the dimensions of the root window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()

        # Open and resize the image to fit the window dimensions
        self.background_image = Image.open("admin_background.jpg")  # Replace with your image path
        self.background_image = self.background_image.resize((width, height), Image.LANCZOS)
        self.background_photo = ImageTk.PhotoImage(self.background_image)

        # Create a label widget to display the image and place it in the background
        self.background_label = tk.Label(self.root, image=self.background_photo)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

    def clear_screen(self):
        # Clear the current screen
        for widget in self.root.winfo_children():
            widget.destroy()
        self.load_background_image()  # Reload the background image for the new screen

    def show_admin_menu(self):
        self.clear_screen()

        tk.Label(self.root, text="Admin Menu", font=("Helvetica", 16)).pack(pady=20)
        tk.Button(self.root, text="Create Account", command=self.show_create_account_screen).pack(pady=10)
        tk.Button(self.root, text="Remove Account", command=self.show_remove_account_screen).pack(pady=10)
        tk.Button(self.root, text="Exit", command=self.root.quit).pack(pady=10)

    def show_create_account_screen(self):
        self.clear_screen()

        tk.Label(self.root, text="Create New Account", font=("Helvetica", 16)).pack(pady=20)
        tk.Label(self.root, text="Account ID:").pack()
        self.new_account_id_entry = tk.Entry(self.root)
        self.new_account_id_entry.pack()

        tk.Label(self.root, text="Name:").pack()
        self.new_account_name_entry = tk.Entry(self.root)
        self.new_account_name_entry.pack()

        tk.Label(self.root, text="Initial Balance:").pack()
        self.new_account_balance_entry = tk.Entry(self.root)
        self.new_account_balance_entry.pack()

        tk.Button(self.root, text="Create Account", command=self.create_account).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.show_admin_menu).pack()

    def create_account(self):
        account_id = self.new_account_id_entry.get()
        name = self.new_account_name_entry.get()
        try:
            initial_balance = float(self.new_account_balance_entry.get())
            self.bank.create_account(account_id, name, initial_balance)
            messagebox.showinfo("Success", "Account created successfully!")
            self.show_admin_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_remove_account_screen(self):
        self.clear_screen()

        tk.Label(self.root, text="Remove Account", font=("Helvetica", 16)).pack(pady=20)
        tk.Label(self.root, text="Account ID:").pack()
        self.remove_account_id_entry = tk.Entry(self.root)
        self.remove_account_id_entry.pack()

        tk.Button(self.root, text="Remove Account", command=self.remove_account).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.show_admin_menu).pack()

    def remove_account(self):
        account_id = self.remove_account_id_entry.get()
        try:
            self.bank.remove_account(account_id)
            messagebox.showinfo("Success", f"Account {account_id} removed successfully!")
            self.show_admin_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

# Initialize the admin GUI application
if __name__ == "__main__":
    bank = Bank()
    root = tk.Tk()
    root.geometry("800x600")  # Set the initial size of the window

    # Set the admin panel logo as the icon of the window
    logo_image = Image.open("admin_logo.jpg")  # Replace with the path to your admin logo image
    logo_photo = ImageTk.PhotoImage(logo_image)
    root.iconphoto(False, logo_photo)

    app = AdminApp(root, bank)
    root.mainloop()
