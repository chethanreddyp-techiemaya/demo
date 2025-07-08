import os
import time
import re
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from pyairtable import Api

AIRTABLE_BASE_ID = 'appQdiMFIIjsEW2aM'
AIRTABLE_API_KEY = 'pat3PvG5VFYBSFb5v.007ade4d95461e456d5045c8b77f80f3e2cc58154ac6cb9175285a98b0df0e53'
AIRTABLE_TABLE_ID = 'tblC9XMw5NHAH6JMy'

def add_task_to_airtable(task, deadline, assign_to, attachment_url, description):
    api = Api(AIRTABLE_API_KEY)
    table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_ID)
    record = {
        "Task": task,
        "Deadline": deadline,
        "Assign To": assign_to,
        "Attachment": [{"url": attachment_url}] if attachment_url else [],
        "Description": description,
    }
    return table.create(record)

def parse_task_command(message):
    pattern = r"Task\s+(.+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*\|\s*(\S+)\s*\|\s*(.+)"
    match = re.match(pattern, message)
    if match:
        task, deadline, assign_to, attachment, description = match.groups()
        return task.strip(), deadline.strip(), assign_to.strip(), attachment.strip(), description.strip()
    return None

def check_whatsapp_task():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://web.whatsapp.com")
    time.sleep(30)  # Wait for QR scan or session load (not production ready)
    last_message = ""
    task_added = False
    try:
        messages = driver.find_elements(By.CSS_SELECTOR, "div.message-in, div.message-out")
        if messages:
            last = messages[-1]
            message_text = last.text
            if message_text != last_message:
                last_message = message_text
                if message_text.startswith("Task"):
                    parsed = parse_task_command(message_text)
                    if parsed:
                        task, deadline, assign_to, attachment, description = parsed
                        add_task_to_airtable(task, deadline, assign_to, attachment, description)
                        task_added = True
    except Exception as e:
        print("Error:", e)
    finally:
        driver.quit()
    return task_added

app = Flask(__name__)



@app.route("/")
def health():
    return "OK", 200



@app.route("/check", methods=["POST", "GET"])
def check():
    result = check_whatsapp_task()
    return jsonify({"task_added": result})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
