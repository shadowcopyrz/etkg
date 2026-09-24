from typing import Optional, Union, Callable, List, Dict, Any
from colorama import Fore

import subprocess
import os

def clear_console() -> None:
    subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)

class MenuAction:
    def __init__(self, title: str, func: Union[Callable, 'ViewMenu']):
        self.title = title
        self.function = func

    def render_title(self) -> str:
        return self.title
    
    def run(self) -> None:
        if isinstance(self.function, ViewMenu):
            self.function.view()
        else:
            self.function()

class OptionAction:
    def __init__(
        self, 
        args: Dict[str, Any],
        title: str,
        action: str,
        args_names: Union[List[str], str],
        choices: Optional[List[str]] = None,
        default_value: Any = None,
        data_type: type = str,
        data_range: Optional[List[Any]] = None
    ):
        self.args = args
        self.title = title
        self.action = action
        self.args_names = args_names
        self.choices = choices or []
        self.value = default_value
        self.data_type = data_type
        self.data_range = data_range

    def _get_arg_key(self, name: str) -> str:
        return name.replace('-', '_')

    def render_title(self) -> str:
        if self.action in ('store_true', 'choice'):
            return f'{self.title} (selected: {Fore.YELLOW}{self.value}{Fore.RESET})'

        if self.action == 'manual_input':
            return f'{self.title} (saved: {Fore.YELLOW}{self.value}{Fore.RESET})'

        if self.action == 'bool_switch' and isinstance(self.args_names, str):
            key = self._get_arg_key(self.args_names)
            if self.args.get(key):
                return f'{self.title} {Fore.GREEN}(enabled){Fore.RESET}'
            return f'{self.title} {Fore.RED}(disabled){Fore.RESET}'

        raise ValueError(f'[MBCI.render_title] Unknown action ({self.action})!')

    def run(self) -> None:
        if self.action == 'bool_switch' and isinstance(self.args_names, str):
            key = self._get_arg_key(self.args_names)
            self.args[key] = not self.args.get(key, False)
            return None
        
        menu_items = self.choices if self.choices else self.args_names

        while True:
            clear_console()
            print(f'{self.title}\n')
            
            if self.action != 'manual_input':
                for i, item in enumerate(menu_items):
                    print(f'{i + 1} - {item}')
                print()
            
            try:
                if self.action == 'manual_input':
                    if self.data_range:
                        print(f'Allowed values: {self.data_range}\n')
                    
                    raw_val = input('>>> ').strip()
                    val = self.data_type(raw_val)
                    
                    if self.data_range and val not in self.data_range:
                        raise ValueError("Value not in allowed range!")
                        
                    self.value = val
                    if isinstance(self.args_names, str):
                        self.args[self._get_arg_key(self.args_names)] = val
                    break

                index = int(input('>>> ').strip()) - 1
                
                if 0 <= index < len(menu_items):
                    self.value = menu_items[index]
                    if self.action == 'store_true':
                        for name in self.args_names:
                            self.args[self._get_arg_key(name)] = False
                        self.args[self._get_arg_key(self.value)] = True
                    elif self.action == 'choice' and isinstance(self.args_names, str):
                        self.args[self._get_arg_key(self.args_names)] = self.value
                    break
            except ValueError:
                pass

class ViewMenu:
    def __init__(self, title: str):
        self.title = title
        self.items: List[Union[MenuAction, OptionAction]] = []
        self.execution = True

    def add_item(self, menu_action_object: Union[MenuAction, OptionAction]) -> None:
        self.items.append(menu_action_object)
    
    def view(self) -> None:
        self.execution = True
        while self.execution:
            clear_console()
            print(f'{self.title}\n')
            
            for i, item in enumerate(self.items):
                print(f'{i + 1} - {item.render_title()}')
            print()
            
            try:
                selected_index = int(input('>>> ')) - 1
                if 0 <= selected_index < len(self.items):
                    self.items[selected_index].run()
            except ValueError:
                pass
    
    def close(self) -> None:
        self.execution = False