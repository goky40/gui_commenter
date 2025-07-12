"""
Facebook Auto Commenter with Full GUI Functionality
"""

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
POST_CACHE_FILE = "post_cache.json"
COMMENTS_PER_ACCOUNT = 1

CACHE = {}  # in-memory cache

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
        try:
            comments = json.load(f)
            if isinstance(comments, list):
                return comments
        except:
            pass
        return [line.strip() for line in f.read().splitlines() if line.strip()]

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

def start_driver(proxy=None):
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--headless=new")
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    return webdriver.Chrome(options=options)

def load_post_cache():
    global CACHE
    if CACHE:
        return CACHE
    if os.path.exists(POST_CACHE_FILE):
        with open(POST_CACHE_FILE, "r", encoding="utf-8") as f:
            CACHE = json.load(f)
    return CACHE

def save_post_cache(cache):
    with open(POST_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def comment_on_link(driver, link, comment_text):
    try:
        driver.get(link)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        cache = load_post_cache()
        cached_xpath = cache.get(link)

        xpaths = [cached_xpath] if cached_xpath else [
            '//div[@aria-label="اكتب تعليقًا..."]',
            '//div[@aria-label="Write a comment…"]',
            '//div[@aria-label="Write a comment"]',
            '//div[contains(@aria-label,"تعليق") and @contenteditable="true"]',
            '//div[contains(@aria-label,"comment") and @contenteditable="true"]',
            '//div[@role="textbox" and @contenteditable="true"]'
        ]

        input_area = None
        for xpath in xpaths:
            if not xpath:
                continue
            try:
                input_area = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                if input_area and not cached_xpath:
                    cache[link] = xpath
                    save_post_cache(cache)
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
        time.sleep(1)

        return True
    except Exception as e:
        log(f"❌ فشل التعليق: {e}")
        return False

# === GUI ===
root = tk.Tk()
root.title("Facebook Auto Commenter")
root.geometry("500x750")
root.configure(bg="white")

frame = tk.Frame(root, padx=10, pady=10, bg="white")
frame.pack(fill="both", expand=True)

link_var = tk.StringVar()
tk.Label(frame, text="🔗 رابط المنشور:", bg="white").pack(anchor="w")
tk.Entry(frame, textvariable=link_var).pack(fill="x", pady=5)

history_combo = ttk.Combobox(frame, values=load_history_links())
history_combo.pack(fill="x", pady=5)

def on_history_select(event):
    link_var.set(history_combo.get())

history_combo.bind("<<ComboboxSelected>>", on_history_select)

progress = ttk.Progressbar(frame, length=450, mode="determinate")
progress.pack(pady=10)

def run_comments():
    link = link_var.get().strip()
    if not link:
        return messagebox.showwarning("تنبيه", "يرجى إدخال رابط المنشور.")
    save_history(link)
    accounts = os.listdir(BASE_DIR)
    progress["maximum"] = len(accounts)
    progress["value"] = 0
    for acc in accounts:
        folder = os.path.join(BASE_DIR, acc)
        convert_cookies_txt_to_json(folder)
        cookies_file = os.path.join(folder, "cookies.json")
        proxy = load_proxy(folder)
        comments = load_comments(folder)
        if not comments:
            continue
        driver = start_driver(proxy)
        try:
            load_cookies(driver, cookies_file)
            for _ in range(COMMENTS_PER_ACCOUNT):
                comment = random.choice(comments)
                success = comment_on_link(driver, link, comment)
                update_status(acc, success)
                if success:
                    log(f"✅ [{acc}] تم التعليق: {comment}")
                else:
                    log(f"⚠️ [{acc}] فشل التعليق.")
        finally:
            driver.quit()
        progress["value"] += 1
        root.update_idletasks()

def manage_comments():
    top = tk.Toplevel(root)
    top.title("إدارة تعليقات الحسابات")
    top.geometry("400x400")
    accs = os.listdir(BASE_DIR)

    def on_select(event):
        acc = acc_combo.get()
        folder = os.path.join(BASE_DIR, acc)
        comments = load_comments(folder)
        text_box.delete("1.0", "end")
        text_box.insert("1.0", "\n".join(comments))

    def save_account_comments():
        acc = acc_combo.get()
        folder = os.path.join(BASE_DIR, acc)
        new_comments = [line.strip() for line in text_box.get("1.0", "end").splitlines() if line.strip()]
        save_comments(folder, new_comments)
        messagebox.showinfo("تم الحفظ", "✅ تم حفظ تعليقات الحساب.")

    acc_combo = ttk.Combobox(top, values=accs)
    acc_combo.pack(fill="x", pady=5)
    acc_combo.bind("<<ComboboxSelected>>", on_select)

    text_box = tk.Text(top, height=15)
    text_box.pack(fill="both", expand=True, pady=5)

    tk.Button(top, text="💾 حفظ التعديلات", command=save_account_comments).pack(pady=5)

def create_new_account():
    name = simpledialog.askstring("اسم الحساب الجديد", "أدخل اسم الحساب الجديد:")
    if name:
        folder = os.path.join(BASE_DIR, name)
        os.makedirs(folder, exist_ok=True)
        save_comments(folder, ["تعليق جديد"])
        messagebox.showinfo("✅ تم", f"تم إنشاء الحساب: {name}")

tk.Button(frame, text="🚀 ابدأ التعليق", command=run_comments, bg="#4CAF50", fg="white").pack(pady=10)
tk.Button(frame, text="📜 عرض سجل المنشورات", command=lambda: messagebox.showinfo("السجل", "\n".join(load_history_links())), bg="#2196F3", fg="white").pack(pady=10)
tk.Button(frame, text="📝 إدارة تعليقات الحسابات", command=manage_comments, bg="#FF9800", fg="white").pack(pady=10)
tk.Button(frame, text="➕ إنشاء حساب جديد", command=create_new_account, bg="#9C27B0", fg="white").pack(pady=10)

root.mainloop()
