import platform
import pathlib
import sys

I_AM_EXECUTABLE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

if I_AM_EXECUTABLE:
    _self_path = pathlib.Path(sys.executable).resolve()
else:
    _self_path = pathlib.Path(sys.argv[0]).resolve()

PATH_TO_SELF = str(_self_path)
ROOT_DIR = _self_path.parent

CONFIG_PATH = str(ROOT_DIR.joinpath('eset-keygen-config.json'))
LOG_PATH = str(ROOT_DIR.joinpath('ESET-KeyGen.log'))

IS_LEGACY_WINDOWS = sys.platform.startswith('win') and platform.release() in ['7', '8', '8.1']
SILENT_MODE = '--silent' in sys.argv
MBCI_MODE = len(sys.argv) == 1