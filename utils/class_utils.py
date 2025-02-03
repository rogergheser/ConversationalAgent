import os
import functools

from typing import Any

class ConversationHistory():
    def __init__(self):
        self.msg_list = []
        self.actions = []
        self.roles = []

    def update_history_decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            path = os.path.join('history.log')
            with open(path, 'w+') as f:
                f.write(self.action_history_str() + '\n')
                f.write("-"*50)
                f.write('\n')
                f.write('\n'.join([f"{role}: {msg}" for msg, role in zip(self.get_history(), self.roles)]))
            return result
        return wrapper

    @update_history_decorator
    def add(self, msg, role, action):
        self.roles.append(role)
        self.msg_list.append(msg)
        self.actions.append(action)

    def clear(self):
        self.msg_list = []
        self.actions = []
    
    def get_history(self, roles=False):
        return self.msg_list
    
    def action_history_str(self):
        return ', \n'.join(self.actions)

    def to_msg_history(self, hist_len=5)->list[dict]:
        history = [{'role': role, 'content': msg} for role, msg in zip(self.roles, self.msg_list)]
        if len(history) > hist_len:
            return history[-hist_len:]
        return history