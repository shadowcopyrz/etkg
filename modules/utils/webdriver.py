from modules.WebDriverInstaller import GOOGLE_CHROME, MICROSOFT_EDGE, MOZILLA_FIREFOX, APPLE_SAFARI, WATERFOX
from modules.utils.logger import *

from selenium.webdriver import Chrome, ChromeOptions, ChromeService
from selenium.webdriver import Edge, EdgeOptions, EdgeService
from selenium.webdriver import Firefox, FirefoxOptions, FirefoxService
from selenium.webdriver import Safari, SafariOptions

from typing import Optional, Any

import traceback
import tempfile
import colorama
import platform
import pathlib
import shutil
import os


class ChromeProxyExtensionManager:
    MANIFEST = """
        {
        "version": "1.0.0",
        "manifest_version": 3,
        "name": "Chrome Proxy Manager",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "webRequest",
            "webRequestAuthProvider"
        ],
        "background": {
            "service_worker": "background.js"
        },
        "host_permissions": [
            "<all_urls>"
        ],
        "minimum_chrome_version":"22.0.0"
        }
    """
    
    BACKGROUND_JS = """
        const config = {
            mode: "fixed_servers",
            rules: {
                singleProxy: {
                    scheme: "%s",
                    host: "%s",
                    port: %s
                }
            }
        }
        chrome.proxy.settings.set({
            value: config,
            scope: 'regular'
        }, () => {});
    """

    BACKGROUND_AUTO_AUTH = """
        chrome.webRequest.onAuthRequired.addListener(
        (details, callback) => {
            const authCredentials = {
            username: "%s",
            password: "%s",
            };
            setTimeout(() => {
            callback({ authCredentials });
            }, 200);
        },
        { urls: ["<all_urls>"] },
        ["asyncBlocking"]
        );
    """

    @staticmethod
    def create_extension(scheme: str, host: str, port: int, username='', password='') -> str:
        if scheme == '' or host == '' or port == 0:
            return ''
        
        tempdir = pathlib.Path(tempfile.mkdtemp())

        with open(tempdir.joinpath('manifest.json'), 'x') as f:
            f.write(ChromeProxyExtensionManager.MANIFEST)
        with open(tempdir.joinpath('background.js'), 'x') as f:
            f.write(ChromeProxyExtensionManager.BACKGROUND_JS % (scheme, host, port))
        
        if username != '' or password != '':
            with open(tempdir.joinpath('background.js'), 'a') as f:
                f.write(ChromeProxyExtensionManager.BACKGROUND_AUTO_AUTH % (username, password))

        return str(tempdir.resolve())

    @staticmethod
    def parse_proxies_from_file(path: str):
        proxies = []
        with open(path) as f:
            try:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line != "":
                        proxy = line.split(':') # scheme:host:port:username:password
                        if len(proxy) == 5:
                            proxies.append(proxy)
            except:
                pass
        return proxies

def _apply_headless_options(options: Any, headless: bool) -> None:
    if not headless:
        return

    user_agent = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
    )

    if isinstance(options, FirefoxOptions):
        options.add_argument('--headless')
        options.add_argument('--width=1920')
        options.add_argument('--height=1080')
        options.set_preference('general.useragent.override', user_agent)
    else:
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'--user-agent={user_agent}')

def _apply_common_linux_options(options: Any) -> None:
    if os.name == 'posix':
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

def _hide_windows_console(service: Any, headless: bool) -> None:
    """Hides 'DevTools listening on...' on Windows."""
    if os.name == 'nt' and headless:
        service.creation_flags = 0x08000000

def initSeleniumWebDriver(
    browser_name: str, 
    webdriver_path: Optional[str] = None, 
    browser_path: Optional[str] = None, 
    chrome_proxy_extension_path: str = '', 
    headless: bool = True
) -> Any:
    browser_path = browser_path or ''

    # Fix paths for aarch64 (ARM)
    if platform.machine() == 'aarch64' and browser_name == GOOGLE_CHROME:
        if not webdriver_path and os.path.exists('/usr/bin/chromedriver'):
            webdriver_path = '/usr/bin/chromedriver'
        if not browser_path and os.path.exists('/usr/bin/chromium'):
            browser_path = '/usr/bin/chromium'

    logging.info('-- Browsers Initializer --')
    console_log(f'{colorama.Fore.LIGHTMAGENTA_EX}-- Browsers Initializer --{colorama.Fore.RESET}\n')

    os_name = 'Unknown'
    if os.name == 'posix':
        os_name = 'Linux' if sys.platform.startswith('linux') else 'macOS'
    elif os.name == 'nt':
        os_name = 'Windows'
        
    logging.info(f'Initializing {browser_name} for {os_name}')
    console_log(f'Initializing {browser_name} for {os_name}', INFO)

    driver = None

    if browser_name == GOOGLE_CHROME:
        driver_options = ChromeOptions()
        driver_options.page_load_strategy = 'eager'
        if browser_path:
            driver_options.binary_location = browser_path
            
        driver_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver_options.add_argument('--log-level=3')
        driver_options.add_argument('--lang=en-US')
        
        if chrome_proxy_extension_path:
            driver_options.add_argument(f"--load-extension={chrome_proxy_extension_path}")

        _apply_headless_options(driver_options, headless)
        _apply_common_linux_options(driver_options)
        
        service = ChromeService(executable_path=webdriver_path)
        _hide_windows_console(service, headless)
        
        try:
            driver = Chrome(options=driver_options, service=service)
        except Exception as e:
            logging.critical("EXC_INFO:", exc_info=True)
            # Fix for downloaded chrome update
            if 'only supports' in traceback.format_exc():
                extracted_path = traceback.format_exc().split('path')[-1].split('Stacktrace')[0].strip()
                chrome_dir = extracted_path[:-10]
                
                if 'new_chrome.exe' in os.listdir(chrome_dir):
                    logging.info('Downloaded Google Chrome update is detected! Using new chrome executable file!')
                    console_log('Downloaded Google Chrome update is detected! Using new chrome executable file!', INFO)
                    
                    driver_options.binary_location = chrome_dir + 'new_chrome.exe'
                    driver = Chrome(options=driver_options, service=service)
                else:
                    raise e
            else:
                raise e

    elif browser_name == MICROSOFT_EDGE:
        driver_options = EdgeOptions()
        driver_options.page_load_strategy = 'eager'
        
        if browser_path:
            driver_options.binary_location = browser_path
            
        driver_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver_options.add_argument('--log-level=3')
        driver_options.add_argument('--lang=en-US')
        
        _apply_headless_options(driver_options, headless)
        _apply_common_linux_options(driver_options)
        
        service = EdgeService(executable_path=webdriver_path)
        _hide_windows_console(service, headless)
        
        try:
            driver = Edge(options=driver_options, service=service)
        except Exception as e:
            logging.critical("EXC_INFO:", exc_info=True)
            # Fix for probably user data directory is already in use
            if '--user-data-dir' in traceback.format_exc():
                driver_options.add_argument("--user-data-dir=./edge_tmp")
                shutil.rmtree("edge_tmp", ignore_errors=True)
                os.makedirs('edge_tmp', exist_ok=True)
                driver = Edge(options=driver_options, service=service)
            else:
                raise e

    elif browser_name in (MOZILLA_FIREFOX, WATERFOX):
        driver_options = FirefoxOptions()
        driver_options.page_load_strategy = "eager"
        
        if browser_path and browser_path.strip():
            driver_options.binary_location = browser_path
            
        driver_options.set_preference('intl.accept_languages', 'en-US')
        
        _apply_headless_options(driver_options, headless)
        _apply_common_linux_options(driver_options)
        
        service = FirefoxService(executable_path=webdriver_path)
        _hide_windows_console(service, headless)
        
        # Fix for: Your firefox profile cannot be loaded. it may be missing or inaccessible
        browser_tmp_dir = 'firefox_tmp' if browser_name == MOZILLA_FIREFOX else 'waterfox_tmp'
        os.makedirs(browser_tmp_dir, exist_ok=True)
        os.environ['TMPDIR'] = os.path.join(os.getcwd(), browser_tmp_dir).replace('\\', '/')
        
        driver = Firefox(options=driver_options, service=service)

    elif browser_name == APPLE_SAFARI:
        if os.name == 'nt':
            console_log('Apple Safari is not supported on Windows!!!', ERROR)
            return None
        if os.name == 'posix' and sys.platform.startswith('linux'):
            console_log('Apple Safari is not supported on Linux!!!', ERROR)
            return None
            
        driver_options = SafariOptions()
        try:
            driver = Safari(options=driver_options)
        except Exception as e:
            logging.critical("EXC_INFO:", exc_info=True)
            if "Allow Remote Automation" in traceback.format_exc():
                error_msg = traceback.format_exc().split('Message: ')[-1].strip()
                console_log(error_msg, ERROR)
            else:
                raise e

    return driver