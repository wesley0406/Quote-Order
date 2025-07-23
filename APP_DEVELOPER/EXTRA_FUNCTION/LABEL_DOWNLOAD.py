from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time, os, sys, shutil, re
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
sys.path.append(r"C:\Users\wesley\Desktop\workboard\APP_DEVELOPER")
import TRACK_TOOL_V2 as TT 
import json

class ReyherAutomation:
    def __init__(self):
        # Set up Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument('--start-maximized')
        self.chrome_options.add_argument('--disable-notifications')

        # import the pass word adn user name 
        with open(r"C:\Users\wesley\Desktop\API_KEYS.json") as f:
            self.config = json.load(f)
        
        # Add unique user data directory
        user_data_dir = os.path.join(os.getcwd(), 'chrome_data')
        self.chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        
        # Initialize the Chrome WebDriver using webdriver_manager
        self.driver = None
        self.destination = "Not set"
        self.ORDER_NUM = "25010010"  # SC code will catach the info from the ERP 
        self.PM_LABEL_FILE = r"Z:\跨部門\共用資料夾\業務 to 包裝 包材及出貨資訊\C019\標籤下載\2025年"
        self.DF_ALL_ORDER = TT.FETCH_DATA()
        self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.chrome_options
            )

    def login_download(self):
        try:
            # Navigate to the REX login page
            url = "https://rex.reyher.de/index.php?id=login&L=1&id=24&tx_mdriologin_pi1%5BredirectTo%5D=rex"
            self.driver.get(url)
            
            # Handle cookie consent popup
            try:
                cookie_button = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
                )
                cookie_button.click()
                time.sleep(2)
            except Exception as e:
                print(f"Cookie popup not found or already accepted: {str(e)}")
            
            # Rest of login process
            partner_input = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.ID, "login-Partnernummer"))
            )
            partner_input.clear()
            partner_input.send_keys(self.config["C019_Partner_Number"])
            
            username_input = self.driver.find_element(By.ID, "login-username")
            username_input.clear()
            username_input.send_keys(self.config["C019_user_name"])
            
            password_input = self.driver.find_element(By.ID, "login-pass")
            password_input.clear()
            password_input.send_keys(self.config["C019_password"])

            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in')]")
            login_button.click()
            # Wait for the page to load after login
            time.sleep(2)

            # clicke the link to download the label
            label_printing_button = self.driver.find_element(By.XPATH, "//a[@href='/en/etikettendruck']")
            label_printing_button.click()

            time.sleep(2)
            # start enter the order and the position number
            self.DOWNLOAD_FROM_WEBSITE()

            print("Sueecssful download")
            return True
            
        except Exception as e:
            print(f"Login failed: {str(e)}")
        
            return False

    def LABEL_DF(self):

        CURRENT_ORDER =  self.DF_ALL_ORDER[self.DF_ALL_ORDER["SC_NO"] == self.ORDER_NUM].copy()
        CURRENT_ORDER.loc[:, "SERIAL_CODE"] =  CURRENT_ORDER["CST_JOB_NO"].str.split("R").str[1]
        CURRENT_ORDER.loc[:, "C019_ORDER_CODE"] =  CURRENT_ORDER["CST_JOB_NO"].str.split("R").str[0]

        #FIND the duplicate lot number error
        if CURRENT_ORDER["SERIAL_CODE"].duplicated().any():
            duplicate_serials = CURRENT_ORDER[CURRENT_ORDER["SERIAL_CODE"].duplicated()]
            raise ValueError(f"Duplicate serial codes found: {duplicate_serials['SERIAL_CODE'].tolist()}")

        return CURRENT_ORDER

    def DOWNLOAD_FROM_WEBSITE(self):
        WAITED_DOWNLOAD = self.LABEL_DF()
        
        for index, row in WAITED_DOWNLOAD.iterrows():
            serial_code = row.get("SERIAL_CODE", "N/A")  # Get safely
            order_code = row.get("C019_ORDER_CODE", "N/A")  # Get safely

            wait = WebDriverWait(self.driver, 10)  # Explicit wait

            # Enter the order number
            order_input = wait.until(EC.presence_of_element_located((By.ID, "orderNumber")))
            order_input.clear()
            order_input.send_keys(order_code)

            # Enter the position number
            position_input = wait.until(EC.presence_of_element_located((By.ID, "positionNumber")))
            position_input.clear()
            position_input.send_keys(serial_code)

            # Press generate label
            OK_button = wait.until(EC.element_to_be_clickable((By.ID, "goToStep2")))
            OK_button.click()

            time.sleep(2)  # Allow page transition

            # Enter the LOT number (handle stale element)
            for _ in range(3):
                try:
                    LOT_NUM_input = wait.until(EC.presence_of_element_located((By.ID, "lotNumber")))
                    LOT_NUM_input.clear()
                    LOT_NUM_input.send_keys(str(order_code + "R" + serial_code))
                    break
                except StaleElementReferenceException:
                    print("Retrying LOT_NUM_input...")
                    time.sleep(1)

            # Enter the country
            country_input = wait.until(EC.presence_of_element_located((By.ID, "mltsel")))
            country_input.clear()
            country_input.send_keys("TW")

            # Download the label
            label_download_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@title="Generate labels"]')))
            self.driver.execute_script("arguments[0].click();", label_download_button)
            time.sleep(2)

            # Go to logistic site
            Logistic_button = wait.until(EC.element_to_be_clickable((By.ID, "goToStep4")))
            self.driver.execute_script("arguments[0].click();", Logistic_button)
            time.sleep(2)  

            # Enter the LOT number again (handle stale element)
            for _ in range(3):
                try:
                    LOT_NUM_input = wait.until(EC.presence_of_element_located((By.ID, "lotNumber")))
                    LOT_NUM_input.clear()
                    LOT_NUM_input.send_keys(str(order_code + "R" +serial_code))
                    break
                except StaleElementReferenceException:
                    print("Retrying LOT_NUM_input...")
                    time.sleep(1)

            # Download the logistics label
            Logistic_download_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@title="Generate logisitics label"]')))
            self.driver.execute_script("arguments[0].click();", Logistic_download_button)
            time.sleep(2)

            # Go back to Home
            Home_button = wait.until(EC.element_to_be_clickable((By.ID, "goToStep1")))
            self.driver.execute_script("arguments[0].click();", Home_button)

            time.sleep(2)  # Allow page transition
        self.driver.close()

    def TRANSFER_LABEL_FILE(self):
        ORDER_DF = self.LABEL_DF()
        C019_ORDER_CODE = str(ORDER_DF.iloc[0]["C019_ORDER_CODE"])
        download_address = r"C:\Users\wesley\Downloads"
        file_name = "SC{}({})".format(str(ORDER_DF.iloc[0]["SC_NO"]), C019_ORDER_CODE)

        self.destination = os.path.join(self.PM_LABEL_FILE , file_name)
        # check  if the label have already been download
        if os.path.exists(self.destination) :
            raise ValueError("This file have been download : {}".format(file_name))
        
        os.makedirs(os.path.join(download_address, file_name), exist_ok=True)
        label_folder = os.path.join(download_address, file_name,"標籤")
        logistics_folder = os.path.join(download_address, file_name,"物流標")
        os.makedirs(label_folder, exist_ok=True)
        os.makedirs(logistics_folder, exist_ok=True)

        for file in os.listdir(download_address) :
            original_address = os.path.join(download_address, file)
            if C019_ORDER_CODE in file and "pdf" in file:

                match = re.search(r"\((\d+)\)", file)
                if match:
                    number = match.group(1)  # Extract the number inside ( )
                    if number != "1":  # Raise an error for (2), (3), etc.
                        raise ValueError(f"Error: Unexpected logistics file '{file}' found!")
                    shutil.move(original_address, os.path.join(logistics_folder, file))  # Add to logistics file 
                else : # 標籤
                    shutil.move(original_address, os.path.join(label_folder, file))

        shutil.move(os.path.join(download_address, file_name), self.destination)



# if __name__ == "__main__":
#     bot = ReyherAutomation()
#     bot.ORDER_NUM = "25040019"
#     bot.login_download()
#     bot.TRANSFER_LABEL_FILE()
#     print(bot.destination)