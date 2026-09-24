from modules.utils.constants import I_AM_EXECUTABLE, PATH_TO_SELF
from modules.utils.logger import *

import subprocess
import logging
import pathlib
import shutil
import sys
import os

class Installer:
    def __init__(self):
        self.executable_path: pathlib.Path
        if sys.platform.startswith('win'):
            system_root = os.environ.get('SystemRoot', 'C:\\Windows')
            self.executable_path = pathlib.Path(system_root) / 'app.exe'
        elif sys.platform == 'darwin':
            self.executable_path = pathlib.Path('/usr/local/bin') / 'app'
        else:
            raise NotImplementedError(f"Platform {sys.platform} not supported!")

    def check_install(self):
        exit_code = None
        try:
            exit_code = subprocess.call([self.executable_path, '--return-exit-code', '999'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
        return (exit_code == 999)
    
    def install(self):
        if self.check_install():
            logging.info('The program is already installed!!!')
            logging.warning(f'Location: {self.executable_path}')
            console_log('The program is already installed!!!', OK)
            console_log(f'Location: {self.executable_path}', WARN)
            return True
        if sys.platform.startswith('win') or sys.platform == 'darwin':
            if I_AM_EXECUTABLE:
                try:
                    shutil.copy2(PATH_TO_SELF, self.executable_path)
                    logging.info(f'The program was successfully installed on the path: {self.executable_path}')
                    console_log(f'The program was successfully installed on the path: {self.executable_path}', OK)
                    return True
                except PermissionError:
                    logging.error('No write access, try running the program with elevated permissions!!!')
                    console_log('No write access, try running the program with elevated permissions!!!', ERROR)
                except shutil.SameFileError:
                    logging.error('Installation is pointless from under an installed executable file!!!')
                    console_log('Installation is pointless from under an installed executable file!!!', ERROR)
                except Exception as e:
                    raise RuntimeError(e)
            else:
                logging.error('Installation from source is not possible!!!!')
                console_log('Installation from source is not possible!!!!', ERROR)
            return False