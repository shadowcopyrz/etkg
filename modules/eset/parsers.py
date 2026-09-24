from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

from modules.EmailAPIs import BaseEmailAPI, CustomEmailAPI, WebWrapperEmailAPI
from modules.utils.logger import *

from typing import Optional, Union

import colorama
import logging
import time
import re

def parseESETToken(email_obj: Union[BaseEmailAPI, WebWrapperEmailAPI], driver: Optional[WebDriver] = None, eset_business=False, delay=3.0, max_iter=100):
    activated_href = None
    
    if isinstance(email_obj, CustomEmailAPI):
        while True:
            activated_href = input(f'\n[  {colorama.Fore.YELLOW}INPT{colorama.Fore.RESET}  ] {colorama.Fore.CYAN}Enter the link to activate your account: {colorama.Fore.RESET}').strip()
            logging.info(f'[  INPT  ] Enter the link to activate your account: {activated_href}')
            if activated_href:
                regex = r'activation\/[a-zA-Z0-9-]+' if eset_business else r'token=[a-zA-Z\d:/-]*'
                match = re.search(regex, activated_href)
                if match:
                    token = match.group()[11:] if eset_business else match.group()[6:]
                    if len(token) == 36:
                        return token
            console_log('Incorrect link syntax', ERROR)

    for _ in range(max_iter):
        try:
            messages = email_obj.get_messages()
            if not messages:
                time.sleep(delay)
                continue

            for message in messages:
                is_found = False
                if eset_business and 'ESET PROTECT Hub' in message['subject']:
                    is_found = True
                elif 'product.eset.com' in message['from'] or 'ESET HOME' in message['from']:
                    is_found = True
                    
                if not is_found:
                    pass
                
                if message.get('body'):
                    activated_href = message['body']
                elif isinstance(email_obj, WebWrapperEmailAPI):
                    if driver is None:
                        raise ValueError('driver argument must not be None!')
                    email_obj.open_mail(message['id'])
                    if eset_business:
                        activated_href = driver.find_element(By.XPATH, "//a[starts-with(@href, 'https://protecthub.eset.com')]").get_attribute('href')
                    else:
                        activated_href = driver.find_element(By.XPATH, "//a[starts-with(@href, 'https://login.eset.com')]").get_attribute('href')
                             
        except Exception as e:
            logging.info(f"[parseESETToken] Error: {e}")
            
        if activated_href:
            regex = r'activation\/[a-zA-Z0-9-]+' if eset_business else r'token=[a-zA-Z\d:/-]*'
            match = re.search(regex, activated_href)
            if match:
                token = match.group()[11:] if eset_business else match.group()[6:]
                if len(token) == 36:
                    return token
                    
        time.sleep(delay)

    raise RuntimeError('Token retrieval error, try again later or change the Email API!!!')

def parseESETProtectHubKey(email_obj: Union[BaseEmailAPI, WebWrapperEmailAPI], driver: Optional[WebDriver] = None, delay=3.0, max_iter=100):
    for _ in range(max_iter):
        license_data = None
        try:
            messages = email_obj.get_messages()
            if not messages:
                time.sleep(delay)
                continue
                
            for message in messages:
                if message['from'] == 'noreply@orders.eset.com' and message['subject'].lower().find('welcome to eset. here') != -1:
                    if message.get('body'):
                        license_data = message['body']
                    elif isinstance(email_obj, WebWrapperEmailAPI):
                        if driver is None:
                            raise ValueError('driver argument must not be None!')
                        email_obj.open_mail(message['id'])
                        license_data = driver.page_source
                    break
        except Exception as e:
            logging.info(f"[parseESETProtectHubKey] Error: {e}")

        if license_data:
            license_data = str(license_data)
            try:
                license_key_match = re.search(r'[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}', license_data)
                license_key = license_key_match.group() if license_key_match else None

                license_id_match = re.search(r'[A-Z0-9]{3}-[A-Z0-9]{3}-[A-Z0-9]{3}', license_data)
                license_id = license_id_match.group() if license_id_match else None

                dates = re.findall(r'\d{2}[./]\d{2}[./]\d{4}', license_data)
                license_out_date = dates[-1] if dates else None

                return license_key, license_out_date, license_id
            except Exception as e:
                pass
                
        time.sleep(delay)

    raise RuntimeError('ESET ProtectHub data waiting time has been exceeded!!!')