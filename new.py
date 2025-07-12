import os
import json
import random
import time
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.join(os.path.dirname(__file__), "accounts_data")
COMMENT_FILE = "comment.txt"
LOG_FILE = "log.txt"
HISTORY_FILE = "history.txt"
STATUS_FILE = "status.json"
COMMENTS_PER_ACCOUNT = 2

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def save_history(link):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {link}\n")

def load_history_links():
    if not os.path.exists(HISTORY_FILE):
        return []
    links = []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                _, link = line.strip().split("|", 1)
                links.append(link.strip())
    return links

def update_status(account, success):
    status = {}
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status = json.load(f)
    status[account] = success
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

def load_comments(folder=None):
    comment_path = os.path.join(folder, COMMENT_FILE) if folder else COMMENT_FILE
    if not os.path.exists(comment_path):
        return ["تعليق افتراضي"]
    with open(comment_path, "r", encoding="utf-8") as f:
        content = f.read()
        try:
            comments = json.loads(content.strip())
            if isinstance(comments, list):
                return comments
        except:
            pass
        return [line.strip() for line in content.splitlines() if line.strip()]

def save_comments(folder, comments_list):
    comment_path = os.path.join(folder, COMMENT_FILE)
    with open(comment_path, "w", encoding="utf-8") as f:
        json.dump(comments_list, f, ensure_ascii=False, indent=2)

def convert_cookies_txt_to_json(folder):
    txt_path = os.path.join(folder, "cookies.txt")
    json_path = os.path.join(folder, "cookies.json")
    if os.path.exists(txt_path):
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
            log(f"✅ تم تحويل cookies.txt إلى cookies.json في: {folder}")
        except Exception as e:
            log(f"❌ فشل تحويل cookies.txt في {folder}: {e}")

def load_cookies(driver, json_path):
    driver.get("https://facebook.com")
    with open(json_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    for cookie in cookies:
        cookie.pop("sameSite", None)
        cookie.pop("expiry", None)
        driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(2)

def load_proxy(folder):
    proxy_file = os.path.join(folder, "proxy.txt")
    if os.path.exists(proxy_file):
        with open(proxy_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def save_proxy(folder, proxy_value):
    proxy_file = os.path.join(folder, "proxy.txt")
    with open(proxy_file, "w", encoding="utf-8") as f:
        f.write(proxy_value.strip())

def start_driver(proxy=None):
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    return webdriver.Chrome(options=options)

def comment_on_link(driver, link, comment_text):
    try:
        driver.get(link)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)

        xpaths = [
            '//div[@aria-label="اكتب تعليقًا..."]',
            '//div[@aria-label="Write a comment…"]',
            '//div[@aria-label="Write a comment"]',
            '//div[contains(@aria-label,"تعليق") and @contenteditable="true"]',
            '//div[contains(@aria-label,"comment") and @contenteditable="true"]',
            '//div[@role="textbox" and @contenteditable="true"]'
        ]

        input_area = None
        for xpath in xpaths:
            try:
                input_area = WebDriverWait(driver, 7).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                if input_area:
                    break
            except:
                continue

        if not input_area:
            raise Exception("❌ لم يتم العثور على حقل التعليق.")

        driver.execute_script("arguments[0].scrollIntoView(true);", input_area)
        time.sleep(1)
        input_area.click()
        input_area.send_keys(comment_text)
        time.sleep(1)
        input_area.send_keys("\n")
        time.sleep(2)

        return True
    except Exception as e:
        log(f"❌ فشل التعليق: {e}")
        return False

def create_new_account():
    new_name = simpledialog.askstring("📁 اسم الحساب الجديد", "أدخل اسم مجلد الحساب الجديد:")
    if not new_name:
        return
    new_folder = os.path.join(BASE_DIR, new_name)
    if os.path.exists(new_folder):
        messagebox.showwarning("⚠️ موجود بالفعل", "هذا الحساب موجود بالفعل.")
        return
    os.makedirs(new_folder, exist_ok=True)
    with open(os.path.join(new_folder, "cookies.txt"), "w", encoding="utf-8") as f:
        f.write("[]")
    with open(os.path.join(new_folder, "proxy.txt"), "w", encoding="utf-8") as f:
        f.write("")
    with open(os.path.join(new_folder, COMMENT_FILE), "w", encoding="utf-8") as f:
        json.dump(["تعليق جديد"], f, ensure_ascii=False, indent=2)
    messagebox.showinfo("✅ تم", f"تم إنشاء حساب {new_name} بنجاح.")

def run_comments():
    link = link_entry.get().strip()
    if not link:
        messagebox.showwarning("❗", "يرجى إدخال رابط المنشور.")
        return

    folders = [os.path.join(BASE_DIR, name) for name in os.listdir(BASE_DIR)
               if os.path.isdir(os.path.join(BASE_DIR, name))]

    if not folders:
        messagebox.showerror("⚠️", "لم يتم العثور على حسابات.")
        return

    progress["value"] = 0
    root.update_idletasks()

    at_least_one_success = False

    for idx, folder in enumerate(folders):
        convert_cookies_txt_to_json(folder)
        cookie_file = os.path.join(folder, "cookies.json")
        account_name = os.path.basename(folder)

        if not os.path.exists(cookie_file):
            log(f"⛔ لا يوجد ملف cookies.json في {folder}")
            update_status(account_name, False)
            continue

        proxy = load_proxy(folder)
        comments = load_comments(folder)

        try:
            driver = start_driver(proxy)
            driver.get("https://facebook.com")
            load_cookies(driver, cookie_file)
            driver.get(link)
            success = False
            for _ in range(COMMENTS_PER_ACCOUNT):
                text = random.choice(comments)
                if comment_on_link(driver, link, text):
                    log(f"✅ [{account_name}] تم التعليق: {text}")
                    success = True
                else:
                    log(f"⚠️ [{account_name}] فشل التعليق.")
            driver.quit()
            update_status(account_name, success)
            if success:
                at_least_one_success = True
        except Exception as e:
            log(f"❌ [{account_name}] خطأ: {e}")
            update_status(account_name, False)

        progress["value"] = ((idx + 1) / len(folders)) * 100
        root.update_idletasks()

    if at_least_one_success:
        save_history(link)

    messagebox.showinfo("تم", "✅ انتهت عملية التعليق من جميع الحسابات.")

# ====== واجهة المستخدم ======
root = tk.Tk()
root.title("🗨️ أداة التعليق التلقائي على فيسبوك")
root.geometry("500x800")
root.configure(bg="white")

frame = tk.Frame(root, bg="white")
frame.pack(padx=20, pady=20, fill="both", expand=True)

link_entry = tk.Entry(frame)
tk.Label(frame, text="🔗 رابط المنشور:", bg="white").pack(anchor="w")
link_entry.pack(fill="x", pady=5)

history_links = load_history_links()
history_combo = ttk.Combobox(frame, values=history_links)

def on_history_select(event):
    link_entry.delete(0, tk.END)
    link_entry.insert(0, history_combo.get())

history_combo.bind("<<ComboboxSelected>>", on_history_select)
history_combo.pack(fill="x", pady=5)

tk.Button(frame, text="🚀 ابدأ التعليق", command=run_comments, bg="#4CAF50", fg="white").pack(pady=10)
progress = ttk.Progressbar(frame, length=450, mode="determinate")
progress.pack(pady=10)

tk.Label(frame, text="🛠️ تحرير بروكسي حساب:", bg="white").pack(anchor="w", pady=(10, 0))
proxy_combo = ttk.Combobox(frame, values=os.listdir(BASE_DIR))
proxy_combo.pack(fill="x", pady=5)

def edit_proxy():
    selected = proxy_combo.get()
    if not selected:
        messagebox.showwarning("تنبيه", "يرجى اختيار مجلد الحساب أولاً")
        return
    folder_path = os.path.join(BASE_DIR, selected)
    old_value = load_proxy(folder_path) or ""
    new_value = simpledialog.askstring("تعديل البروكسي", "أدخل البروكسي الجديد:", initialvalue=old_value)
    if new_value is not None:
        save_proxy(folder_path, new_value)
        messagebox.showinfo("تم", "✅ تم تحديث البروكسي")

def view_history():
    if not os.path.exists(HISTORY_FILE):
        messagebox.showinfo("📜 سجل المنشورات", "لا يوجد سجل حتى الآن.")
        return
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history_data = f.read()
    top = tk.Toplevel(root)
    top.title("📜 سجل المنشورات")
    text = tk.Text(top, wrap="word")
    text.insert("1.0", history_data)
    text.pack(expand=True, fill="both")

def manage_comments():
    top = tk.Toplevel(root)
    top.title("📝 إدارة تعليقات الحسابات")
    top.geometry("400x300")

    account_list = os.listdir(BASE_DIR)
    combo = ttk.Combobox(top, values=account_list)
    combo.pack(fill="x", pady=10)

    text = tk.Text(top, wrap="word")
    text.pack(expand=True, fill="both")

    def load_account_comments(event=None):
        account = combo.get()
        path = os.path.join(BASE_DIR, account)
        if not os.path.isdir(path):
            return
        comments = load_comments(path)
        text.delete("1.0", tk.END)
        for line in comments:
            text.insert(tk.END, line + "\n")

    def save_account_comments():
        account = combo.get()
        path = os.path.join(BASE_DIR, account)
        if not os.path.isdir(path):
            return
        content = text.get("1.0", tk.END).strip().split("\n")
        content = [line.strip() for line in content if line.strip()]
        save_comments(path, content)
        messagebox.showinfo("تم", "✅ تم حفظ التعليقات")

    combo.bind("<<ComboboxSelected>>", load_account_comments)
    tk.Button(top, text="💾 حفظ التعديلات", command=save_account_comments).pack(pady=5)

tk.Button(frame, text="📜 عرض سجل المنشورات", command=view_history, bg="#2196F3", fg="white").pack(pady=10)
tk.Button(frame, text="📝 إدارة تعليقات الحسابات", command=manage_comments, bg="#FF9800", fg="white").pack(pady=10)
tk.Button(frame, text="➕ إنشاء حساب جديد", command=create_new_account, bg="#9C27B0", fg="white").pack(pady=10)

root.mainloop()
