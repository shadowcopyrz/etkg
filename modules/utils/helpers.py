from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

from typing import Union, List

import random
import string


class button_with_text_is_clickable:
    """
    Selenium Custom Expected Condition.
    Searches for a button with the specified text and verifies that it is not disabled.
    """
    def __init__(self, texts: Union[str, List[str]]):
        self.targets = [t.lower() for t in (texts if isinstance(texts, list) else [texts])]

    def __call__(self, driver: WebDriver):
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        for button in buttons:
            button_text = (button.get_attribute('innerText') or '').strip().lower()
            
            if button_text in self.targets:
                if button.get_attribute('disabled') or button.get_attribute('aria-disabled') == 'true':
                    return False 
                
                return button
                
        return False

def dataGenerator(length, only_numbers=False):
    """generates a password by default. If only_numbers=True - phone number"""
    data = []
    if only_numbers: # phone number
        data = [random.choice(string.digits) for _ in range(length)]
    else: # password
        length += random.randint(1, 10)
        data = [ # 1 uppercase & lowercase letter, 1 number, 1 special character
            random.choice(string.ascii_uppercase),
            random.choice(string.ascii_lowercase),
            random.choice(string.digits),
            random.choice("""!"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~""")
        ]
        characters = string.ascii_letters + string.digits + string.punctuation
        data += [random.choice(characters) for _ in range(length-3)]
        random.shuffle(data)
    return ''.join(data)