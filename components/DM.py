import logging
import ollama
import os

from .stateTracker import DialogueST
from utils import (
    ConversationHistory,
    extract_action_and_arguments,
    generate,
    load_model,
)
from typing import Any, Optional

class DM:
    def __init__(self,
                 dm_cfg: dict,
                 history: ConversationHistory,
                 logger: Optional[Any]=None):
        self.dm_cfg = dm_cfg
        self.history = history
        self.logger = logger if logger else logging.getLogger('DM')
        self.special_actions = {} # key: fun, args, kwargs
        if os.environ['USER'] == 'amir.gheser':
            self.model, self.tokenizer = load_model(dm_cfg['model_name'], parallel=False, device='cuda', dtype='b16')

    @classmethod
    def from_cfg(cls, cfg, history):
        # get logger name from cfg
        raise NotImplementedError
    
    def update_possible_actions(self, new_special_actions: dict):
        self.special_actions.update(new_special_actions)

    def __call__(self, state_tracker: DialogueST):
        nba, argument = self.get_nba(state_tracker)
        
        return self.nba_handler(nba, argument)

    def get_nba(self, state_tracker: DialogueST):
        """
        Get the next best action to perform based on the meaning representation.
        """
        return self.query_dialogue_manager(state_tracker)
    
    def query_dialogue_manager(self, state_tracker: DialogueST):
        """
        Query the dialogue manager model to get the next best action to perform.
        """
        meaning_representation = state_tracker.to_dict()
        raw_action = self.query_model(self.dm_cfg['model_name'], self.dm_cfg['system_prompt_file'], str(meaning_representation))
        # action = parse_json(raw_action) # TODO what to parse? Do we need to parse?
        # Define a format for asking info
        self.logger.debug(raw_action)
        try:
            action, argument = extract_action_and_arguments(raw_action)
        except:
            self.logger.debug('\033[91m' + 'Error in parsing the action. Please try again.\n\n'
                         + raw_action)
            return
        
        return action, argument

    def nba_handler(self, action, argument)->str:
        match action:
            case 'ask_info':
                return f'ask_info({argument})'
            case 'request_info':
                return f'ask_info({argument})'
            case 'confirm_order':
                fun, args, kwargs = self.special_actions['confirm_order']
                return fun(*args, **kwargs)
            case 'confirmation':
                fun, args, kwargs = self.special_actions['confirm_order']
                return fun(*args, **kwargs)
            case _:
                if action in self.special_actions:
                    fun, args, kwargs = self.special_actions[action]
                    return fun(*args, **kwargs)
                else:
                    raise ValueError(f'Unknown action: {action}')
            
    def query_model(self, model_name, system, input_text=False, max_seq_len=128):
        system_prompt = open(system, 'r').read()
        user_env = os.getenv('USER')
        if user_env == 'amir.gheser':
            hist = self.history.to_msg_history()
            hist = hist[-5:] if len(hist > 5) else hist
            history = "\n".join([f"{k['role']}: {k['content']}"  for k in hist])
            input = system_prompt + '\n' + history + '\n' + input_text

            input = self.tokenizer(input, return_tensors="pt").to(self.model.device)
            response = generate(self.model, input, self.tokenizer, max_new_tokens=max_seq_len)

            return response
        elif user_env == 'amirgheser':
            # we are on the local machine
            messages = [{
                            'role':'system',
                            'content': system_prompt
                            }] + self.history.to_msg_history()
                        # + [{
                        #     'role':'system',
                        #     'content': system_prompt
                        #     }]
            if input_text:
                messages.append({
                    'role': 'user',
                    'content': input_text
                })
            self.logger.debug(messages, extra={"color": "blue"})
            response = ollama.chat(model=model_name, messages=
                messages
            )
            return response['message']['content']
        else:
            raise ValueError('Unknown user environment. Please set the USER environment variable.')