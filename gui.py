import tkinter as tk
from tkinter import messagebox
from api_client import APIClient
from encryption import EncryptionManager
import base64
from PIL import ImageTk, Image
import io
import qrcode

class Application(tk.Tk):
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.title("Secure Banking Client")
        self.geometry("400x400")
        self.api_client = api_client
        
        # Initialize frames
        self.login_frame = None
        self.dashboard_frame = None
        self.build_login_frame()

    def build_login_frame(self):
        if self.login_frame:
            self.login_frame.destroy()

        self.login_frame = tk.Frame(self)
        self.login_frame.pack(pady=50)

        tk.Label(self.login_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5)
        username_entry = tk.Entry(self.login_frame)
        username_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5)
        password_entry = tk.Entry(self.login_frame, show="*")
        password_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Button(self.login_frame, text="Login", command=lambda: self.handle_login(username_entry.get(), password_entry.get())).grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(self.login_frame, text="Register", command=lambda: self.build_register_frame()).grid(row=3, column=0, columnspan=2, pady=10)

    def build_register_frame(self):
        self.login_frame.destroy()
        register_frame = tk.Frame(self)
        register_frame.pack(pady=50)

        tk.Label(register_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5)
        username_entry = tk.Entry(register_frame)
        username_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(register_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5)
        password_entry = tk.Entry(register_frame, show="*")
        password_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(register_frame, text="Email:").grid(row=2, column=0, padx=5, pady=5)
        email_entry = tk.Entry(register_frame)
        email_entry.grid(row=2, column=1, padx=5, pady=5)

        def register_action():
            success, msg = self.api_client.register(username_entry.get(), password_entry.get(), email_entry.get())
            if success:
                messagebox.showinfo("Success", msg)
                register_frame.destroy()
                self.build_login_frame()
            else:
                messagebox.showerror("Error", msg)

        tk.Button(register_frame, text="Register", command=register_action).grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(register_frame, text="Back", command=lambda: [register_frame.destroy(), self.build_login_frame()]).grid(row=4, column=0, columnspan=2, pady=10)

    def handle_login(self, username: str, password: str):
        success, msg = self.api_client.login(username, password)
        if success:
            messagebox.showinfo("Success", msg)
            self.build_dashboard()
        else:
            messagebox.showerror("Error", msg)

    def build_dashboard(self):
        if self.login_frame:
            self.login_frame.destroy()
        if self.dashboard_frame:
            self.dashboard_frame.destroy()

        self.dashboard_frame = tk.Frame(self)
        self.dashboard_frame.pack(pady=20)

        tk.Button(self.dashboard_frame, text="Check Balance", command=self.check_balance).pack(pady=5)
        tk.Button(self.dashboard_frame, text="Transfer Funds", command=self.build_transfer_frame).pack(pady=5)
        tk.Button(self.dashboard_frame, text="Setup 2FA", command=self.setup_2fa).pack(pady=5)

    def check_balance(self):
        success, data = self.api_client.get_balance()
        if success:
            messagebox.showinfo("Balance", f"Your balance is: {data}")
        else:
            messagebox.showerror("Error", data)

    def build_transfer_frame(self):
        transfer_window = tk.Toplevel(self)
        transfer_window.title("Transfer Funds")

        tk.Label(transfer_window, text="Recipient:").grid(row=0, column=0, padx=5, pady=5)
        recipient_entry = tk.Entry(transfer_window)
        recipient_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(transfer_window, text="Amount:").grid(row=1, column=0, padx=5, pady=5)
        amount_entry = tk.Entry(transfer_window)
        amount_entry.grid(row=1, column=1, padx=5, pady=5)

        def transfer_action():
            success, msg = self.api_client.transfer_funds(recipient_entry.get(), amount_entry.get())
            if success:
                messagebox.showinfo("Success", msg)
                transfer_window.destroy()
            else:
                messagebox.showerror("Error", msg)

        tk.Button(transfer_window, text="Transfer", command=transfer_action).grid(row=2, column=0, columnspan=2, pady=10)

    def setup_2fa(self):
        # Display a QR code for the user. This QR code can represent a TOTP secret key.
        secret_key = self.api_client.fetch_2fa_key()
        qr = qrcode.QRCode()
        qr.add_data(secret_key)
        qr.make()
        img = qr.make_image(fill="black", back_color="white")
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        pil_image = Image.open(bio)
        tk_image = ImageTk.PhotoImage(pil_image)

        top = tk.Toplevel(self)
        top.title("2FA Setup")
        tk.Label(top, text="Scan this QR code with your authenticator app.").pack(pady=10)
        tk.Label(top, image=tk_image).pack()
        top.mainloop()

