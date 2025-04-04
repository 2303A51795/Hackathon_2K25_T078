import tkinter as tk
from tkinter import messagebox
import pandas as pd
import os
from datetime import datetime
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS  # PyInstaller temporary folder
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# File paths
DATASET_FILE = resource_path("medicine_data.csv")
USERS_FILE = resource_path("users.csv")
REJECTED_FILE = resource_path("rejected_medicines.csv")

# Ensure necessary files exist
for file, columns in [
    (DATASET_FILE, ["medicine_name", "expiry_date", "is_sealed", "chemical_composition", "std_composition", "barcode", "amount", "batch"]),
    (USERS_FILE, ["username", "password"]),
    (REJECTED_FILE, ["medicine_name", "barcode", "reason", "expiry_date"])
]:
    if not os.path.exists(file):
        pd.DataFrame(columns=columns).to_csv(file, index=False)

# Styles
TITLE_FONT = ("Helvetica", 16, "bold")
LABEL_FONT = ("Helvetica", 12)
BUTTON_STYLE = {"width": 20, "pady": 5}

# ---------------- GUI Functions ---------------- #

def register():
    def save_user():
        username = entry_username.get()
        password = entry_password.get()
        if username and password:
            users = pd.read_csv(USERS_FILE)
            if username in users["username"].values:
                messagebox.showerror("Error", "Username already exists.")
            else:
                users = users._append({"username": username, "password": password}, ignore_index=True)
                users.to_csv(USERS_FILE, index=False)
                messagebox.showinfo("Success", "Registered successfully!")
                register_window.destroy()
        else:
            messagebox.showerror("Error", "Please enter both fields.")

    register_window = tk.Toplevel()
    register_window.title("Register")
    frame = tk.Frame(register_window, padx=20, pady=20)
    frame.pack()

    tk.Label(frame, text="Register", font=TITLE_FONT).pack(pady=10)
    for label_text, var in [("Username", "username"), ("Password", "password")]:
        tk.Label(frame, text=label_text, font=LABEL_FONT).pack(anchor="w")
        entry = tk.Entry(frame, show="*" if label_text == "Password" else "")
        entry.pack(fill="x", pady=5)
        if var == "username":
            entry_username = entry
        else:
            entry_password = entry

    tk.Button(frame, text="Register", command=save_user, **BUTTON_STYLE).pack()

def login():
    def validate():
        username = entry_username.get()
        password = entry_password.get()
        users = pd.read_csv(USERS_FILE)
        if ((users["username"] == username) & (users["password"] == password)).any():
            messagebox.showinfo("Success", "Login successful!")
            login_window.destroy()
            home_page()
        else:
            messagebox.showerror("Error", "Invalid username or password.")

    login_window = tk.Toplevel()
    login_window.title("Login")
    frame = tk.Frame(login_window, padx=20, pady=20)
    frame.pack()

    tk.Label(frame, text="Login", font=TITLE_FONT).pack(pady=10)
    for label_text, var in [("Username", "username"), ("Password", "password")]:
        tk.Label(frame, text=label_text, font=LABEL_FONT).pack(anchor="w")
        entry = tk.Entry(frame, show="*" if label_text == "Password" else "")
        entry.pack(fill="x", pady=5)
        if var == "username":
            entry_username = entry
        else:
            entry_password = entry

    tk.Button(frame, text="Login", command=validate, **BUTTON_STYLE).pack()

def add_medicine():
    def save_medicine():
        try:
            data = {
                "medicine_name": entry_name.get(),
                "expiry_date": entry_expiry.get(),
                "is_sealed": entry_sealed.get(),
                "chemical_composition": float(entry_chem.get()),
                "std_composition": float(entry_std.get()),
                "barcode": entry_barcode.get(),
                "amount": float(entry_amount.get()),
                "batch": entry_batch.get()
            }
            df = pd.read_csv(DATASET_FILE)
            df = df._append(data, ignore_index=True)
            df.to_csv(DATASET_FILE, index=False)
            messagebox.showinfo("Success", "Medicine added successfully!")
            med_window.destroy()
        except:
            messagebox.showerror("Error", "Invalid data entered!")

    med_window = tk.Toplevel()
    med_window.title("Add Medicine")
    frame = tk.Frame(med_window, padx=20, pady=20)
    frame.pack()

    tk.Label(frame, text="Add Medicine", font=TITLE_FONT).pack(pady=10)
    labels = [
        "Medicine Name", "Expiry Date (YYYY-MM-DD)", "Is Sealed (yes/no)",
        "Chemical Composition", "Standard Composition", "Barcode",
        "Amount", "Batch Number"
    ]
    entries = []
    for label in labels:
        tk.Label(frame, text=label, font=LABEL_FONT).pack(anchor="w")
        entry = tk.Entry(frame)
        entry.pack(fill="x", pady=5)
        entries.append(entry)

    (entry_name, entry_expiry, entry_sealed, entry_chem, entry_std,
     entry_barcode, entry_amount, entry_batch) = entries

    tk.Button(frame, text="Save", command=save_medicine, **BUTTON_STYLE).pack(pady=10)

def quality_check():
    df = pd.read_csv(DATASET_FILE)
    if df.empty:
        messagebox.showinfo("Quality Check", "No data available.")
        return

    df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
    today = datetime.today()
    df['composition_ratio'] = (df['chemical_composition'] / df['std_composition']) * 100

    def assign_grade(ratio):
        if ratio >= 95:
            return 'A'
        elif 90 <= ratio < 95:
            return 'B'
        elif 80 <= ratio < 90:
            return 'C'
        else:
            return 'D'

    df['grade'] = df['composition_ratio'].apply(assign_grade)
    rejected_rows = []

    def check(row):
        if row['expiry_date'] < today:
            rejected_rows.append(row)
            return "REJECTED: Expired"
        elif str(row['is_sealed']).strip().lower() != "yes":
            rejected_rows.append(row)
            return "REJECTED: Unsealed"
        elif row['grade'] in ['A', 'B']:
            return "PASS"
        else:
            rejected_rows.append(row)
            return "REJECTED: Low Grade"

    df['quality_status'] = df.apply(check, axis=1)
    df.to_csv(DATASET_FILE, index=False)

    if rejected_rows:
        rejected_df = pd.DataFrame([{
            "medicine_name": row['medicine_name'],
            "barcode": row['barcode'],
            "reason": row['quality_status'].split(":")[1].strip(),
            "expiry_date": row['expiry_date'].strftime('%Y-%m-%d')
        } for row in rejected_rows])
        rejected_df.to_csv(REJECTED_FILE, mode='a', index=False, header=not os.path.exists(REJECTED_FILE))

    # Scrollable results window
    result_window = tk.Toplevel()
    result_window.title("Quality Check Results")

    canvas = tk.Canvas(result_window)
    scrollbar = tk.Scrollbar(result_window, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    tk.Label(scroll_frame, text="Quality Check Results", font=TITLE_FONT).pack(pady=10)
    for _, row in df.iterrows():
        tk.Label(scroll_frame, text=f"{row['medicine_name']} - Grade: {row['grade']} - Status: {row['quality_status']}", font=LABEL_FONT).pack(anchor="w")

def view_rejected():
    if not os.path.exists(REJECTED_FILE) or os.path.getsize(REJECTED_FILE) == 0:
        messagebox.showinfo("Rejected Medicines", "No rejected medicines found.")
        return

    df = pd.read_csv(REJECTED_FILE)
    rejected_window = tk.Toplevel()
    rejected_window.title("Rejected Medicines")

    canvas = tk.Canvas(rejected_window)
    scrollbar = tk.Scrollbar(rejected_window, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    tk.Label(scroll_frame, text="Rejected Medicines", font=TITLE_FONT).pack(pady=10)
    for _, row in df.iterrows():
        tk.Label(scroll_frame, text=f"{row['medicine_name']} | Barcode: {row['barcode']} | Reason: {row['reason']} | Expiry: {row['expiry_date']}", font=LABEL_FONT).pack(anchor="w")

def search_by_barcode():
    def search():
        barcode = entry_barcode.get()
        df = pd.read_csv(DATASET_FILE)
        result = df[df['barcode'] == barcode]
        if not result.empty:
            info = result.to_string(index=False)
            messagebox.showinfo("Medicine Found", info)
        else:
            messagebox.showerror("Not Found", "No medicine found with this barcode.")

    search_window = tk.Toplevel()
    search_window.title("Search Medicine by Barcode")
    frame = tk.Frame(search_window, padx=20, pady=20)
    frame.pack()

    tk.Label(frame, text="Search by Barcode", font=TITLE_FONT).pack(pady=10)
    tk.Label(frame, text="Enter Barcode:", font=LABEL_FONT).pack(anchor="w")
    entry_barcode = tk.Entry(frame)
    entry_barcode.pack(fill="x", pady=5)
    tk.Button(frame, text="Search", command=search, **BUTTON_STYLE).pack(pady=10)

def home_page():
    home = tk.Toplevel()
    home.title("Medicine Quality Monitor")
    frame = tk.Frame(home, padx=40, pady=40)
    frame.pack()

    tk.Label(frame, text="Welcome!", font=TITLE_FONT).pack(pady=10)
    tk.Button(frame, text="Add Medicine", command=add_medicine, **BUTTON_STYLE).pack()
    tk.Button(frame, text="Run Quality Check", command=quality_check, **BUTTON_STYLE).pack()
    tk.Button(frame, text="Search by Barcode", command=search_by_barcode, **BUTTON_STYLE).pack()
    tk.Button(frame, text="View Rejected Medicines", command=view_rejected, **BUTTON_STYLE).pack()

# ---------------- Main Window ---------------- #
root = tk.Tk()
root.title("Medicine Quality Monitoring System")
frame = tk.Frame(root, padx=50, pady=50)
frame.pack()

tk.Label(frame, text="Medicine Quality Monitoring System", font=TITLE_FONT).pack(pady=10)
tk.Button(frame, text="Register", command=register, **BUTTON_STYLE).pack()
tk.Button(frame, text="Login", command=login, **BUTTON_STYLE).pack()

root.mainloop()