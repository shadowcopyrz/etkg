from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

from typing import Optional, Union, List

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


def select_country(
    self, 
    target_country: str = "Ukraine", 
    dropdown_id: str = "country-select"
) -> bool:
    logging.info(f"Selecting country: '{target_country}'...")
    wait = WebDriverWait(self.driver, 10)
    actions = ActionChains(self.driver)

    try:
        # 1. Находим целевой контейнер по ID (или запасному селектору)
        container = wait.until(
            EC.presence_of_element_located((
                By.XPATH, 
                f"//*[@id='{dropdown_id}'] | //*[contains(@class, '{dropdown_id}')]"
            ))
        )
        
        # Центрируем во вьюпорте, чтобы перекрыть sticky-шапки и плавающие кнопки
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", container)

        # 2. Проверяем, не выбрана ли страна уже
        try:
            current_value = container.find_element(
                By.CSS_SELECTOR, '[class*="single-value"], [class*="singleValue"]'
            ).text.strip()
            if current_value.lower() == target_country.strip().lower():
                logging.info(f"Country '{target_country}' is already selected.")
                return True
        except NoSuchElementException:
            pass

        # 3. Кликаем по контролу для открытия меню
        control = container.find_element(By.CSS_SELECTOR, '[class*="control"]') if "control" not in container.get_attribute("class") else container
        actions.move_to_element(control).click().perform()

        # 4. Находим input внутри открытого селекта и вводим название страны
        input_field = wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR, 
                f"#{dropdown_id} input, [class*='control'] input"
            ))
        )
        
        # Очистка и быстрый ввод названия
        input_field.send_keys(Keys.CONTROL + "a")
        input_field.send_keys(Keys.BACKSPACE)
        input_field.send_keys(target_country)

        # 5. Ожидаем появление нужной опции в выпадающем списке
        # Ищем строго по тексту нужной страны внутри элементов опций меню
        option_xpath = (
            f"//*[contains(@class, 'option') and "
            f"translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = "
            f"'{target_country.strip().lower()}']"
        )

        try:
            option_el = wait.until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
            
            # Двойной fallback на случай перекрытия соседними слоями
            try:
                actions.move_to_element(option_el).click().perform()
            except Exception:
                self.driver.execute_script("arguments[0].click();", option_el)

        except TimeoutException:
            # Fallback: если меню отфильтровалось до 1 элемента, подтверждаем через ENTER
            logging.warning("Option element click timed out; sending ENTER key to input...")
            input_field.send_keys(Keys.ENTER)

        # 6. Подтверждение успешного выбора
        wait.until(
            lambda d: target_country.lower() in container.find_element(
                By.CSS_SELECTOR, '[class*="single-value"], [class*="singleValue"]'
            ).text.lower()
        )

        logging.info(f"Country '{target_country}' successfully selected!")
        return True

    except Exception as e:
        logging.error(f"Failed to select country '{target_country}': {e}")
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

def format_output_block(prefix: str, data: dict, add_prefix_for_keys: Optional[List[str]] = None) -> str:
    sep = '-' * 49
    lines = ['', sep]
    prefix = prefix[::-1]
    for key, val in data.items():
        if key == '' and val is None:
            lines.append('')    
        else:
            if add_prefix_for_keys and key in add_prefix_for_keys:
                lines.append(f'{prefix}{key[::-1]}: {val}')
            else:
                lines.append(f'{key[::-1]}: {val}')
    lines.extend([sep, ''])
    return '\n'.join(lines)
