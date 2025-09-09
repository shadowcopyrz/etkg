from colorama import Fore
from .SharedTools import validate_custom_password, console_log, OK, ERROR

import os

def clear_console():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

class MenuAction(object):
    def __init__(self, title, func):
        self.title = title
        self.function = func

    def render_title(self):
        return self.title
    
    def run(self):
        if isinstance(self.function, ViewMenu):
            self.function.view()
        else:
            self.function()

class OptionAction(object):
    def __init__(self, args, title, action, args_names, choices=[], default_value=None, data_type=str, data_range=None, validation_func=None):
        self.args = args
        self.title = title
        self.action = action
        self.value = default_value
        self.choices = choices
        self.args_names = args_names
        self.data_type = data_type
        self.data_range = data_range
        self.validation_func = validation_func

    def render_title(self):
        if self.action in ['store_true', 'choice']:
            return f'{self.title} (selected: {Fore.YELLOW}{self.value}{Fore.RESET})'
        elif self.action == 'manual_input':
            # Special handling for password display
            if self.args_names == 'custom-password' and self.args['custom_password']:
                masked_password = '*' * len(str(self.args['custom_password']))
                return f'{self.title} (saved: {Fore.YELLOW}{masked_password}{Fore.RESET})'
            elif self.args_names == 'password' and self.value:
                masked_password = '*' * len(str(self.value))
                return f'{self.title} (saved: {Fore.YELLOW}{masked_password}{Fore.RESET})'
            else:
                return f'{self.title} (saved: {Fore.YELLOW}{self.args[self.args_names.replace("-", "_")]}{Fore.RESET})'
        elif self.action == 'bool_switch':
            if self.args[self.args_names.replace('-', '_')]:
                return f'{self.title} {Fore.GREEN}(enabled){Fore.RESET}'
            return f'{self.title} {Fore.RED}(disabled){Fore.RESET}'
        
    def run(self):
        if self.action == 'bool_switch':
            self.args[self.args_names.replace('-', '_')] = not self.args[self.args_names.replace('-', '_')]
            return True
        execution = True
        while True:
            clear_console()
            print(self.title+'\n')
            menu_items = []
            if self.choices != []:
                menu_items = self.choices
            else:
                menu_items = self.args_names
            if self.action != 'manual_input':
                for index in range(0, len(menu_items)):
                    menu_item = menu_items[index]
                    print(f'{index+1} - {menu_item}')
                print()
            try:
                if self.action == 'manual_input':
                    while True:
                        if self.data_range is not None:
                            print('Allowed values: '+str(self.data_range)+'\n')
                        
                        # Special handling for password input
                        if self.args_names in ['password', 'custom-password']:
                            print('Custom password requirements:')
                            print('- At least 10 characters long')
                            print('- 1 uppercase letter')
                            print('- 1 lowercase letter')
                            print('- 1 number\n')
                        
                        self.value = input('>>> ').strip()
                        
                        try:
                            self.value = self.data_type(self.value)
                            if self.data_range is not None:
                                if self.value not in self.data_range:
                                    raise
                            
                            # Custom validation function
                            if self.validation_func is not None and self.value:
                                is_valid, message = self.validation_func(self.value)
                                if not is_valid:
                                    clear_console()
                                    print(self.title+'\n')
                                    print(f'Invalid input: {message}\n')
                                    continue
                                else:
                                    print(f'\nInput is valid and will be saved!')
                            
                            # Special validation for password (backward compatibility)
                            if self.args_names in ['password', 'custom-password'] and self.value:
                                is_valid, message = validate_custom_password(self.value)
                                if not is_valid:
                                    clear_console()
                                    print(self.title+'\n')
                                    print(f'Invalid password: {message}\n')
                                    continue
                                else:
                                    print(f'\nPassword is valid and will be saved!')
                            
                            self.args[self.args_names.replace('-', '_')] = self.value # self.args_names is str
                            execution = False
                            break
                        except:
                            clear_console()
                            print(self.title+'\n')
                if not execution:
                    break
                index = int(input('>>> ').strip()) - 1
                self.value = menu_items[index]
                if index in range(0, len(menu_items)):
                    if self.action == 'store_true':
                        for args_name in self.args_names: # self.args_names is list
                            self.args[args_name.replace('-', '_')] = False
                        self.args[self.value.replace('-', '_')] = True # self.value == args_name
                    elif self.action == 'choice':
                        self.args[self.args_names.replace('-', '_')] = self.value # self.args_names is str
                    break
            except ValueError:
                pass

class ViewMenu(object):
    def __init__(self, title):
        self.title = title
        self.items = []
        self.execution = True

    def add_item(self, menu_action_object: MenuAction):
        self.items.append(menu_action_object)
    
    def view(self):
        self.execution = True
        while self.execution:
            clear_console()
            print(self.title+'\n')
            for item_index in range(0, len(self.items)):
                item = self.items[item_index]
                print(f'{item_index+1} - {item.render_title()}')
            print()
            try:
                selected_item_index = int(input('>>> ')) - 1
                if selected_item_index in range(0, len(self.items)):
                    self.items[selected_item_index].run()
            except ValueError:
                pass
    
    def close(self):
        self.execution = False