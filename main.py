from modules.EmailAPIs import *

from typing import List, Any

import sys

# ---- Quick settings [for Developers] ----
VERSION = ['v1.5.7.0', 1570]
LOGO = f"""
███████╗███████╗███████╗████████╗   ██╗  ██╗███████╗██╗   ██╗ ██████╗ ███████╗███╗   ██╗
██╔════╝██╔════╝██╔════╝╚══██╔══╝   ██║ ██╔╝██╔════╝╚██╗ ██╔╝██╔════╝ ██╔════╝████╗  ██║
█████╗  ███████╗█████╗     ██║      █████╔╝ █████╗   ╚████╔╝ ██║  ███╗█████╗  ██╔██╗ ██║
██╔══╝  ╚════██║██╔══╝     ██║      ██╔═██╗ ██╔══╝    ╚██╔╝  ██║   ██║██╔══╝  ██║╚██╗██║   
███████╗███████║███████╗   ██║      ██║  ██╗███████╗   ██║   ╚██████╔╝███████╗██║ ╚████║   
╚══════╝╚══════╝╚══════╝   ╚═╝      ╚═╝  ╚═╝╚══════╝   ╚═╝    ╚═════╝ ╚══════╝╚═╝  ╚═══╝                                                                      
                                                Project Version: {VERSION[0]}
                                                Project Devs: rzc0d3r, AdityaGarg8, k0re,
                                                              Fasjeit, alejanpa17, Ischunddu,
                                                              soladify, AngryBonk, Xoncia,
                                                              Anteneh13, otre4, AHDR3,
                                                              Shariful797, ImHisako,
                                                              ppsmurf, ugvfpdcuwfnh, chrisdaloa
                                                Telegram: https://t.me/rzc0d3r_official
"""
if '--no-logo' in sys.argv:
    LOGO = f'ESET KeyGen {VERSION[0]} by rzc0d3r\n'

DEFAULT_PATH_TO_PROXY_FILE = 'proxies.txt'
DEFAULT_EMAIL_API = 'emailfake'
EMAIL_API_CLASSES = {
    'fakemail': FakeMailAPI,
    'emailfake': EmailFakeAPI,
}
AVAILABLE_EMAIL_APIS = list(EMAIL_API_CLASSES.keys())

args: Dict[str, Any] = {
    'auto_detect_browser': True,
    'chrome': False,
    'firefox': False,
    'waterfox': False,
    'edge': False,
    'safari': False,

    'key': True,
    'small_business_key': False,
    'advanced_key': False,
    'account': False,
    'protecthub_account': False,
    'update': False,
    'install': False,
    'return_exit_code': 0,

    'no_headless': False,
    'custom_browser_location': '',
    'email_api': DEFAULT_EMAIL_API,
    'custom_email_api': False,
    'skip_update_check': False,
    'no_logo': False,
    'disable_progress_bar': False,
    'disable_output_file': False,
    'output_file': '',
    'repeat': 1,
    'proxy_file': DEFAULT_PATH_TO_PROXY_FILE,
    
    'silent': False,
    'disable_logging': False
}

MBCI_BROWSERS: List[str] = ['auto_detect_browser', 'chrome', 'firefox', 'waterfox', 'edge', 'safari']
MBCI_MODES_OF_OPERATION: List[str] = ['key', 'small_business_key', 'advanced_key', 'account', 'protecthub_account', 'update', 'install']
# -----------------------------------------------------------------------------------------------

from modules.WebDriverInstaller import *

from modules.eset.core import EsetProtectHubRegister as EPHR
from modules.eset.core import EsetProtectHubKeygen as EPHK
from modules.eset.core import IPBlockedException
from modules.eset.core import EsetRegister as ER
from modules.eset.core import EsetKeygen as EK

from modules.utils.installer import *
from modules.utils.webdriver import *
from modules.utils.constants import *
from modules.utils.helpers import *
from modules.utils.logger import *
from modules.Updater import *
from modules.MBCI import *

import contextlib
import traceback
import platform
import colorama
import platform
import datetime
import argparse
import logging
import json
import copy
import re
import io

# -----------------------------------------------------------------------------------------------

if ('--disable-logging' not in sys.argv and not MBCI_MODE) or ('--disable-logging' in sys.argv and SILENT_MODE): # Here it is present to catch an error when parsing arguments using argparse
    enable_logging()

DRIVER = None
ARGS_DEFAULT = copy.deepcopy(args)

PROXIES = []
PROXIES_LEN = 0
PROXY_COUNTER = 1
PROXY_ERROR_COUNTER = 0
PROXY_ERROR_COUNTER_LIMIT = 3

CHROME_PROXY_EXTENSION_PATH = ''

class MBCIConfigManager:
    def __init__(self, path=CONFIG_PATH):
        self.path = path

    @property
    def is_exists(self):
        return os.path.isfile(self.path)

    def save(self, args: Dict[str, Any]) -> bool:
        config: Dict[str, Any] = {}

        active_browser = next((k for k in MBCI_BROWSERS if args.get(k)), None)
        if active_browser and not ARGS_DEFAULT.get(active_browser):
            config['Browser'] = active_browser

        active_mode = next((k for k in MBCI_MODES_OF_OPERATION if args.get(k)), None)
        if active_mode and not ARGS_DEFAULT.get(active_mode):
            config['Mode of operation'] = active_mode

        if args.get('email_api') != ARGS_DEFAULT['email_api']:
            config['Email API'] = args.get('email_api')

        excluded_groups = set(MBCI_BROWSERS + MBCI_MODES_OF_OPERATION + ['email_api', 'return_exit_code'])
        for key, default_value in ARGS_DEFAULT.items():
            if key in excluded_groups:
                continue
                
            current_value = args.get(key)
            if current_value != default_value:
                config[key] = current_value

        if config or self.is_exists:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            return bool(config)

        return False
    
    def load_as_sys_argv(self) -> List[str]:
        if not self.is_exists:
            return []
            
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            return []

        all_args = copy.deepcopy(ARGS_DEFAULT)

        browser = config.pop('Browser', None)
        if browser:
            browser = browser.replace('-', '_')
            if browser in MBCI_BROWSERS:
                for b in MBCI_BROWSERS:
                    all_args[b] = False
                all_args[browser] = True

        mode = config.pop('Mode of operation', None)
        if mode:
            mode = mode.replace('-', '_')
            if mode in MBCI_MODES_OF_OPERATION:
                for m in MBCI_MODES_OF_OPERATION:
                    all_args[m] = False
                all_args[mode] = True

        email_api = config.pop('Email API', None)
        if email_api:
            all_args['email_api'] = email_api

        for key, value in config.items():
            norm_key = key.replace('-', '_')
            if norm_key in ARGS_DEFAULT:
                all_args[norm_key] = value

        sys_argv: List[str] = []
        
        for key, value in all_args.items():
            if key == 'return_exit_code':
                continue
                
            cli_flag = f"--{key.replace('_', '-')}"
            
            if isinstance(value, bool):
                if value:
                    sys_argv.append(cli_flag)
            else:
                if value != ARGS_DEFAULT[key]:
                    sys_argv.extend([cli_flag, str(value)])
                    
        return sys_argv

def RunMenu():
    MainMenu = ViewMenu(LOGO+'\n---- Main Menu ----')

    SettingMenu = ViewMenu(LOGO+'\n---- Settings Menu ----')
    SettingMenu.add_item(
        OptionAction(
            args,
            title='Browsers',
            action='store_true',
            args_names=MBCI_BROWSERS,
            default_value=[key for key in MBCI_BROWSERS if args[key.replace('-', '_')]][0]
        )
    )
    SettingMenu.add_item(
        OptionAction(
            args,
            title='Modes of operation',
            action='store_true',
            args_names=MBCI_MODES_OF_OPERATION,
            default_value=[key for key in MBCI_MODES_OF_OPERATION if args[key.replace('-', '_')]][0]
        )
    )
    SettingMenu.add_item(
        OptionAction(
            args,
            title='Email APIs',
            action='choice',
            args_names='email-api',
            choices=AVAILABLE_EMAIL_APIS,
            default_value=args['email_api']
        )
    )
    SettingMenu.add_item(
        OptionAction(
            args,
            title='--no-headless',
            action='bool_switch',
            args_names='no-headless'
        )
    )
    SettingMenu.add_item(
        OptionAction(
            args,
            title='--custom-browser-location',
            action='manual_input',
            args_names='custom-browser-location',
            default_value=args['custom_browser_location']
        )
    )
    SettingMenu.add_item(
        OptionAction(
            args,
            title='--custom-email-api',
            action='bool_switch',
            args_names='custom-email-api'
        )
    )
    SettingMenu.add_item(
        OptionAction(
            args,
            title='--skip-update-check',
            action='bool_switch',
            args_names='skip_update_check'
        )
    )
    SettingMenu.add_item(
        OptionAction(
            args,
            title='--disable-progress-bar',
            action='bool_switch',
            args_names='disable_progress_bar'
        )
    )
    SettingMenu.add_item(
        OptionAction(
            args,
            title='--disable-output-file',
            action='bool_switch',
            args_names='disable_output_file'
        )
    )
    SettingMenu.add_item(
        OptionAction(
            args,
            title='--output-file',
            action='manual_input',
            args_names='output-file',
            default_value=args['output_file']
        )
    )
    SettingMenu.add_item(
        OptionAction(
            args,
            title='--disable-logging',
            action='bool_switch',
            args_names='disable_logging'
        )
    )
    SettingMenu.add_item(
        OptionAction(
            args,
            title='--repeat',
            action='manual_input',
            args_names='repeat',
            default_value=args['repeat'],
            data_type=int
        )
    )
    SettingMenu.add_item(
        OptionAction(
            args,
            title='--proxy-file',
            action='manual_input',
            args_names='proxy-file',
            default_value=args['proxy_file']
        )
    )

    def exit_with_save_config():
        MBCIConfigManager().save(args)
        sys.exit()

    SettingMenu.add_item(MenuAction('Back', SettingMenu.close))
    MainMenu.add_item(MenuAction('Settings', SettingMenu))
    MainMenu.add_item(MenuAction('Start', MainMenu.close))
    MainMenu.add_item(MenuAction('Exit', exit_with_save_config))
    MainMenu.view()

def parse_argv(sys_argv=None):
    if '--return-exit-code' not in sys.argv and not SILENT_MODE and sys_argv is None:
        print(LOGO)
    if MBCI_MODE and sys_argv is None: # for MBCI mode
        RunMenu()
    else: # CLI
        args_parser = argparse.ArgumentParser()
        ENABLE_REQUIRED_ARGUMENTS = True
        GLOBAL_OVERRIDE_ARGUMENTS = ['--update',  '--install', '--return-exit-code']
        for argv in GLOBAL_OVERRIDE_ARGUMENTS:
            ENABLE_REQUIRED_ARGUMENTS = (argv not in sys.argv)
            if not ENABLE_REQUIRED_ARGUMENTS:
                break
        # Required
        ## Browsers
        args_browsers = args_parser.add_mutually_exclusive_group(required=ENABLE_REQUIRED_ARGUMENTS)   
        args_browsers.add_argument('--chrome', action='store_true', help='Launching the program via Google Chrome browser')
        args_browsers.add_argument('--firefox', action='store_true', help='Launching the program via Mozilla Firefox browser')
        args_browsers.add_argument('--waterfox', action='store_true', help='Launching the program via Waterfox browser')
        args_browsers.add_argument('--edge', action='store_true', help='Launching the program via Microsoft Edge browser')
        args_browsers.add_argument('--safari', action='store_true', help='Launching the program via Apple Safari browser')
        args_browsers.add_argument('--auto-detect-browser', action='store_true', help='The program itself will determine which browser to use (from the list of supported browsers)')
        
        ## Modes of operation
        args_modes = args_parser.add_mutually_exclusive_group(required=ENABLE_REQUIRED_ARGUMENTS)
        args_modes.add_argument('--key', action='store_true', help='muimerP ytiruceS tramS TESE rof yek esnecil a gnitaerC'[::-1])
        args_modes.add_argument('--small-business-key', action='store_true', help=')secived 5 - yek 1( ytiruceS ssenisuB llamS TESE rof yek esnecil a gnitaerC'[::-1])
        args_modes.add_argument('--advanced-key', action='store_true', help=')secived 52 - yek 1( decnavdA TCETORP TESE rof yek esnecil a gnitaerC'[::-1])
        args_modes.add_argument('--account', action='store_true', help=')noisrev lairt eerf eht etavitca ot( tnuoccA EMOH TESE a gnitaerC'[::-1])
        args_modes.add_argument('--protecthub-account', action='store_true', help=')noisrev lairt eerf eht etavitca ot( tnuoccA buHtcetorP TESE a gnitaerC'[::-1])
        args_modes.add_argument('--only-webdriver-update', action='store_true', help='yek esnecil dna tnuocca gnitareneg tuohtiw sresworb dna srevirdbew sllatsni/setadpU'[::-1])
        args_modes.add_argument('--update', action='store_true', help='Switching to program update mode - Overrides all arguments that are available!!!')
        args_modes.add_argument('--install', action='store_true', help='Installs the program and adds it to the environment variable (Windows & macOS only) - Overrides all arguments that are available!!!')   
        args_modes.add_argument('--return-exit-code', type=int, default=0, help='[For developers] Will make the program return the exit code you requested - Overrides all arguments that are available!!!')
        # Optional
        args_parser.add_argument('--skip-webdriver-menu', action='store_true', help='Skips installation/upgrade webdrivers through the my custom wrapper (the built-in selenium-manager will be used)')
        args_parser.add_argument('--no-headless', action='store_true', help='Shows the browser at runtime (the browser is hidden by default, but on Windows 7 this option is enabled by itself)')
        args_parser.add_argument('--custom-browser-location', type=str, default='', help='Set path to the custom browser (to the binary file, useful when using non-standard releases, for example, Firefox Developer Edition)')
        args_parser.add_argument('--email-api', choices=AVAILABLE_EMAIL_APIS, default=DEFAULT_EMAIL_API, help=f'Specify which api to use for mail, default - {DEFAULT_EMAIL_API}')
        args_parser.add_argument('--custom-email-api', action='store_true', help='Allows you to manually specify any email, and all work will go through it. But you will also have to manually read inbox and do what is described in the documentation for this argument')
        args_parser.add_argument('--skip-update-check', action='store_true', help='Skips checking for program updates')
        args_parser.add_argument('--no-logo', action='store_true', help='Replaces ASCII-Art with plain text')
        args_parser.add_argument('--disable-progress-bar', action='store_true', help='Disables the webdriver download progress bar')
        args_parser.add_argument('--disable-output-file', action='store_true', help='Disables the output txt file generation')
        args_parser.add_argument('--output-file', type=str, default='', help='Specifies the path to the output file')
        args_parser.add_argument('--repeat', type=int, default=1, help='Specifies how many times to repeat generation')
        args_parser.add_argument('--proxy-file', type=str, default=DEFAULT_PATH_TO_PROXY_FILE, help=f'Specifies the path from where the list of proxies will be read from, default - {DEFAULT_PATH_TO_PROXY_FILE}')

        # Logging
        args_logging = args_parser.add_mutually_exclusive_group()
        args_logging.add_argument('--silent', action='store_true', help='Disables message output, output called by the --custom-email-api argument will still be output!')
        args_logging.add_argument('--disable-logging', action='store_true', help='Disables logging')

        parsed_args = None
        captured_stderr = io.StringIO()
        with contextlib.redirect_stderr(captured_stderr):
            try:
                parsed_args = vars(args_parser.parse_args(sys_argv))
                parsed_args['repeat'] = abs(parsed_args['repeat'])
                if sys_argv is None:
                    logging.info(f'Parsed arguments: {parsed_args}')
            except SystemExit:
                captured_stderr = captured_stderr.getvalue().strip()
                if captured_stderr != '':
                    if sys_argv is None:
                        logging.error(captured_stderr)
                    console_log(captured_stderr)
                if sys_argv is None:
                    exit_program(-1)
        return parsed_args

def exit_program(exit_code, driver=None):
    if MBCI_MODE and not SILENT_MODE:
        input('\nPress Enter to exit...')
    if driver is not None:
        driver.quit()
    sys.exit(exit_code)

def update():
    Updater().updater_menu()
    exit_program(0)

def main(disable_exit=False):
    global PROXY_ERROR_COUNTER_LIMIT
    global PROXY_ERROR_COUNTER
    global DRIVER
    if args['return_exit_code'] != 0:
        sys.exit(args['return_exit_code'])
    if MBCI_MODE and not disable_exit:
        print()
    try:
        # changing input arguments for special cases
        if not args['update'] and not args['install']:
            if IS_LEGACY_WINDOWS:
                args['no_headless'] = True
            elif args['advanced_key'] or args['protecthub_account']:
                args['no_headless'] = True
        # check program updates
        elif args['update']:
            logging.info('-- Updater --')
            console_log(f'{Fore.LIGHTMAGENTA_EX}-- Updater --{Fore.RESET}\n')
            update()
        elif args['install']:
            logging.info('-- Installer --')
            console_log(f'{Fore.LIGHTMAGENTA_EX}-- Installer --{Fore.RESET}\n')
            Installer().install()
            exit_program(0)
        if not args['skip_update_check'] and not args['update']:
            try:
                logging.info('-- Updater --')
                console_log(f'{Fore.LIGHTMAGENTA_EX}-- Updater --{Fore.RESET}\n')
                updater = Updater()
                latest_cloud_version = list(updater.get_releases().keys())[0]
                latest_cloud_version_int = latest_cloud_version[1:].split('.')
                latest_cloud_version_int = int(''.join(latest_cloud_version_int[:-1])+latest_cloud_version_int[-1][0])
                if VERSION[1] > latest_cloud_version_int:
                    logging.warning(f'The project has an unreleased version, maybe you are using a build from the developer?')
                    console_log(f'The project has an unreleased version, maybe you are using a build from the developer?\n', WARN, True, SILENT_MODE)
                elif latest_cloud_version_int > VERSION[1]:
                    logging.info(f'Project update is available up to version: {latest_cloud_version}')
                    if not SILENT_MODE:
                        console_log(f'Project update is available up to version: {colorama.Fore.GREEN}{latest_cloud_version}{colorama.Fore.RESET}', WARN)
                        update_now = input(f'[  {colorama.Fore.YELLOW}INPT{colorama.Fore.RESET}  ] {colorama.Fore.CYAN}Do you want to update right now? (y/n): {colorama.Fore.RESET}').strip().lower()
                        if update_now == 'y':
                            update()
                        else:
                            console_log(f'The update has been ignored\n', INFO)
                else:
                    logging.info('Project up to date!!!')
                    console_log('Project up to date!!!\n', OK)
            except Exception as e:
                logging.error('EXC_INFO:', exc_info=True)
        
        # initialization and configuration of everything necessary for work            
        webdriver_path = None
        browser_name = GOOGLE_CHROME
        custom_browser_location = None if args['custom_browser_location'] == '' else args['custom_browser_location']
        webdriver_installer = WebDriverInstaller(browser_name, custom_browser_location)

        if args['auto_detect_browser']:
            result = webdriver_installer.detect_installed_browser()
            if result is not None:
                browser_name = result[0]
                webdriver_installer = WebDriverInstaller(browser_name, custom_browser_location)
        else:
            if args['chrome']:
                browser_name = GOOGLE_CHROME
                global CHROME_PROXY_EXTENSION_PATH
                if PROXIES != []:
                    CHROME_PROXY_EXTENSION_PATH = ChromeProxyExtensionManager.create_extension(*PROXIES[0])
                else:
                    CHROME_PROXY_EXTENSION_PATH = ''
            elif args['firefox']:
                browser_name = MOZILLA_FIREFOX
            elif args['waterfox']:
                browser_name = WATERFOX
            elif args['edge']:
                browser_name = MICROSOFT_EDGE
            elif args['safari']:
                browser_name = APPLE_SAFARI
            webdriver_installer = WebDriverInstaller(browser_name, custom_browser_location)

        if IS_LEGACY_WINDOWS:
            webdriver_path, custom_browser_location = webdriver_installer.menu(args['disable_progress_bar'])

        DRIVER = initSeleniumWebDriver(browser_name, webdriver_path, custom_browser_location, CHROME_PROXY_EXTENSION_PATH, (not args['no_headless']))
        if DRIVER is None:
            raise RuntimeError(f'{browser_name} initialization error!')
        if PROXIES != []:
            scheme, host, port, username, password = PROXIES[0]
            global PROXY_COUNTER
            if username != '' or password != '':
                logging.info(f'[{PROXY_COUNTER}/{PROXIES_LEN}] Using proxy with authentication: {host}:{port}')
                console_log(f'[{PROXY_COUNTER}/{PROXIES_LEN}] Using proxy with authentication: {host}:{port}', INFO)
            else:
                logging.info(f'[{PROXY_COUNTER}/{PROXIES_LEN}] Using proxy: {host}:{port}')
                console_log(f'[{PROXY_COUNTER}/{PROXIES_LEN}] Using proxy: {host}:{port}', INFO)

        # main part of the program
        logging.info(f'-- KeyGen --')
        console_log(f'\n{Fore.LIGHTMAGENTA_EX}-- KeyGen --{Fore.RESET}\n')
        if not args['custom_email_api']:
            email_api_name = args['email_api']

            logging.info(f'[{email_api_name}] Mail registration...')
            console_log(f'[{email_api_name}] Mail registration...', INFO)

            email_class = EMAIL_API_CLASSES[email_api_name]
            if issubclass(email_class, WebWrapperEmailAPI): # WebWrapper API, need to pass the selenium object to the class initialization
                email_obj = email_class(DRIVER)
            else: # real APIs without the need for a browser
                email_obj = email_class()

            try:
                if email_obj.init() and email_obj.email != '':
                    logging.info('Mail registration completed successfully!')
                    console_log('Mail registration completed successfully!', OK)
                else:
                    logging.critical('Mail registration was not completed, try using a different Email API!')
                    console_log('Mail registration was not completed, try using a different Email API!\n', ERROR)
                    PROXY_ERROR_COUNTER += 1
            except Exception as e:
                logging.error(f'Mail registration failed: {str(e)}')
        else:
            email_obj = CustomEmailAPI()
            while True:
                email = input(f'[  {colorama.Fore.YELLOW}INPT{colorama.Fore.RESET}  ] {colorama.Fore.CYAN}Enter the email address you have access to: {colorama.Fore.RESET}').strip()
                match = re.match(r'^[-a-z0-9+.]+@[a-z0-9]+(\.[a-z]+)+$', email)
                if match:
                    email_obj.email = match.group()
                    console_log('Mail has the correct syntax!', OK)
                    break
                else:
                    console_log('Invalid email syntax!!!', ERROR)
        
        if email_obj.email != '':
            e_passwd = dataGenerator(10)
            l_key = None
            obtained_from_site = False
            # ESET HOME
            if args['account'] or args['key'] or args['small_business_key']:
                ER_obj = ER(email_obj, e_passwd, DRIVER)
                ER_obj.createAccount()
                ER_obj.confirmAccount()
                output_line = '\n'.join([
                    '',
                    '-------------------------------------------------',
                    '}{ :liamE tnuoccA'[::-1].format(email_obj.email),
                    '}{ :drowssaP tnuoccA'[::-1].format(e_passwd),
                    '-------------------------------------------------',
                    ''
                ])
                output_filename = 'ESET ACCOUNTS.txt'
                if args['key'] or args['small_business_key']:
                    output_filename = 'ESET KEYS.txt'
                    EK_obj = EK(email_obj, DRIVER, 'ESET HOME' if args['key'] else 'SMALL BUSINESS')
                    EK_obj.sendRequestForKey()
                    l_name, l_key, l_out_date = EK_obj.getLD()
                    output_line = '\n'.join([
                        '',
                        '-------------------------------------------------',
                        '}{ :liamE tnuoccA'[::-1].format(email_obj.email),
                        '}{ :drowssaP tnuoccA'[::-1].format(e_passwd),
                        '',
                        '}{ :emaN esneciL'[::-1].format(l_name),
                        '}{ :yeK esneciL'[::-1].format(l_key),
                        '}{ :etaD tuO esneciL'[::-1].format(l_out_date),
                        '-------------------------------------------------',
                        ''
                    ])

            # ESET ProtectHub
            elif args['protecthub_account'] or args['advanced_key']:
                EPHR_obj = EPHR(email_obj, e_passwd, DRIVER)
                EPHR_obj.createAccount()
                EPHR_obj.confirmAccount()
                EPHR_obj.activateAccount()
                output_line = '\n'.join([
                    '',
                    '---------------------------------------------------------------------',
                    '}{ :liamE tnuoccA buHtcetorP TESE'[::-1].format(email_obj.email),
                    '}{ :drowssaP tnuoccA buHtcetorP TESE'[::-1].format(e_passwd),
                    '---------------------------------------------------------------------',
                    ''
                ])    
                output_filename = 'ESET ACCOUNTS.txt'
                if args['advanced_key']:
                    output_filename = 'ESET KEYS.txt'
                    EPHK_obj = EPHK(email_obj, e_passwd, DRIVER)
                    l_name, l_key, l_out_date, obtained_from_site = EPHK_obj.getLD()
                    if l_name is not None:
                        output_line = '\n'.join([
                            '',
                            '---------------------------------------------------------------------',
                            '}{ :liamE tnuoccA buHtcetorP TESE'[::-1].format(email_obj.email),
                            '}{ :drowssaP tnuoccA buHtcetorP TESE'[::-1].format(e_passwd),
                            '',
                            '}{ :emaN esneciL'[::-1].format(l_name),
                            '}{ :yeK esneciL'[::-1].format(l_key),
                            '}{ :etaD tuO esneciL'[::-1].format(l_out_date),
                            '---------------------------------------------------------------------',
                            ''
                        ])

            # end
            logging.info(output_line)
            console_log(output_line)
            if not args['disable_output_file']:
                out_file = None if args['output_file'] == '' else args['output_file']
                if not out_file:
                    date = datetime.datetime.now()
                    out_file = f'{str(date.day)}.{str(date.month)}.{str(date.year)} - ' + output_filename
                f = open(out_file, 'a')
                f.write(output_line)
                f.close()
            
            if l_key is not None and args['advanced_key'] and obtained_from_site:
                if not SILENT_MODE:
                    unbind_key = input(f'[  {colorama.Fore.YELLOW}INPT{colorama.Fore.RESET}  ] {colorama.Fore.CYAN}Do you want to unbind the key from this account? (y/n): {colorama.Fore.RESET}').strip().lower()
                    if unbind_key == 'y':
                        EPHK_obj.removeLicense()
                else:
                    EPHK_obj.removeLicense()
    except IPBlockedException:
        logging.critical('EXC_INFO:', exc_info=True)
        traceback_string = traceback.format_exc()
        if PROXIES != []:
            PROXIES.remove(PROXIES[0])
            if PROXY_COUNTER < PROXIES_LEN:
                PROXY_COUNTER += 1
        console_log(traceback_string, ERROR)
    except Exception as E:
        PROXY_ERROR_COUNTER_LIMIT += 1
        logging.critical('EXC_INFO:', exc_info=True)
        traceback_string = traceback.format_exc()
        if str(type(E)).find('selenium') and traceback_string.find('Stacktrace:') != -1: # disabling stacktrace output
            traceback_string = traceback_string.split('Stacktrace:', 1)[0]
        console_log(traceback_string, ERROR)

    if PROXIES != [] and PROXY_ERROR_COUNTER == PROXY_ERROR_COUNTER_LIMIT:
        PROXY_ERROR_COUNTER = 0
        PROXIES.remove(PROXIES[0])
        if PROXY_COUNTER < PROXIES_LEN:
            PROXY_COUNTER += 1

    if globals().get('DRIVER', None) and isinstance(DRIVER, WebDriver):
        DRIVER.quit()
    if not disable_exit:
        exit_program(0)

if __name__ == '__main__':
    if MBCI_MODE:
        config_manager = MBCIConfigManager()
        if config_manager.is_exists:
            try:
                config_sys_argv = config_manager.load_as_sys_argv()
                parsed_args = parse_argv(config_sys_argv)
                
                if parsed_args is not None:
                    args = parsed_args
            except Exception as E:
                console_log('\nError loading the config, check its integrity!!!', WARN)
                input('\nPress Enter to continue...')

        parse_argv()
        args['repeat'] = abs(args['repeat'])
        
        try:
            config_manager.save(args)
        except Exception:
            console_log('\nError saving configuration, check write access!!!', WARN)
            input('\nPress Enter to continue...')
    else:
        args = parse_argv() # CLI
    
    if args['disable_logging']:
        logging.basicConfig(level=logging.CRITICAL+1)
    else:
        enable_logging()

    logging.info(f'ESET-KeyGen Version: text={VERSION[0]}, index={VERSION[1]}')
    logging.info(f'I_AM_EXECUTABLE={I_AM_EXECUTABLE}, OS={platform.platform()}, IS_LEGACY_WINDOWS={IS_LEGACY_WINDOWS}')
    logging.info(f'sys.argv: {sys.argv}')
    
    # load proxies from file
    result = WebDriverInstaller(GOOGLE_CHROME).detect_installed_browser()
    browser_name = None
    if result is not None:
        browser_name = result[0]
    if browser_name == GOOGLE_CHROME and os.path.exists(args['proxy_file']) and os.path.isfile(args['proxy_file']):
        PROXIES = ChromeProxyExtensionManager.parse_proxies_from_file(args['proxy_file'])
        PROXIES_LEN = len(PROXIES)
        #random.shuffle(PROXIES)

    if args['repeat'] <= 1:
        main()
    else:
        args['skip_update_check'] = True
        for i in range(args['repeat']):
            try:
                logging.info(f'------------ Initializing of {i+1} start ------------')
                console_log(f'\n{Fore.MAGENTA}------------ Initializing of {Fore.YELLOW}{i+1} {Fore.MAGENTA}start ------------{Fore.RESET}\n')
                is_last_run = (i == args['repeat'] - 1)    
                main(disable_exit=not is_last_run)       
            except KeyboardInterrupt:
                exit_program(0, DRIVER)
