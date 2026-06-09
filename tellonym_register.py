# -*- coding: utf-8 -*-
"""
Script to automate account creation on Tellonym.me
- Creates account with random name, links email+password, saves credentials.
- Follows a specific user using browser API / DOM click (from follow_user.py).
- Loops infinitely.
"""

import sys
import io
import json
import os
import time
import random
import string
import argparse
import requests
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL           = "https://tellonym.me/"
EMAIL_SETUP_URL    = "https://tellonym.me/account/email"
TARGET_USER        = "pipinstall"

# Telegram Bot Config
TELEGRAM_BOT_TOKEN = "8953807139:AAEhmtNxjyVPbN0vjr5Ci9JYFe-BQNFiVVM"
TELEGRAM_CHAT_ID   = "-1003515021675"

# ─── Random credentials generator ─────────────────────────────────────────────
def random_email() -> str:
    """8 random letters + 4 random digits + @yopmail.com"""
    letters = "".join(random.choices(string.ascii_lowercase, k=8))
    digits  = "".join(random.choices(string.digits, k=4))
    return f"{letters}{digits}@yopmail.com"

def random_password() -> str:
    """9 random alphanumeric characters"""
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=9))

def random_name_generator() -> str:
    """6-10 random letters"""
    return "".join(random.choices(string.ascii_lowercase, k=random.randint(6, 10)))

# ─── Send credentials to Telegram ─────────────────────────────────────────────
def send_to_telegram(username: str, email: str, password: str) -> None:
    message = (
        "🆕 <b>حساب جديد (Tellonym)</b> 🆕\n\n"
        f"👤 <b>اليوزر:</b> <code>{username}</code>\n"
        f"📧 <b>الإيميل:</b> <code>{email}</code>\n"
        f"🔑 <b>الرمز:</b> <code>{password}</code>"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("[+] Credentials sent to Telegram successfully!")
        else:
            print(f"[-] Failed to send to Telegram: HTTP {r.status_code} - {r.text}")
    except Exception as e:
        print(f"[!] Error sending to Telegram: {e}")

# ─── Browser setup ────────────────────────────────────────────────────────────
def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # options.add_argument("--incognito") # useful for clean state
    driver = webdriver.Chrome(options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver

# ─── Register a new account ───────────────────────────────────────────────────
def register_account(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, 20)

    print("[*] Navigating to tellonym.me for registration...")
    driver.get(BASE_URL)
    time.sleep(3)

    # Find name input
    print("[*] Looking for name input field...")
    name_input = None

    try:
        name_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH,
                 '//input[@placeholder="Enter your name" '
                 'or @placeholder="enter your name" '
                 'or contains(@placeholder,"name")]')
            )
        )
    except Exception:
        pass

    if name_input is None:
        try:
            inputs = driver.find_elements(By.XPATH, '//input[@type="text"]')
            if inputs:
                name_input = inputs[0]
        except Exception:
            pass

    if name_input is None:
        raise RuntimeError("Name input field not found!")

    driver.execute_script("arguments[0].scrollIntoView(true);", name_input)
    time.sleep(0.4)
    name_input.clear()
    name_input.click()
    time.sleep(0.3)
    
    random_name = random_name_generator()
    name_input.send_keys(random_name)
    time.sleep(1)
    print(f"[+] Typed random name: '{random_name}'")

    # Find Create account button
    print("[*] Looking for 'Create account' button...")
    create_btn = None

    try:
        create_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 '//button[contains(translate(text(),'
                 '"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"),'
                 '"create account")]')
            )
        )
    except Exception:
        pass

    if create_btn is None:
        try:
            create_btn = driver.find_element(
                By.XPATH,
                '//*[contains(text(),"Create account") '
                'or contains(text(),"Create Account") '
                'or contains(text(),"Sign up") '
                'or contains(text(),"Get started")]',
            )
        except Exception:
            pass

    if create_btn is None:
        try:
            create_btn = driver.find_element(By.XPATH, '//button[@type="submit"]')
        except Exception:
            pass

    if create_btn is None:
        raise RuntimeError("Create account button not found!")

    driver.execute_script("arguments[0].scrollIntoView(true);", create_btn)
    time.sleep(0.5)
    create_btn.click()
    print("[+] Clicked 'Create account'!")

    # Wait for redirection (account created)
    print("[*] Waiting for account creation...")
    for attempt in range(10):
        time.sleep(2)
        if driver.current_url.rstrip("/") != BASE_URL.rstrip("/"):
            print(f"[+] Redirected to {driver.current_url} -> account created!")
            break

# ─── Link email + set password ────────────────────────────────────────────────
def link_email_and_password(driver: webdriver.Chrome) -> tuple[str, str]:
    wait = WebDriverWait(driver, 25)

    email    = random_email()
    password = random_password()

    print(f"\n[*] Navigating to email setup page: {EMAIL_SETUP_URL}")
    driver.get(EMAIL_SETUP_URL)
    time.sleep(3)

    # Step 1: Email field
    email_input = None
    selectors = [
        '//input[@placeholder="your@email.com" or @placeholder="Your@email.com"]',
        '//input[@type="email"]',
        '//input[contains(@placeholder,"email") or contains(@placeholder,"Email")]',
        '//input[@name="email" or @id="email"]',
    ]
    for sel in selectors:
        try:
            email_input = wait.until(EC.presence_of_element_located((By.XPATH, sel)))
            break
        except Exception:
            pass

    if email_input is None:
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        if all_inputs:
            email_input = all_inputs[0]
        else:
            raise RuntimeError("Email input not found!")

    driver.execute_script("arguments[0].scrollIntoView(true);", email_input)
    time.sleep(0.4)
    email_input.clear()
    email_input.click()
    time.sleep(0.3)
    email_input.send_keys(email)
    time.sleep(0.8)

    next_btn = _find_next_button(driver, wait)
    driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
    time.sleep(0.4)
    next_btn.click()
    time.sleep(3)

    # Step 2: Password field
    pass_input = None
    pass_selectors = [
        '//input[@type="password"]',
        '//input[contains(@placeholder,"Password") or contains(@placeholder,"password")]',
        '//input[@name="password" or @id="password"]',
    ]
    for sel in pass_selectors:
        try:
            pass_input = wait.until(EC.presence_of_element_located((By.XPATH, sel)))
            break
        except Exception:
            pass

    if pass_input is None:
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        if all_inputs:
            pass_input = all_inputs[0]
        else:
            raise RuntimeError("Password input not found!")

    driver.execute_script("arguments[0].scrollIntoView(true);", pass_input)
    time.sleep(0.4)
    pass_input.clear()
    pass_input.click()
    time.sleep(0.3)
    pass_input.send_keys(password)
    time.sleep(0.8)

    next_btn2 = _find_next_button(driver, wait)
    driver.execute_script("arguments[0].scrollIntoView(true);", next_btn2)
    time.sleep(0.4)
    next_btn2.click()
    time.sleep(3)

    return email, password

def _find_next_button(driver: webdriver.Chrome, wait: WebDriverWait):
    next_btn = None
    btn_selectors = [
        '//button[contains(translate(text(),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"),"next")]',
        '//button[@type="submit"]',
        '//*[contains(text(),"Next") or contains(text(),"next") or contains(text(),"Continue")]',
        '//button[contains(@class,"submit") or contains(@class,"next") or contains(@class,"primary")]',
    ]
    for sel in btn_selectors:
        try:
            next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, sel)))
            break
        except Exception:
            pass

    if next_btn is None:
        btns = driver.find_elements(By.TAG_NAME, "button")
        if btns:
            next_btn = btns[-1]
        else:
            raise RuntimeError("Next button not found!")
    return next_btn

def get_username(driver: webdriver.Chrome) -> str:
    try:
        raw = driver.execute_script("return localStorage.getItem('reduxPersist:user');")
        if raw:
            data = json.loads(raw)
            return data.get("username") or data.get("name") or "unknown"
    except Exception:
        pass
    url = driver.current_url
    if "tellonym.me/" in url:
        return url.split("tellonym.me/")[-1].split("/")[0] or "unknown"
    return "unknown"


# ─── Follow via Tellonym API (direct, no DOM needed) ─────────────────────────
def follow_via_api(driver: webdriver.Chrome, target: str) -> bool:
    """
    Use the Tellonym REST API directly from the browser context,
    which already has the auth token in localStorage.
    """
    print(f"[*] Attempting follow via Tellonym API for '{target}'...")

    # Wait for the async script to finish
    driver.set_script_timeout(15)
    
    result = driver.execute_async_script("""
        var target   = arguments[0];
        var callback = arguments[1];

        // Extract auth token from reduxPersist:user
        var token = null;
        try {
            var raw = localStorage.getItem('reduxPersist:user');
            if (raw) {
                var u = JSON.parse(raw);
                token = u.token || u.accessToken || u.authToken || null;
            }
        } catch(e) {}

        // Also try direct token keys
        if (!token) {
            token = localStorage.getItem('token')
                 || localStorage.getItem('accessToken')
                 || localStorage.getItem('auth_token')
                 || null;
        }

        if (!token) { callback({ok: false, reason: 'no-token'}); return; }

        // POST /follows  (Tellonym's follow endpoint)
        fetch('https://api.tellonym.me/follows', {
            method: 'POST',
            headers: {
                'Content-Type':    'application/json',
                'Authorization':   'Bearer ' + token,
                'tellonym-client': 'web:0',
                'Accept':          'application/json'
            },
            body: JSON.stringify({ username: target })
        })
        .then(function(r) {
            return r.text().then(function(body) {
                var json = null;
                try { json = JSON.parse(body); } catch(e) {}
                callback({ ok: r.ok, status: r.status, body: json || body });
            });
        })
        .catch(function(e) { callback({ ok: false, reason: e.toString() }); });
    """, target)

    print(f"[*] API response: {result}")

    if not isinstance(result, dict):
        print(f"[-] Unexpected response: {result}")
        return False

    status = result.get("status", 0)
    if result.get("ok") or status in (200, 201):
        print(f"[+] Followed '{target}' via API! (HTTP {status})")
        return True
    elif status == 409:
        print(f"[+] Already following '{target}' (HTTP 409).")
        return True
    elif status == 404:
        print(f"[-] User '{target}' not found (HTTP 404).")
        return False
    elif status == 401:
        print(f"[-] Auth token rejected (HTTP 401) – session may be expired.")
        return False
    else:
        reason = result.get("reason", "")
        if reason == "no-token":
            print("[-] No auth token found in localStorage. Cannot call API.")
        else:
            print(f"[-] API follow failed: HTTP {status} | {result.get('body', '')}")
        return False

# ─── Follow via DOM (click Follow then Anonymous? within 3 seconds) ───────────
def follow_via_dom(driver: webdriver.Chrome, target: str) -> bool:
    """
    Navigate to the profile page, click Follow, then immediately click
    the 'Anonymous?' countdown button (within ~2.5s) to make the follow
    anonymous instead of public.
    """
    profile_url = f"{BASE_URL}{target}"

    print(f"\n[*] Navigating to: {profile_url}")
    driver.get(profile_url)

    # Wait for React to fully hydrate the page
    print("[*] Waiting for page to fully load (React hydration)...")
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
    )
    except Exception:
        pass
    time.sleep(7)   # React pages need extra time

    print(f"[*] Current URL: {driver.current_url}")

    # ── Step 1: Find the Follow button ──────────────────────────────────────
    all_els = driver.find_elements(By.XPATH, '//button | //*[@role="button"]')
    print(f"[*] Clickable elements found: {len(all_els)}")

    follow_btn = None
    for i, el in enumerate(all_els):
        txt      = (el.text or "").strip()
        label    = el.get_attribute("aria-label") or ""
        tid      = el.get_attribute("data-testid") or ""
        cls      = (el.get_attribute("class") or "")[:80]
        combined = (txt + label + tid + cls).lower()
        
        # Don't print everything, just log if found
        if txt.lower() == "follow" and follow_btn is None:
            follow_btn = el
            print(f"    [+] Exact 'Follow' button found!")
        elif "follow" in combined and "unfollow" not in combined and follow_btn is None:
            follow_btn = el
            print(f"    [+] Follow button candidate found!")

    if follow_btn is None:
        print("[-] Follow button not found in DOM.")
        return False

    # ── Step 2: Click Follow ─────────────────────────────────────────────────
    print(f"[*] Clicking 'Follow' button...")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", follow_btn)
    time.sleep(0.3)
    try:
        follow_btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", follow_btn)

    print("[+] 'Follow' clicked! Now watching for 'Anonymous?' countdown button...")

    # ── Step 3: Immediately find and click "Anonymous?" ─────────────────────
    anon_btn   = None
    deadline   = time.time() + 2.5   # 2.5-second window (safe margin)

    anon_xpaths = [
        '//*[contains(text(),"Anonymous")]',
        '//button[contains(text(),"Anonymous")]',
        '//*[@aria-label and contains(@aria-label,"Anonymous")]',
        '//*[contains(text(),"anonym")]',   # lowercase variant
    ]

    while time.time() < deadline:
        for xp in anon_xpaths:
            els = driver.find_elements(By.XPATH, xp)
            for el in els:
                txt = (el.text or "").strip()
                if "anonymous" in txt.lower() or "anonym" in txt.lower():
                    anon_btn = el
                    print(f"[+] Found Anonymous? button: '{txt}'")
                    break
            if anon_btn:
                break
        if anon_btn:
            break
        time.sleep(0.1)   # poll every 100 ms

    if anon_btn:
        print("[*] Clicking 'Anonymous?' to make follow anonymous...")
        try:
            anon_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", anon_btn)
        time.sleep(1)
        print("[+] Anonymous follow confirmed!")

        try:
            page_src = driver.page_source
            if "anonymous" in page_src.lower() or "anonym" in page_src.lower():
                print("[+] Page confirms anonymous follow!")
        except Exception:
            pass
        return True

    else:
        print("[!] 'Anonymous?' button not found within 2.5s window.")
        print("    The follow may have been registered as PUBLIC.")
        try:
            if "unfollow" in driver.page_source.lower():
                print("[~] Follow succeeded but it was PUBLIC (not anonymous).")
                return True
        except Exception:
            pass
        return False

# ─── Main follow routine ──────────────────────────────────────────────────────
def follow_user(driver: webdriver.Chrome, target: str) -> bool:
    # Navigate to the profile first (needed for API auth context)
    profile_url = f"{BASE_URL}{target}"
    print(f"\n[*] Loading profile page: {profile_url}")
    driver.get(profile_url)
    time.sleep(4)

    # Try API method first (faster, more reliable)
    print("\n[── Method 1: Tellonym REST API ──]")
    if follow_via_api(driver, target):
        return True

    # Fallback: DOM click
    print("\n[── Method 2: DOM click ──]")
    return follow_via_dom(driver, target)

# ─── Main Loop ────────────────────────────────────────────────────────────────
def main():
    loop_count = 1
    
    while True:
        print("="*60)
        print(f"[*] Starting Account Generation Loop #{loop_count}")
        print("="*60)
        
        driver = None
        try:
            driver = build_driver()

            # 1. Register account
            register_account(driver)

            # 2. Link email + password
            username = get_username(driver)
            print(f"\n[*] Account username: {username}")

            email, password = link_email_and_password(driver)

            # 3. Send credentials to Telegram
            send_to_telegram(username, email, password)

            # 4. Follow target
            success = follow_user(driver, TARGET_USER)
            if success:
                print(f"\n[+] Follow action succeeded for '{TARGET_USER}'!")
            else:
                print(f"\n[-] Could not follow '{TARGET_USER}'.")

            print(f"\n[+] Loop #{loop_count} completed!")
            
        except Exception as e:
            print(f"\n[!] Error in loop #{loop_count}: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if driver:
                driver.quit()
                print("[*] Browser closed. Cleaning up...")
                
        loop_count += 1
        print("[*] Waiting 5 seconds before creating the next account...")
        time.sleep(5)

if __name__ == "__main__":
    main()
