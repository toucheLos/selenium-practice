import random
import sys
import multiprocessing as mp
from multiprocessing import Pool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
import time
from twilio.rest import Client

# Twilio setup
def send_sms(credentials, message):
    client = Client(credentials['account_sid'], credentials['auth_token'])
    message = client.messages.create(
        body=message,
        from_=credentials['twilio_phone'],
        to=credentials['personal_phone']
    )
    print(f"Message sent to {credentials['personal_phone']}: {message.sid}")

def read_credentials(file_path):
    # File formatted as such:
    # username="username"
    # password="password"
    with open(file_path, 'r') as file:
        credentials = {}
        for line in file:
            name, value = line.strip().split('=', 1)
            credentials[name] = value
        return credentials

def selenium_script(instances, credentials):
    # Set the path to the WebDriver executable
    driver = webdriver.Firefox()

    # Open the desired URL
    driver.get("google.com")

    characters = "1234567890QWERTYUIOPASDFGHJKLZXCVBNM"
    access_code = None

    def get_access_code():
        return ''.join(random.choice(characters) for _ in range(14))
    
    def save_access_code():
        with open('successful_access_code', 'w') as file:
            file.write(f"Successful access code: {access_code}\n")

    try:
        # Wait until the username field is present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'idp-discovery-username'))
        )

        # Find the username field and enter the username
        username_field = driver.find_element(By.ID, 'idp-discovery-username')
        username_field.send_keys(credentials['username'])

        # Click to move to password field
        onto_password = driver.find_element(By.ID, 'idp-discovery-submit')
        onto_password.click()

        # Wait until the password field is present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'okta-signin-password'))
        )

        # Find the password field and enter the password
        password_field = driver.find_element(By.ID, 'okta-signin-password')
        password_field.send_keys(credentials['password'])

        # Find the sign-in button and click it
        sign_in_button = driver.find_element(By.ID, 'okta-signin-submit')
        sign_in_button.click()

        # Optional: Wait for some time to ensure the login process completes
        time.sleep(5)

        # Wait until the access code button is present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="Enter access code button"]'))
        )

        enter_access_code_field = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Enter access code button"]')
        enter_access_code_field.click()

        # Now proceed with the rest of your actions, like inputting a string and pressing register multiple times
        for _ in range(10000):
            try:
                input_field = driver.find_element(By.NAME, 'inputValue')  # Ensure this is the correct name attribute
                input_field.clear()
                access_code = get_access_code()
                input_field.send_keys(access_code)

                # Wait until the register button is present
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="product-modal-register-btn"]'))
                )

                # Find the register button
                register_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="product-modal-register-btn"]')
                register_button.click()

                time.sleep(1)
            except:
                message = f"Match found. Code is {access_code}"
                save_access_code(access_code)
                send_sms(credentials, message)
                driver.quit()
                sys.exit(1)

    except Exception as e:
        print(f'An error occurred: {e}')
        driver.quit()
        sys.exit(1)
    finally:
        driver.quit()

# For Multiprocessing

def multiprocess():

    credentials = read_credentials('credentials.txt')
    cpus = mp.cpu_count()
    print(f"Running selenium scripts on {cpus} cpus")
    poolCount = cpus

    with Pool(poolCount) as p:
        p.starmap(selenium_script, [(i, credentials) for i in range(poolCount)])

if __name__ == "__main__":
    multiprocess()
