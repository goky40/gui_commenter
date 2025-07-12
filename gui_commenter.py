import os
import json
import time
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import re

# === إعداد المسارات ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FOLDER = os.path.join(BASE_DIR, "accounts_data")
CHROMEDRIVER_PATH = os.path.join(BASE_DIR, "chromedriver.exe")
LOG_PATH = os.path.join(BASE_DIR, "log.txt")

# === تسجيل في ملف Log ===
def log(msg):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {msg}\n")
    print(msg)

# === فحص الكوكيز ===
def check_cookies_valid(account_folder):
    cookies_path = os.path.join(account_folder, "cookies.txt")
    if not os.path.exists(cookies_path):
        return False, "لا يوجد ملف cookies."

    with open(cookies_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    required = {"c_user", "xs"}
    found = {cookie['name'] for cookie in cookies}

    if required.issubset(found):
        return True, "✅ الكوكيز تحتوي على بيانات تسجيل الدخول."
    else:
        return False, "❌ الكوكيز ناقصة. لم يتم تسجيل الدخول بشكل صحيح."

# === فحص كل الحسابات عند التشغيل ===
def auto_check_all_cookies():
    log(f"🔍 جاري فحص الكوكيز في: {ACCOUNTS_FOLDER}")
    if not os.path.exists(ACCOUNTS_FOLDER):
        log("❌ مجلد الحسابات غير موجود.")
        return

    invalid_accounts = []
    for folder_name in os.listdir(ACCOUNTS_FOLDER):
        user_folder = os.path.join(ACCOUNTS_FOLDER, folder_name)
        if not os.path.isdir(user_folder):
            continue
        valid, msg = check_cookies_valid(user_folder)
        if not valid:
            log(f"⚠️ الكوكيز غير صالحة للحساب: {folder_name} → {msg}")
            invalid_accounts.append(folder_name)
        else:
            log(f"✅ الكوكيز صالحة للحساب: {folder_name}")

    if invalid_accounts:
        messagebox.showwarning("تحذير الكوكيز", f"تم العثور على حسابات بكوكيز غير صالحة:\n\n" + "\n".join(invalid_accounts))
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

def comment_on_link(link):
    if not link.startswith("http"):
        messagebox.showerror("خطأ", "يرجى إدخال رابط صحيح يبدأ بـ http أو https")
        return

    for folder_name in os.listdir(ACCOUNTS_FOLDER):
        user_folder = os.path.join(ACCOUNTS_FOLDER, folder_name)
        cookies_path = os.path.join(user_folder, "cookies.txt")
        comment_path = os.path.join(user_folder, "comment.txt")

        if not os.path.exists(cookies_path) or not os.path.exists(comment_path):
            log(f"❌ تخطي الحساب: {folder_name} (لا يوجد cookies أو comment.txt)")
            continue

        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        with open(comment_path, "r", encoding="utf-8") as f:
            comment_text = f.read().strip()

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

        try:
            log(f"🔄 محاولة الدخول بحساب: {folder_name}")
            driver.get("https://www.facebook.com/")
            time.sleep(3)

            for cookie in cookies:
                cookie.pop("sameSite", None)
                cookie.pop("expiry", None)
                driver.add_cookie(cookie)

            driver.get("https://www.facebook.com/")
            time.sleep(5)

            if "login" in driver.current_url.lower():
                log(f"❌ فشل الدخول من الكوكيز لحساب: {folder_name}")
                driver.quit()
                continue

            # فتح رابط البوست
            driver.get(link)
            time.sleep(6)
            log(f"🔗 الرابط الحالي بعد التحميل: {driver.current_url}")

            # سحب للأسفل عشان عناصر الصفحة تظهر
            driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(2)

            # نحاول نلاقي كل خانات التعليق الظاهرة
            comment_areas = driver.find_elements(By.XPATH, "//div[@role='textbox']")
            comment_sent = False

            for comment_area in comment_areas:
                try:
                    if comment_area.is_displayed():
                        actions = ActionChains(driver)
                        actions.move_to_element(comment_area).click().perform()
                        time.sleep(1)
                        comment_area.send_keys(comment_text)
                        time.sleep(1)
                        comment_area.send_keys(Keys.RETURN)
                        log(f"✅ تم إرسال التعليق من {folder_name}")
                        comment_sent = True
                        break
                except Exception as e:
                    continue

            if not comment_sent:
                log(f"❌ لم يتم العثور على خانة التعليق الصحيحة في: {folder_name}")
                driver.save_screenshot(os.path.join(user_folder, "not_found.png"))
                with open(os.path.join(user_folder, "page_source.html"), "w", encoding="utf-8") as f:
                    f.write(driver.page_source)

        except Exception as e:
            log(f"⚠️ خطأ أثناء تنفيذ التعليق من {folder_name}: {e}")

        finally:
            driver.quit()

    messagebox.showinfo("انتهى", "✅ تم التعليق من كل الحسابات")

    if not link.startswith("http"):
        messagebox.showerror("خطأ", "يرجى إدخال رابط صحيح يبدأ بـ http أو https")
        return

    for folder_name in os.listdir(ACCOUNTS_FOLDER):
        user_folder = os.path.join(ACCOUNTS_FOLDER, folder_name)
        cookies_path = os.path.join(user_folder, "cookies.txt")
        comment_path = os.path.join(user_folder, "comment.txt")

        if not os.path.exists(cookies_path) or not os.path.exists(comment_path):
            log(f"❌ تخطي الحساب: {folder_name} (لا يوجد cookies أو comment.txt)")
            continue

        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        with open(comment_path, "r", encoding="utf-8") as f:
            comment_text = f.read().strip()

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

        try:
            log(f"🔄 محاولة الدخول بحساب: {folder_name}")
            driver.get("https://www.facebook.com/")
            time.sleep(3)

            for cookie in cookies:
                cookie.pop("sameSite", None)
                cookie.pop("expiry", None)
                driver.add_cookie(cookie)

            driver.get("https://www.facebook.com/")
            time.sleep(5)

            if "login" in driver.current_url.lower():
                log(f"❌ فشل الدخول من الكوكيز لحساب: {folder_name}")
                driver.quit()
                continue

            driver.get(link)
            time.sleep(6)

            # احصل على الرابط الحقيقي بعد التحميل
            real_url = driver.current_url
            log(f"🔗 الرابط الحالي بعد التحميل: {real_url}")

            # لو الرابط اتغير، افتحه تاني عشان نضمن الوصول للمكان الصحيح
            if "share/p/" in link and "permalink.php" in real_url:
                driver.get(real_url)
                time.sleep(5)

            # محاولة الضغط على زر "تعليق"
            try:
                comment_button = driver.find_element(By.XPATH, "//span[text()='تعليق' or text()='Comment']")
                driver.execute_script("arguments[0].click();", comment_button)
                time.sleep(2)
            except:
                pass

            # محاولة إيجاد خانة النص
            try:
                comment_area = driver.find_element(By.XPATH, "//div[@aria-label='اكتب تعليق' or @aria-label='Write a comment']")
            except Exception as e:
                log(f"❌ لم يتم العثور على خانة التعليق الصحيحة في: {folder_name}")
                driver.save_screenshot(os.path.join(user_folder, "not_found.png"))
                with open(os.path.join(user_folder, "page_source.html"), "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                driver.quit()
                continue

            # التركيز ثم إرسال التعليق
            actions = ActionChains(driver)
            actions.move_to_element(comment_area).click().perform()
            time.sleep(1)
            comment_area.send_keys(comment_text)
            time.sleep(1)
            comment_area.send_keys(Keys.RETURN)
            log(f"✅ تم إرسال التعليق من {folder_name}")

        except Exception as e:
            log(f"⚠️ خطأ أثناء تنفيذ التعليق من {folder_name}: {e}")

        finally:
            driver.quit()

    messagebox.showinfo("انتهى", "✅ تم التعليق من كل الحسابات")
    if not link.startswith("http"):
        messagebox.showerror("خطأ", "يرجى إدخال رابط صحيح يبدأ بـ http أو https")
        return

    for folder_name in os.listdir(ACCOUNTS_FOLDER):
        user_folder = os.path.join(ACCOUNTS_FOLDER, folder_name)
        cookies_path = os.path.join(user_folder, "cookies.txt")
        comment_path = os.path.join(user_folder, "comment.txt")

        if not os.path.exists(cookies_path) or not os.path.exists(comment_path):
            log(f"❌ تخطي الحساب: {folder_name} (لا يوجد cookies أو comment.txt)")
            continue

        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        with open(comment_path, "r", encoding="utf-8") as f:
            comment_text = f.read().strip()

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

        try:
            log(f"🔄 محاولة الدخول بحساب: {folder_name}")
            driver.get("https://www.facebook.com/")
            time.sleep(3)

            for cookie in cookies:
                cookie.pop("sameSite", None)
                cookie.pop("expiry", None)
                driver.add_cookie(cookie)

            driver.get(link)
            time.sleep(6)
            log(f"🔗 الرابط الحالي بعد التحميل: {real_url}")
            real_url = driver.current_url
            if "share/p/" in link and "permalink.php" in real_url:
                driver.get(real_url)
                time.sleep(5)

            # انتظر التحويل التلقائي
            final_url = driver.current_url
            log(f"🔗 الرابط الحالي بعد التحويل: {final_url}")

            if "facebook.com/permalink.php" not in final_url:
                log(f"❌ لم يتم التحويل لرابط منشور صالح: {final_url}")
                driver.quit()
                continue

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            # الضغط على زر تعليق إذا وجد
            try:
                comment_button = driver.find_element(By.XPATH, "//span[text()='تعليق' or text()='Comment']")
                driver.execute_script("arguments[0].click();", comment_button)
                time.sleep(2)
            except:
                log("ℹ️ لم يتم العثور على زر 'تعليق'، الاستمرار...")

            # محاولة إيجاد خانة التعليق الأوسع
            try:
                comment_area = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//div[@role='textbox' and @contenteditable='true']"
                    ))
                )
            except Exception as e:
                log(f"❌ لم يتم العثور على خانة التعليق الصحيحة في: {folder_name} ({e})")
                driver.save_screenshot(os.path.join(user_folder, "not_found_comment.png"))
                with open(os.path.join(user_folder, "page_source.html"), "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                driver.quit()
                continue

            # الكتابة والإرسال
            actions = ActionChains(driver)
            actions.move_to_element(comment_area).click().perform()
            time.sleep(1)
            comment_area.send_keys(comment_text)
            time.sleep(1)
            comment_area.send_keys(Keys.RETURN)
            log(f"✅ تم إرسال التعليق من {folder_name}")

        except Exception as e:
            log(f"⚠️ خطأ أثناء تنفيذ التعليق من {folder_name}: {e}")
        finally:
            driver.quit()

    messagebox.showinfo("انتهى", "✅ تم التعليق من كل الحسابات")
    if not link.startswith("http"):
        messagebox.showerror("خطأ", "يرجى إدخال رابط صحيح يبدأ بـ http أو https")
        return

    for folder_name in os.listdir(ACCOUNTS_FOLDER):
        user_folder = os.path.join(ACCOUNTS_FOLDER, folder_name)
        cookies_path = os.path.join(user_folder, "cookies.txt")
        comment_path = os.path.join(user_folder, "comment.txt")

        if not os.path.exists(cookies_path) or not os.path.exists(comment_path):
            log(f"❌ تخطي الحساب: {folder_name} (لا يوجد cookies أو comment.txt)")
            continue

        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        with open(comment_path, "r", encoding="utf-8") as f:
            comment_text = f.read().strip()

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

        try:
            log(f"🔄 محاولة الدخول بحساب: {folder_name}")
            driver.get("https://www.facebook.com/")
            time.sleep(3)

            for cookie in cookies:
                cookie.pop("sameSite", None)
                cookie.pop("expiry", None)
                driver.add_cookie(cookie)

            driver.get(link)
            time.sleep(7)

            current_url = driver.current_url
            log(f"🔗 الرابط الحالي بعد التحميل: {current_url}")

            # Scroll للأسفل لإظهار خانة التعليق
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            try:
                comment_area = driver.find_element(By.XPATH, "//div[@aria-label='اكتب تعليق' or @aria-label='Write a comment']")
            except:
                log(f"❌ لم يتم العثور على خانة التعليق الصحيحة في: {folder_name}")
                driver.save_screenshot(os.path.join(user_folder, "not_found_comment.png"))
                with open(os.path.join(user_folder, "page_source.html"), "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                driver.quit()
                continue

            # كتابة التعليق داخل خانة الإدخال
            actions = ActionChains(driver)
            actions.move_to_element(comment_area).click().perform()
            time.sleep(1)

            comment_area.send_keys(comment_text)
            time.sleep(1)
            comment_area.send_keys(Keys.RETURN)
            log(f"✅ تم إرسال التعليق من {folder_name}")

        except Exception as e:
            log(f"⚠️ خطأ أثناء تنفيذ التعليق من {folder_name}: {e}")

        finally:
            driver.quit()

    messagebox.showinfo("انتهى", "✅ تم التعليق من كل الحسابات")
    if not link.startswith("http"):
        messagebox.showerror("خطأ", "يرجى إدخال رابط صحيح يبدأ بـ http أو https")
        return

    for folder_name in os.listdir(ACCOUNTS_FOLDER):
        user_folder = os.path.join(ACCOUNTS_FOLDER, folder_name)
        cookies_path = os.path.join(user_folder, "cookies.txt")
        comment_path = os.path.join(user_folder, "comment.txt")

        if not os.path.exists(cookies_path) or not os.path.exists(comment_path):
            log(f"❌ تخطي الحساب: {folder_name} (لا يوجد cookies أو comment.txt)")
            continue

        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        with open(comment_path, "r", encoding="utf-8") as f:
            comment_text = f.read().strip()

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

        try:
            log(f"🔄 محاولة الدخول بحساب: {folder_name}")
            driver.get("https://www.facebook.com/")
            time.sleep(3)

            for cookie in cookies:
                cookie.pop("sameSite", None)
                cookie.pop("expiry", None)
                driver.add_cookie(cookie)

            driver.get("https://www.facebook.com/")
            time.sleep(5)

            if "login" in driver.current_url.lower():
                log(f"❌ فشل الدخول من الكوكيز لحساب: {folder_name}")
                driver.quit()
                continue

            driver.get(link)
            time.sleep(7)

            current_url = driver.current_url
            log(f"🔗 الرابط الحالي بعد التحميل: {current_url}")

            # التأكد أن overlay ظهر
            time.sleep(3)

            # إيجاد خانة التعليق داخل overlay (النافذة المنبثقة)
            try:
                comment_area = driver.find_element(By.XPATH, "//div[@aria-label='اكتب تعليق' or @aria-label='Write a comment']")
            except:
                log(f"❌ لم يتم العثور على خانة التعليق الصحيحة في: {folder_name}")
                driver.save_screenshot(os.path.join(user_folder, "not_found_overlay.png"))
                with open(os.path.join(user_folder, "overlay_source.html"), "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                driver.quit()
                continue

            # إرسال التعليق
            actions = ActionChains(driver)
            actions.move_to_element(comment_area).click().perform()
            time.sleep(1)

            driver.execute_script("""
                arguments[0].focus();
                arguments[0].textContent = arguments[1];
                const event = new InputEvent('input', {
                    bubbles: true,
                    cancelable: true,
                    inputType: 'insertText',
                    data: arguments[1]
                });
                arguments[0].dispatchEvent(event);
            """, comment_area, comment_text)

            time.sleep(1)
            comment_area.send_keys(Keys.RETURN)
            log(f"✅ تم إرسال التعليق من {folder_name} على المنشور داخل overlay")

        except Exception as e:
            log(f"⚠️ خطأ أثناء تنفيذ التعليق من {folder_name}: {e}")
        finally:
            driver.quit()

    messagebox.showinfo("انتهى", "✅ تم التعليق من كل الحسابات")
    if not link.startswith("http"):
        messagebox.showerror("خطأ", "يرجى إدخال رابط صحيح يبدأ بـ http أو https")
        return

    for folder_name in os.listdir(ACCOUNTS_FOLDER):
        user_folder = os.path.join(ACCOUNTS_FOLDER, folder_name)
        cookies_path = os.path.join(user_folder, "cookies.txt")
        comment_path = os.path.join(user_folder, "comment.txt")

        if not os.path.exists(cookies_path) or not os.path.exists(comment_path):
            log(f"❌ تخطي الحساب: {folder_name} (لا يوجد cookies أو comment.txt)")
            continue

        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        with open(comment_path, "r", encoding="utf-8") as f:
            comment_text = f.read().strip()

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

        try:
            log(f"🔄 محاولة الدخول بحساب: {folder_name}")
            driver.get("https://www.facebook.com/")
            time.sleep(3)

            for cookie in cookies:
                cookie.pop("sameSite", None)
                cookie.pop("expiry", None)
                driver.add_cookie(cookie)

            driver.get("https://www.facebook.com/")
            time.sleep(5)

            if "login" in driver.current_url.lower():
                log(f"❌ فشل الدخول من الكوكيز لحساب: {folder_name}")
                driver.quit()
                continue

            driver.get(link)
            time.sleep(6)

            # تحقق من الرابط النهائي
            current_url = driver.current_url
            log(f"🔗 الرابط الحالي بعد التحميل: {current_url}")
            if "story_fbid" not in current_url:
                log(f"❌ لم يتم فتح الرابط الصحيح لحساب: {folder_name}")
                driver.quit()
                continue

            # محاولة الضغط على زر "تعليق"
            try:
                comment_button = driver.find_element(By.XPATH, "//span[text()='تعليق' or text()='Comment']")
                driver.execute_script("arguments[0].click();", comment_button)
                time.sleep(3)
            except:
                pass

            # خانة التعليق
            try:
                comment_area = driver.find_element(By.XPATH, "//div[@role='textbox']")
            except:
                log(f"❌ لم يتم العثور على خانة التعليق في: {folder_name}")
                driver.save_screenshot(os.path.join(user_folder, "not_found.png"))
                with open(os.path.join(user_folder, "page_source.html"), "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                driver.quit()
                continue

            # كتابة التعليق باستخدام JavaScript
            driver.execute_script("""
                arguments[0].focus();
                arguments[0].textContent = arguments[1];
                const event = new InputEvent('input', {
                    bubbles: true,
                    cancelable: true,
                    inputType: 'insertText',
                    data: arguments[1]
                });
                arguments[0].dispatchEvent(event);
            """, comment_area, comment_text)

            time.sleep(2)

            # اضغط زر النشر أو Enter
            try:
                post_button = driver.find_element(By.XPATH, "//div[@aria-label='اضغط Enter لإرسال.' or @aria-label='Press Enter to post.']")
                post_button.click()
                log(f"✅ تم إرسال التعليق من {folder_name} باستخدام زر النشر")
            except:
                try:
                    comment_area.send_keys(Keys.RETURN)
                    log(f"✅ تم إرسال التعليق من {folder_name} باستخدام Enter")
                except Exception as e:
                    log(f"❌ فشل في إرسال التعليق من {folder_name}: {e}")

        except Exception as e:
            log(f"⚠️ خطأ أثناء تنفيذ التعليق من {folder_name}: {e}")
        finally:
            driver.quit()

    messagebox.showinfo("انتهى", "✅ تم التعليق من كل الحسابات")
    if not link.startswith("http"):
        messagebox.showerror("خطأ", "يرجى إدخال رابط صحيح يبدأ بـ http أو https")
        return

    for folder_name in os.listdir(ACCOUNTS_FOLDER):
        user_folder = os.path.join(ACCOUNTS_FOLDER, folder_name)
        cookies_path = os.path.join(user_folder, "cookies.txt")
        comment_path = os.path.join(user_folder, "comment.txt")

        if not os.path.exists(cookies_path) or not os.path.exists(comment_path):
            log(f"❌ تخطي الحساب: {folder_name} (لا يوجد cookies أو comment.txt)")
            continue

        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        with open(comment_path, "r", encoding="utf-8") as f:
            comment_text = f.read().strip()

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

        try:
            log(f"🔄 محاولة الدخول بحساب: {folder_name}")
            driver.get("https://www.facebook.com/")
            time.sleep(3)

            for cookie in cookies:
                cookie.pop("sameSite", None)
                cookie.pop("expiry", None)
                driver.add_cookie(cookie)

            driver.get("https://www.facebook.com/")
            time.sleep(5)

            if "login" in driver.current_url.lower():
                log(f"❌ فشل الدخول من الكوكيز لحساب: {folder_name}")
                driver.quit()
                continue

            driver.get(link)
            time.sleep(6)
            log(f"🔗 الرابط الحالي بعد التحميل: {driver.current_url}")

            try:
                comment_area = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))
                )
            except:
                log(f"❌ لم يتم العثور على خانة التعليق في: {folder_name}")
                driver.save_screenshot(os.path.join(user_folder, "not_found.png"))
                with open(os.path.join(user_folder, "page_source.html"), "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                driver.quit()
                continue

            # استخدام JavaScript لإجبار الكتابة + إرسال ENTER
            driver.execute_script("""
                const el = arguments[0];
                const text = arguments[1];
                el.focus();
                el.innerText = text;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                const keyboardEvent = new KeyboardEvent('keydown', {
                    bubbles: true,
                    cancelable: true,
                    key: 'Enter',
                    code: 'Enter',
                    which: 13,
                    keyCode: 13
                });
                el.dispatchEvent(keyboardEvent);
            """, comment_area, comment_text)
            time.sleep(1)

            # اضغط Enter باستخدام ActionChains
            actions = ActionChains(driver)
            actions.move_to_element(comment_area).click().send_keys(Keys.RETURN).perform()
            time.sleep(3)
            log(f"✅ تم إرسال التعليق من {folder_name}")

        except Exception as e:
            log(f"⚠️ خطأ أثناء تنفيذ التعليق من {folder_name}: {e}")
            driver.save_screenshot(os.path.join(user_folder, "send_fail.png"))
        finally:
            driver.quit()

    messagebox.showinfo("انتهى", "✅ تم التعليق من كل الحسابات")
def add_new_account():
    new_account = simpledialog.askstring("إضافة حساب جديد", "أدخل اسم الحساب (مثل الإيميل):")
    if not new_account:
        return
    folder_name = new_account.strip().replace("\n", "").replace("/", "_").replace("\\", "_")
    account_folder = os.path.join(ACCOUNTS_FOLDER, folder_name)
    os.makedirs(account_folder, exist_ok=True)
    messagebox.showinfo("تمت الإضافة", f"تم إنشاء مجلد الحساب: {folder_name}\nيرجى الآن اختيار الحساب من القائمة وتحديث الكوكيز.")
    start_gui(refresh=True)

# === تحديث الكوكيز لحساب محدد ===
def update_cookies(selected_account):
    if not selected_account:
        messagebox.showerror("خطأ", "يرجى اختيار حساب لتحديث الكوكيز")
        return

    folder_name = selected_account.strip().replace("\n", "").replace("/", "_").replace("\\", "_")
    account_folder = os.path.join(ACCOUNTS_FOLDER, folder_name)
    os.makedirs(account_folder, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

    try:
        driver.get("https://www.facebook.com/")
        messagebox.showinfo("تسجيل الدخول", f"يرجى تسجيل الدخول يدويًا الآن للحساب: {selected_account}")

        confirm_window = tk.Toplevel()
        confirm_window.title("تأكيد الحفظ")
        confirm_window.geometry("300x100")
        tk.Label(confirm_window, text="اضغط زر 'تم' بعد تسجيل الدخول").pack(pady=10)
        tk.Button(confirm_window, text="✅ تم", command=confirm_window.destroy).pack()
        confirm_window.grab_set()
        window.wait_window(confirm_window)

        cookies = driver.get_cookies()
        with open(os.path.join(account_folder, "cookies.txt"), "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)

        if not os.path.exists(os.path.join(account_folder, "comment.txt")):
            with open(os.path.join(account_folder, "comment.txt"), "w", encoding="utf-8") as f:
                f.write("تعليق افتراضي")

        messagebox.showinfo("تم", "✅ تم حفظ الكوكيز بنجاح.")
    except Exception as e:
        messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ الكوكيز:\n{e}")
    finally:
        driver.quit()

# === واجهة المستخدم ===
def start_gui(refresh=False):
    global window
    if refresh:
        window.destroy()

    window = tk.Tk()
    window.title("نشر تعليق على فيسبوك")
    window.geometry("520x340")
    window.resizable(False, False)

    label = tk.Label(window, text="ضع رابط منشور فيسبوك للتعليق عليه:", font=("Arial", 12))
    label.pack(pady=10)

    link_entry = tk.Entry(window, width=60)
    link_entry.pack(pady=5)

    def on_submit():
        link = link_entry.get().strip()
        if not link:
            messagebox.showerror("خطأ", "يرجى إدخال رابط المنشور.")
        else:
            comment_on_link(link)

    btn_comment = tk.Button(window, text="📝 نشر التعليق من كل الحسابات", command=on_submit, bg="green", fg="white", font=("Arial", 11))
    btn_comment.pack(pady=10)

    tk.Label(window, text="اختر حساب لتحديث الكوكيز:", font=("Arial", 11)).pack()
    accounts_list = [f for f in os.listdir(ACCOUNTS_FOLDER) if os.path.isdir(os.path.join(ACCOUNTS_FOLDER, f))]
    selected_account = tk.StringVar(window)
    if accounts_list:
        selected_account.set(accounts_list[0])
    else:
        selected_account.set("")

    dropdown = ttk.Combobox(window, textvariable=selected_account, values=accounts_list, width=45)
    dropdown.pack(pady=5)

    btn_update = tk.Button(window, text="🔁 تحديث الكوكيز لهذا الحساب", command=lambda: update_cookies(selected_account.get()), bg="blue", fg="white", font=("Arial", 11))
    btn_update.pack(pady=10)

    btn_add = tk.Button(window, text="➕ إضافة حساب جديد", command=add_new_account, bg="gray", fg="white", font=("Arial", 10))
    btn_add.pack(pady=5)

    window.mainloop()

# === تشغيل البرنامج ===
if __name__ == "__main__":
    os.makedirs(ACCOUNTS_FOLDER, exist_ok=True)
    auto_check_all_cookies()
    start_gui()
