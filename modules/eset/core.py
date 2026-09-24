from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By


from modules.utils.helpers import button_with_text_is_clickable, dataGenerator
from modules.eset.parsers import parseESETToken, parseESETProtectHubKey
from modules.utils.logger import console_log, INFO, OK, ERROR, WARN
from modules.EmailAPIs import BaseEmailAPI

from typing import Optional, Tuple, Union, List

import colorama
import time
import logging


class IPBlockedException(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class EsetRegister:
    def __init__(self, registered_email_obj: BaseEmailAPI, eset_password: str, driver: WebDriver):
        self.email_obj = registered_email_obj
        self.eset_password = eset_password
        self.driver = driver
        self.window_handle: Optional[str] = None
        self.wait = WebDriverWait(self.driver, 15)

    def createAccount(self) -> bool:
        logging.info('Register page loading...')
        console_log('\nRegister page loading...', INFO)

        if hasattr(self.email_obj, 'open_mail'):
            self.driver.switch_to.new_window('tab')
            self.window_handle = self.driver.current_window_handle
            
        self.driver.get('https://login.eset.com/Register')
        
        email_input = self.wait.until(EC.presence_of_element_located((By.ID, 'email')))
        logging.info('Register page is loaded!')
        console_log('Register page is loaded!', OK)

        logging.info('Bypassing cookies...')
        console_log('\nBypassing cookies...', INFO)
        try:
            cookie_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'cc-accept'))
            )
            self.driver.execute_script('arguments[0].click();', cookie_button)
            logging.info('Cookies successfully bypassed!')
            console_log('Cookies successfully bypassed!', OK)
            time.sleep(1)
        except TimeoutException:
            logging.info('Cookies were not bypassed (it doesn\'t affect the algorithm, I think :D)')
            console_log('Cookies were not bypassed (it doesn\'t affect the algorithm, I think :D)', ERROR)
        
        logging.info('Data filling...')
        console_log('\nData filling...', INFO)
        
        email_input.send_keys(self.email_obj.email)
        time.sleep(0.5)
        self.driver.find_element(By.ID, 'password').send_keys(self.eset_password)
        
        logging.info('Selecting the country...')
        try:
            current_country = self.driver.find_element(By.CSS_SELECTOR, '.select__single-value.css-1dimb5e-singleValue').text
            if current_country != 'Ukraine':
                dropdown = self.driver.find_element(By.CSS_SELECTOR, '.select__control.css-13cymwt-control')
                self.driver.execute_script('arguments[0].click();', dropdown)
                
                for country in self.driver.find_elements(By.CSS_SELECTOR, '.select__option.css-uhiml7-option'):
                    if country.text == 'Ukraine':
                        self.driver.execute_script('arguments[0].click();', country)
                        logging.info('Country selected!')
                        break
        except NoSuchElementException:
            pass

        create_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-label='register-create-account-button']")
        self.driver.execute_script('arguments[0].click();', create_button)
        
        for _ in range(30):
            title = self.driver.title
            if title == 'Service not available':
                raise IPBlockedException('\nESET temporarily blocked your IP, try again later!!! Try to use VPN/Proxy or try to change Email API!!!')
            
            if self.driver.current_url == 'https://home.eset.com/':
                logging.info('Successfully!')
                console_log('Successfully!', OK)
                return True
            
            if 'This email address is already registered' in self.driver.page_source:
                raise RuntimeError(f'Email: {self.email_obj.email} is already registered!')
            
            time.sleep(1)
        
        raise IPBlockedException('\nESET temporarily blocked your IP, try again later!!! Try to use VPN/Proxy or try to change Email API!!!')

    def confirmAccount(self) -> bool:
        if self.email_obj.class_name != 'custom':
            logging.info(f'[{self.email_obj.class_name}] ESET-HOME-Token interception...')
            console_log(f'\n[{self.email_obj.class_name}] ESET-HOME-Token interception...', INFO)

        token = parseESETToken(self.email_obj, self.driver, max_iter=100, delay=3)

        if hasattr(self.email_obj, 'open_mail') and self.window_handle:
            self.driver.switch_to.window(self.window_handle)
        
        logging.info(f'ESET-HOME-Token: {token}')
        logging.info('Account confirmation is in progress...')
        console_log(f'ESET-HOME-Token: {token}', OK)
        console_log('\nAccount confirmation is in progress...', INFO)
        
        self.driver.get(f'https://login.eset.com/link/confirmregistration?token={token}')
        self.wait.until(EC.title_contains('ESET HOME'))
        
        try:
            self.wait.until_not(EC.presence_of_element_located((By.CLASS_NAME, 'verification-email_p')))
        except TimeoutException:
            self.driver.get(f'https://login.eset.com/link/confirmregistration?token={token}')
            self.wait.until(EC.title_contains('ESET HOME'))
            self.wait.until_not(EC.presence_of_element_located((By.CLASS_NAME, 'verification-email_p')))
            
            try:
                error_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-label='common-error-modal-dismiss-btn']"))
                )
                if error_button:
                    raise RuntimeError('Account confirmation error! Try again!')
            except TimeoutException:
                pass
                
            skip_button = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-label='onboarding-welcome-skip-introduction-btn']")))
            self.driver.execute_script('arguments[0].click();', skip_button)
        
        logging.info('Account successfully confirmed!')
        console_log('Account successfully confirmed!', OK)
        return True


class EsetKeygen:
    def __init__(self, registered_email_obj: BaseEmailAPI, driver: WebDriver, mode: str = 'ESET HOME'):
        self.email_obj = registered_email_obj
        self.driver = driver
        self.mode = mode.upper()
        self.wait = WebDriverWait(self.driver, 15)
        
        if self.mode not in ['ESET HOME', 'SMALL BUSINESS']:
            raise RuntimeError('Undefined keygen mode!')
        
    def sendRequestForKey(self) -> None:
        logging.info(f'[{self.mode}] Sending request and waiting for response...')
        console_log(f'\n[{self.mode}] Sending request and waiting for response...', INFO)

        skip_button = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-label='onboarding-welcome-skip-introduction-btn']")))
        self.driver.execute_script('arguments[0].click();', skip_button)
        
        trial_button = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "label[data-label='onboarding-add-subscription-protect-card-trial']")))
        self.driver.execute_script('arguments[0].click();', trial_button)
        
        self.__press_button_with_text(['continue', 'continua'])
    
        if self.mode == 'ESET HOME':
            card_lbl = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "label[data-label='onboarding-trial-protect-card-148']")))
        else:
            card_lbl = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "label[data-label='onboarding-trial-protect-card-172']")))
        
        self.driver.execute_script('arguments[0].click();', card_lbl)
        
        try:
            self.__press_button_with_text(['continue', 'continua'])
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-label='onboarding-trial-subscription-card']")))
            
            time.sleep(0.5)
            self.__press_button_with_text(['continue', 'continua'])
            self.wait.until(EC.url_to_be('https://home.eset.com/onboarding/download'))

            logging.info(f'[{self.mode}] Response successfully received!')
            console_log(f'[{self.mode}] Response successfully received!', OK)
        except Exception:
            raise RuntimeError('Request sending error!!!')

    def getLD(self) -> Tuple[str, str, str]:
        logging.info('License uploads...')
        console_log('\nLicense uploads...', INFO)

        self.driver.get('https://home.eset.com/subscriptions')
        
        detail_button = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-label='license-list-open-detail-page-btn']")))
        self.driver.execute_script("arguments[0].click();", detail_button)
        
        try:
            info_div = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-label='license-detail-info']")))
            self.driver.execute_script("arguments[0].click();", info_div)
        except TimeoutException:
            pass

        if 'detail' in self.driver.current_url:
            logging.info(f'License ID: {self.driver.current_url[-11:]}')
            console_log(f'License ID: {self.driver.current_url[-11:]}', OK)
        
        name_elem = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-label='license-detail-product-name']")))
        date_elem = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-label='license-detail-license-model-additional-info']")))
        key_elem = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-label='license-detail-license-key']")))
        
        license_name = name_elem.text
        license_out_date = date_elem.text
        license_key = key_elem.text
        
        logging.info('Information successfully received!')
        console_log('Information successfully received!', OK)
        return license_name, license_key, license_out_date
  
    def __press_button_with_text(self, text: Union[str, List[str]], timeout: float = 30) -> None:
        try:
            button = WebDriverWait(self.driver, timeout).until(
                button_with_text_is_clickable(text)
            )
            
            try:
                button.click()
            except Exception:
                self.driver.execute_script('arguments[0].click();', button)
                
        except TimeoutException:
            raise RuntimeError(f'Press button with text ({text}) error!!! Timeout exceeded.')

class EsetProtectHubRegister:
    def __init__(self, registered_email_obj: BaseEmailAPI, eset_password: str, driver: WebDriver):
        self.email_obj = registered_email_obj
        self.driver = driver
        self.eset_password = eset_password
        self.window_handle: Optional[str] = None
        self.wait = WebDriverWait(self.driver, 15)
        
    def createAccount(self) -> bool:
        logging.info('Loading ESET ProtectHub Page...')
        console_log('\nLoading ESET ProtectHub Page...', INFO)
        
        if hasattr(self.email_obj, 'open_mail'):
            self.driver.switch_to.new_window('tab')
            self.window_handle = self.driver.current_window_handle
            
        self.driver.get('https://protecthub.eset.com/public/registration?culture=en-US')
        
        self.wait.until(EC.presence_of_element_located((By.ID, 'continue')))
        
        cookie_button = self.wait.until(EC.presence_of_element_located((By.ID, 'cc-accept')))
        self.driver.execute_script('arguments[0].click();', cookie_button)
        
        logging.info('Successfully!')
        console_log('Successfully!', OK)

        logging.info('Data filling...')
        console_log('\nData filling...', INFO)
        self.driver.find_element(By.ID, 'email-input').send_keys(self.email_obj.email)
        self.driver.find_element(By.ID, 'company-name-input').send_keys(dataGenerator(10))
        
        logging.info('Selecting the country...')
        country_dropdown = self.wait.until(EC.presence_of_element_located((By.ID, 'country-select')))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", country_dropdown)
        time.sleep(0.5)
        
        ActionChains(self.driver).move_to_element(country_dropdown).click().perform()
        time.sleep(0.5)
        
        country_options = self.driver.find_elements(By.XPATH, '//div[starts-with(@class, "select")]')
        for country in country_options:
            if country.text.strip() == 'Ukraine':
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", country)
                ActionChains(self.driver).move_to_element(country).click().perform()
                logging.info('Country selected!')
                break
        
        self.driver.find_element(By.ID, 'company-vat-input').send_keys(dataGenerator(10, True))
        self.driver.find_element(By.ID, 'company-crn-input').send_keys(dataGenerator(10, True))
        
        logging.warning('Solve the captcha on the page manually!!!')
        console_log(f'\n{colorama.Fore.CYAN}Solve the captcha on the page manually!!!{colorama.Fore.RESET}', INFO, fill_text=False)

        # mtcaptcha
        while True:
            try:
                token = self.driver.find_element(By.CLASS_NAME, 'mtcaptcha-verifiedtoken').get_attribute('value')
                if token:
                    break
            except Exception:
                pass
            time.sleep(1)
            
        continue_button = self.driver.find_element(By.ID, 'continue')
        self.driver.execute_script('arguments[0].click();', continue_button)
        
        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: d.find_element(By.ID, 'registration-email-sent').text == 'We sent you a verification email'
            )
            logging.info('Successfully!')
            console_log('Successfully!', OK)
        except TimeoutException:
            raise IPBlockedException('\nESET temporarily blocked your IP, try again later!!! Try to use VPN/Proxy or try to change Email API!!!')
        
        return True

    def activateAccount(self) -> None:
        logging.info('Data filling...')
        console_log('\nData filling...', INFO)
        
        self.wait.until(EC.presence_of_element_located((By.ID, 'first-name-input'))).send_keys(dataGenerator(10))
        self.driver.find_element(By.ID, 'last-name-input').send_keys(dataGenerator(10))
        self.driver.find_element(By.ID, 'password-input').send_keys(self.eset_password)
        self.driver.find_element(By.ID, 'password-repeat-input').send_keys(self.eset_password)
        
        button = self.driver.find_element(By.ID, 'continue')
        self.driver.execute_script('arguments[0].click();', button)

        self.wait.until(EC.presence_of_element_located((By.ID, 'phone-input'))).send_keys(dataGenerator(10, True))
        time.sleep(0.5)
        
        button = self.driver.find_element(By.ID, 'continue')
        self.driver.execute_script('arguments[0].click();', button)
        
        WebDriverWait(self.driver, 15).until(
            lambda d: d.find_element(By.ID, 'activated-user-title').text == 'Your account has been successfully activated'
        )
        logging.info('Successfully!')
        console_log('Successfully!', OK)

    def confirmAccount(self) -> None:
        if self.email_obj.class_name != 'custom':
            logging.info(f'[{self.email_obj.class_name}] ProtectHub-Token interception...')
            console_log(f'\n[{self.email_obj.class_name}] ProtectHub-Token interception...', INFO)

        token = parseESETToken(self.email_obj, self.driver, True, max_iter=100, delay=3)

        if hasattr(self.email_obj, 'open_mail') and self.window_handle:
            self.driver.switch_to.window(self.window_handle)
        
        logging.info(f'ProtectHub-Token: {token}')
        logging.info('Account confirmation is in progress...')
        console_log(f'ProtectHub-Token: {token}', OK)
        console_log('\nAccount confirmation is in progress...', INFO)
        
        self.driver.get(f'https://protecthub.eset.com/public/activation/{token}/?culture=en-US')
        self.wait.until(EC.presence_of_element_located((By.ID, "first-name-input")))
        
        logging.info('Account successfully confirmed!')
        console_log('Account successfully confirmed!', OK)

class EsetProtectHubKeygen:
    def __init__(self, registered_email_obj: BaseEmailAPI, eset_password: str, driver: WebDriver):
        self.email_obj = registered_email_obj
        self.eset_password = eset_password
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 15)

    def getLD(self) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[bool]]:
        logging.info('Logging in to the created account...')
        console_log('\nLogging in to the created account...', INFO)
        self.driver.get('https://protecthub.eset.com')
        
        self.wait.until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(self.email_obj.email)
        self.driver.find_element(By.ID, 'password').send_keys(self.eset_password)
        
        login_button = self.driver.find_element(By.ID, "btn-login")
        self.driver.execute_script('arguments[0].click();', login_button)
        
        self.wait.until(EC.presence_of_element_located((By.ID, 'welcome-dialog-trial-link')))
        logging.info('Successfully!')
        logging.info('Sending a request for a get license...')
        console_log('Successfully!', OK)
        console_log('\nSending a request for a get license...', INFO)
        
        try:
            trial_link = self.driver.find_element(By.ID, 'welcome-dialog-trial-link')
            self.driver.execute_script('arguments[0].click();', trial_link)
        except Exception:
            pass
        
        license_is_being_generated = False
        for _ in range(30):
            try:
                toasts = self.driver.find_elements(By.CSS_SELECTOR, '.Toastify__toast-body.toastBody')
                if any('is being generated' in t.text.lower() for t in toasts):
                    license_is_being_generated = True
                    logging.info('Request successfully sent!')
                    console_log('Request successfully sent!', OK)
                    try:
                        skip_button = self.driver.find_element(By.ID, 'welcome-dialog-skip-button')
                        self.driver.execute_script('arguments[0].click();', skip_button)
                    except Exception:
                        pass
                    break
            except Exception:
                pass
            time.sleep(1)
        
        if not license_is_being_generated:
            raise RuntimeError('The request has not been sent!')
        
        logging.info('Waiting for a back response...')
        console_log('\nWaiting for a back response...', INFO)
        license_was_generated = False
        for _ in range(180): # 3m
            try:
                toasts = self.driver.find_elements(By.CSS_SELECTOR, '.Toastify__toast-body.toastBody')
                for alert in toasts:
                    if 'couldn\'t be generated' in alert.text:
                        break
                    elif 'was generated' in alert.text or 'Activate the ESET PROTECT platform modules' in alert.text:
                        logging.info('Successfully!')
                        console_log('Successfully!', OK)
                        license_was_generated = True
                        break
            except Exception:
                pass
            if license_was_generated:
                break
            time.sleep(1)

        if not license_was_generated:
            raise RuntimeError('The license cannot be generated, try again later!')

        logging.info('[Site] License uploads...')
        console_log('\n[Site] License uploads...', INFO)
        license_name = 'ESET PROTECT Advanced'
        try:
            self.driver.get('https://protecthub.eset.com/licenses')
            
            cell = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-label='customer-licenses-list-body-cell-renderer-row-0-column-0']")))
            WebDriverWait(self.driver, 15).until(lambda d: cell.text.strip() != "")
            license_id = cell.text.strip()
            
            logging.info(f'License ID: {license_id}')
            logging.info('Getting information from the license...')
            console_log(f'License ID: {license_id}', OK)
            console_log('\nGetting information from the license...', INFO)
            
            self.driver.get(f'https://protecthub.eset.com/subscriptions/details/2/{license_id}/overview')

            date_div = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-label='license-overview-validity-value']")))
            raw_date = date_div.text.strip().split(' ')[0]
            license_out_date = raw_date.replace('/', '.')
            
            show_key_container = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-label='license-overview-key-value']")))
            self.driver.execute_script('arguments[0].children[0].children[0].click();', show_key_container)
            
            pwd_input = self.wait.until(EC.presence_of_element_located((By.ID, 'show-license-key-auth-modal-password-input')))
            pwd_input.send_keys(self.eset_password)

            show_key_button = self.wait.until(EC.presence_of_element_located((By.ID, 'show-license-key-auth-modal-authenticate')))
            self.driver.execute_script('arguments[0].click();', show_key_button)
            
            for _ in range(30):
                try:
                    license_key = self.driver.find_element(By.CSS_SELECTOR, "div[data-label='license-overview-key-value']").text.strip()
                    if license_key and not license_key.startswith('XXXX-XXXX-XXXX-XXXX-XXXX'):
                        license_key = license_key.split(' ')[0]
                        logging.info('Information successfully received!')
                        console_log('Information successfully received!', OK)
                        return license_name, license_key, license_out_date, True
                except Exception:
                    pass
                time.sleep(1)
        except Exception:
            logging.critical('EXC_INFO:', exc_info=True)
            console_log('Error when obtaining a license key from the site!!!', ERROR)
        
        logging.info('[Email] License uploads...')
        console_log('\n[Email] License uploads...', INFO)
        if self.email_obj.class_name == 'custom':
            logging.warning('Wait for a message to your e-mail about successful key generation!!!')
            console_log('\nWait for a message to your e-mail about successful key generation!!!', WARN, fill_text=True)
            return None, None, None, None
            
        license_key, license_out_date, license_id = parseESETProtectHubKey(self.email_obj, self.driver, delay=3, max_iter=50) 
        logging.info(f'License ID: {license_id}')
        logging.info('Getting information from the license...')
        logging.info('Information successfully received!')
        console_log(f'License ID: {license_id}', OK)
        console_log('\nGetting information from the license...', INFO)
        console_log('Information successfully received!', OK)
        return license_name, license_key, license_out_date, False
    
    def removeLicense(self) -> Optional[bool]:
        logging.info('Deleting the key from the account, the key will still work...')
        console_log('Deleting the key from the account, the key will still work...', INFO)
        try:
            actions_button = self.wait.until(EC.presence_of_element_located((By.ID, 'license-actions-button')))
            self.driver.execute_script('arguments[0].click();', actions_button)
            time.sleep(1)
            
            try:
                remove_sub = self.driver.find_element(By.XPATH, "//*[normalize-space(text())='Remove subscription']")
                self.driver.execute_script('arguments[0].click();', remove_sub)
            except NoSuchElementException:
                pass
                
            remove_dlg_button = self.wait.until(EC.presence_of_element_located((By.ID, 'remove-license-dlg-remove-btn')))
            self.driver.execute_script('arguments[0].click();', remove_dlg_button)
            time.sleep(2)
            
            for _ in range(15):
                try:
                    btn = self.driver.find_element(By.ID, 'remove-license-dlg-remove-btn')
                    self.driver.execute_script('arguments[0].click();', btn)
                except Exception:
                    pass    
                if 'Subscription removed' not in self.driver.page_source:
                    time.sleep(1)
                    logging.info('Key successfully deleted!!!')
                    console_log('Key successfully deleted!!!', OK)
                    return True
                time.sleep(1)
        except Exception:
            pass
            
        logging.error('Failed to delete key, this error has no effect on the operation of the key!!!')
        console_log('Failed to delete key, this error has no effect on the operation of the key!!!', ERROR)
        return None