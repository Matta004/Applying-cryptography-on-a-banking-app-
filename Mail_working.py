import smtplib
from email.message import EmailMessage
import tkinter as tk
from tkinter import messagebox
import csv
import os
import random
import string
from PIL import Image, ImageTk
import threading

# Google account credentials
SENDER_EMAIL = "kambucharestaurant@gmail.com"
SENDER_APP_PASSWORD = "nguo xchl yxep dfma"

class Account:
    def __init__(self, account_id, name, initial_balance=0):
        self.account_id = account_id
        self.name = name
        self.balance = initial_balance

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
                try:
                    next(reader)  # Skip the header row
                except StopIteration:
                    return
                for row in reader:
                    account_id, name, dob, address, phone, email, gov_id, password, balance, initial_balance = row
                    self.accounts[account_id] = Account(account_id, name, float(balance))

    def create_account(self, account_id, name, dob, address, phone, email, gov_id, password, initial_balance=0, balance=0):
        if account_id not in self.accounts:
            self.accounts[account_id] = Account(account_id, name, balance)
            self.save_account_to_file(account_id, name, dob, address, phone, email, gov_id, password, initial_balance)
        else:
            raise ValueError("Account ID already exists. Please choose a different ID.")

    def save_account_to_file(self, account_id, name, dob, address, phone, email, gov_id, password, balance, initial_balance=0):
        file_exists = os.path.isfile(self.accounts_file)
        with open(self.accounts_file, 'a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists or os.stat(self.accounts_file).st_size == 0:
                writer.writerow(["Account ID", "Name", "DOB", "Address", "Phone", "Email", "Gov ID", "Password", "Balance", "Initial Balance"])
            writer.writerow([account_id, name, dob, address, phone, email, gov_id, password, balance, initial_balance])

    def load_account_requests(self):
        requests = []
        if os.path.exists(self.requests_file):
            with open(self.requests_file, 'r') as file:
                reader = csv.reader(file)
                try:
                    next(reader)  # Skip the header row
                except StopIteration:
                    return
                for row in reader:
                    requests.append(row)
        return requests

    def delete_account_request(self, account_id):
        requests = self.load_account_requests()
        with open(self.requests_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Account ID", "Name", "DOB", "Address", "Phone", "Email", "Gov ID"])  # Write header row
            for request in requests:
                if request[0] != account_id:
                    writer.writerow(request)

    def send_approval_email(self, email, account_id, password):
        msg = EmailMessage()
        msg.set_content(f"Dear User,\n\nYour account has been approved.\n\nAccount ID: {account_id}\nPassword: {password}\n\nPlease keep this information secure.")
        msg['Subject'] = "Your Account has been Approved"
        msg['From'] = SENDER_EMAIL
        msg['To'] = email

        print("Attempting to send email...")  # Debug statement

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                print("Connecting to SMTP server...")  # Debug statement
                smtp.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                print("Login successful!")  # Debug statement
                smtp.send_message(msg)
            print(f"Email successfully sent to {email} with Account ID: {account_id}")
        except smtplib.SMTPException as e:
            print(f"SMTP error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def accept_request(self, request):
        account_id, name, dob, address, phone, email, gov_id, password = request
        print("Accept request started.")  # Debug statement
        try:
            self.create_account(account_id, name, dob, address, phone, email, gov_id, password, balance=0)
            print("Account created.")  # Debug statement
            self.delete_account_request(account_id)
            print("Account request deleted.")  # Debug statement
            
            # Call email function in a separate thread
            email_thread = threading.Thread(target=self.send_approval_email, args=(email, account_id, password))
            email_thread.start()
            print("send_approval_email called in thread.")  # Debug statement
            
            messagebox.showinfo("Success", f"Account {account_id} created and email sent successfully!")
        except ValueError as e:
            print(f"Error in accept_request: {e}")
            messagebox.showerror("Error", str(e))

class AdminApp:
    def __init__(self, root, bank):
        self.bank = bank
        self.root = root
        self.root.title("Admin Panel - Banking System")

        # Set the window size and make it centered
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")

        # Load the background image
        self.load_background_image()

        # Start with the admin menu screen
        self.show_admin_menu()

    def load_background_image(self):
        try:
            self.background_image = Image.open("admin_background.jpg")  # Replace with your image path
            self.background_photo = ImageTk.PhotoImage(self.background_image.resize((800, 600), Image.LANCZOS))
            self.background_label = tk.Label(self.root, image=self.background_photo)
            self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        except FileNotFoundError:
            print("Background image not found.")

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.load_background_image()

    def show_admin_menu(self):
        self.clear_screen()

        admin_menu_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        admin_menu_frame.place(relx=0.5, rely=0.3, anchor="n")

        tk.Label(admin_menu_frame, text="Admin Menu", font=("Arial", 16), bg="#ffffff").pack(pady=10)
        tk.Button(admin_menu_frame, text="View Account Requests", command=self.show_account_requests_screen, font=("Arial", 12), width=20, bg="#2196f3", fg="#ffffff").pack(pady=5)
        tk.Button(admin_menu_frame, text="Exit", command=self.root.quit, font=("Arial", 12), width=20, bg="#9e9e9e", fg="#ffffff").pack(pady=5)

    def show_account_requests_screen(self):
        self.clear_screen()

        requests_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20, relief="groove", bd=3)
        requests_frame.place(relx=0.5, rely=0.2, anchor="n")

        tk.Label(requests_frame, text="Account Requests", font=("Arial", 16), bg="#ffffff").pack(pady=10)

        requests = self.bank.load_account_requests()
        if requests:
            for request in requests:
                request_frame = tk.Frame(requests_frame, bg="#ffffff", pady=5)
                request_frame.pack(fill="x", padx=10)
                tk.Label(request_frame, text=f"ID: {request[0]}, Name: {request[1]}, DOB: {request[2]}, Address: {request[3]}, Phone: {request[4]}, Email: {request[5]}, Gov ID: {request[6]}", font=("Arial", 10), bg="#ffffff", anchor="w").pack(side="left")
                tk.Button(request_frame, text="Accept", command=lambda req=request: self.accept_request(req), font=("Arial", 10), bg="#4caf50", fg="#ffffff").pack(side="right", padx=5)
        else:
            tk.Label(requests_frame, text="No account requests found.", font=("Arial", 12), bg="#ffffff").pack(pady=5)

        tk.Button(requests_frame, text="Back", command=self.show_admin_menu, font=("Arial", 12), width=20, bg="#f44336", fg="#ffffff").pack(pady=10)

    def accept_request(self, request):
        self.bank.accept_request(request)
        self.root.update()  # Ensure GUI updates after action
        self.show_account_requests_screen()

# Initialize the admin GUI application
if __name__ == "__main__":
    bank = Bank()
    root = tk.Tk()

    # Set the admin panel logo as the icon of the window
    try:
        logo_image = Image.open("admin_logo.jpg")  # Replace with the path to your admin logo image
        logo_photo = ImageTk.PhotoImage(logo_image)
        root.iconphoto(False, logo_photo)
    except FileNotFoundError:
        print("Logo image not found.")

    app = AdminApp(root, bank)
    root.mainloop()
