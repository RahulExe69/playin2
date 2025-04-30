import os
import time
import random
import string
import logging
from threading import Lock
from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logging.basicConfig(
    filename='account_creator.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

SIGNUP_URL = "https://playinexch247.com/#"
DELAY = random.randint(5, 10)  # Random delay between 5-10 seconds

class AccountCreator:
    def __init__(self):
        self.lock = Lock()
        self.status = {
            "running": False,
            "current": 0,
            "total": 0,
            "success": 0,
            "failure": 0
        }

    def create_accounts(self, base_user, password, count, phone=None):
        with self.lock:
            self.status.update({
                "running": True,
                "current": 0,
                "total": count,
                "success": 0,
                "failure": 0
            })

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        driver = webdriver.Chrome(
            service=Service('/usr/bin/chromedriver'),
            options=chrome_options
        )

        try:
            for i in range(1, count + 1):
                username = f"{base_user}{i}"
                email = f"{username}@gmail.com"
                phone_number = phone or ''.join(random.choices(string.digits, k=10))
                
                try:
                    driver.get(SIGNUP_URL)
                    time.sleep(2)

                    # Fill form
                    driver.find_element(By.NAME, "username").send_keys(username)
                    driver.find_element(By.NAME, "email").send_keys(email)
                    driver.find_element(By.NAME, "password").send_keys(password)
                    driver.find_element(By.NAME, "mobile").send_keys(phone_number)
                    
                    # Submit
                    driver.find_element(By.XPATH, "//button[@type='submit']").click()
                    time.sleep(3)

                    logging.info(f"Created: {username} | {email} | {phone_number}")
                    with self.lock:
                        self.status["success"] += 1
                except Exception as e:
                    logging.error(f"Failed {username}: {str(e)}")
                    with self.lock:
                        self.status["failure"] += 1

                with self.lock:
                    self.status["current"] += 1
                
                time.sleep(DELAY)
        finally:
            driver.quit()
            with self.lock:
                self.status["running"] = False

app = Flask(__name__)
creator = AccountCreator()

@app.route("/", methods=["GET", "POST"])
def index():
    error = success_msg = None
    if request.method == "POST":
        base = request.form.get("base_username", "").strip()
        password = request.form.get("password", "").strip()
        count_str = request.form.get("count", "").strip()
        phone = request.form.get("phone", "").strip()

        if not base or not password or not count_str:
            error = "Base username, password, and count are required."
        elif not count_str.isdigit() or int(count_str) < 1:
            error = "Count must be a positive integer."
        elif phone and (not phone.isdigit() or len(phone) != 10):
            error = "Phone must be a 10-digit number."
        else:
            count = int(count_str)
            thread = threading.Thread(target=creator.create_accounts, args=(base, password, count, phone), daemon=True)
            thread.start()
            success_msg = f"Started creating {count} accounts with base '{base}'"

    return render_template("index.html", error=error, success=success_msg)

@app.route("/status")
def get_status():
    return jsonify(creator.status)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
