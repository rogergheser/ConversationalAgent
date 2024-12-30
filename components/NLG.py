import os
import ollama
import logging

from typing import Optional, Any
from utils import (
    ConversationHistory,
    generate,
    log_call,
    load_model
)

class NLG:
    def __init__(self, nlg_cfg: dict, history: ConversationHistory, logger: Optional[Any]=None):
        self.nlg_cfg = nlg_cfg
        self.history = history
        self.logger = logger if logger else logging.getLogger('NLG')
        if os.environ['USER'] == 'amir.gheser':
            self.model, self.tokenizer = load_model(nlg_cfg['model_name'], parallel=False, device='cuda', dtype='b16')

    @classmethod
    def from_cfg(cls, cfg, history):
        # get logger name from cfg
        # TODO: Implement this method
        raise NotImplementedError

    def __call__(self, nba: str):
        return self.lexicalise(nba)

    @log_call(logger=logging.getLogger('NLG'))
    def lexicalise(self, action):
        self.logger.debug('lexicalise: ' + action)
        lexicalised_text = self.query_model(self.nlg_cfg['model_name'], self.nlg_cfg['system_prompt_file'], input_text=action)

        self.history.add(lexicalised_text, 'system', action)

        return lexicalised_text
    
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
