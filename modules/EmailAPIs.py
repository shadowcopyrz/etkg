from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from abc import ABC, abstractmethod
from typing import List, Dict

import logging
import time

PARSE_FAKEMAIL_INBOX = """
let raw_inbox = Array.from(document.getElementById('schranka').children).slice(0, -3)
let inbox = []
for(let i=0; i < raw_inbox.length; i++) {
    let id = raw_inbox[i].dataset.href
    let from = raw_inbox[i].children[0].children[1].tagName.toLowerCase()
    let subject = raw_inbox[i].children[1].innerText.trim()
    inbox.push([id, from, subject])
}
return inbox
"""
PARSE_EMAILFAKE_INBOX = """
let inbox = []
let messages = document.getElementById('email-table').children
for (let i = 0; i < messages.length; i++)
{
    let message = messages[i]
    let childrens = messages[i].children
    if (message.hasAttribute('id') && message.id == 'mail-summary-head')
        continue
    else if (message.hasAttribute('id') && message.id == 'mail-summary-body')
        inbox.push(['https://emailfake.com', childrens[0].children[0].children[4].innerText, childrens[0].children[0].children[7].innerText])
    else
        inbox.push([message, childrens[0].innerText, childrens[1].innerText])
}
return inbox
"""


class BaseEmailAPI(ABC):
    def __init__(self):
        self.class_name = self.__class__.__name__.lower().replace('api', '')
        self.email: str = ''

    @abstractmethod
    def init(self) -> bool:
        """Register email and save to self.email"""
        pass

    @abstractmethod
    def get_messages(self) -> List[Dict[str, str]]:
        """return: [{'id': '...', 'from': '...', 'subject': '...', 'body': '...'}]"""
        pass

class CustomEmailAPI(BaseEmailAPI):
    def init(self) -> bool:
        return True

    def get_messages(self) -> list:
        return []

class WebWrapperEmailAPI(BaseEmailAPI):
    def __init__(self, driver: WebDriver):
        super().__init__()
        self.driver = driver
        self.window_handle = None
    
    def init(self) -> bool:
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                if self._perform_init():
                    return True
            except Exception as e:
                logging.info(f"[{self.class_name}] init error (attempt {attempt + 1}/{max_attempts}): {str(e)}")
                time.sleep(1)
                
        logging.critical(f"[{self.class_name}] init failed {max_attempts} attempts!!!")
        return False

    @abstractmethod
    def _perform_init(self) -> bool:
        pass

    @abstractmethod
    def open_mail(self, mail_id: str):
        """Open mail in browser by mail_id"""
        pass

class FakeMailAPI(WebWrapperEmailAPI):
    def _perform_init(self) -> bool:     
        self.driver.get('https://www.fakemail.net')
        self.window_handle = self.driver.current_window_handle

        wait = WebDriverWait(self.driver, 5)
        email_element = wait.until(EC.presence_of_element_located((By.ID, 'email')))

        wait.until(lambda d: email_element.text.strip() != '')

        self.email = email_element.text.strip()
        return True

    def get_messages(self) -> List[Dict[str, str]]:
        self.driver.switch_to.window(self.window_handle)
        self.driver.get('https://www.fakemail.net')

        raw_inbox = self.driver.execute_script(PARSE_FAKEMAIL_INBOX)
        if not raw_inbox:
            return []

        return [{
            'id': msg[0],
            'from': msg[1],
            'subject': msg[2],
            'body': ''
        } for msg in raw_inbox]
    
    def open_mail(self, mail_id: str):
        self.driver.switch_to.window(self.window_handle)
        self.driver.get(f'https://www.fakemail.net/email/id/{mail_id}')

class EmailFakeAPI(WebWrapperEmailAPI):
    def __init__(self, driver):
        super().__init__(driver)
        self.opened_mail = False

    def _perform_init(self) -> bool:
        self.driver.get('https://emailfake.com/fake_email_generator')
        self.window_handle = self.driver.current_window_handle

        wait = WebDriverWait(self.driver, 5)
        email_element = wait.until(EC.presence_of_element_located((By.ID, 'email_ch_text')))

        wait.until(lambda d: email_element.text.split() != '')

        self.email = email_element.text.strip()
        self.driver.get('https://emailfake.com')
        return True

    def get_messages(self) -> List[Dict[str, str]]:
        self.driver.get('https://emailfake.com')
        self.driver.switch_to.window(self.window_handle)

        try:
            raw_inbox = self.driver.execute_script(PARSE_EMAILFAKE_INBOX)
            if not raw_inbox:
                return []

            return [{
                'id': msg[0],
                'from': msg[1],
                'subject': msg[2],
                'body': ''
            } for msg in raw_inbox]
        except Exception:
            return []
    
    def open_mail(self, mail_id: str):
        self.driver.switch_to.window(self.window_handle)
        wait = WebDriverWait(self.driver, 5)
        if isinstance(mail_id, WebElement):
            self.driver.execute_script('arguments[0].click();', mail_id)
        else:
            self.driver.get(mail_id)
        wait.until(EC.presence_of_element_located((By.ID, 'mail-summary-body')))