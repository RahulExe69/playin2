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

# Configuration
logging.basicConfig(
    filename='account_creator.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

SIGNUP_URL = "https://playinexch247.com/#"
DELAY = 7  # Increased delay to avoid detection

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
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
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
                    time.sleep(2)  # Wait for page load

                    # Fill form
                    driver.find_element(By.NAME, "username").send_keys(username)
                    driver.find_element(By.NAME, "email").send_keys(email)
                    driver.find_element(By.NAME, "password").send_keys(password)
                    driver.find_element(By.NAME, "mobile").send_keys(phone_number)
                    
                    # Submit
                    driver.find_element(By.XPATH, "//button[@type='submit']").click()
                    time.sleep(3)  # Wait for submission

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
    if request.method == "POST":
        # [Form handling logic similar to original]
        # Start thread with creator.create_accounts()
    return render_template("index.html")

@app.route("/status")
def get_status():
    return jsonify(creator.status)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)