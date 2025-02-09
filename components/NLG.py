import os
import ollama
import logging
import json
from typing import Optional, Any
from utils import (
    ConversationHistory,
    generate,
    log_call,
    load_model
)

class NLG:
    def __init__(self, 
                 nlg_cfg: dict, 
                 history: ConversationHistory, 
                 cfg: Any,
                 logger: Optional[Any] = None):
        self.nlg_cfg = nlg_cfg
        self.history = history
        self.cfg = cfg
        self.logger = logger if logger else logging.getLogger('NLG')
        if os.environ['USER'] == 'amir.gheser':
            self.model, self.tokenizer = load_model(nlg_cfg['model_name'], parallel=False, device='cuda', dtype='b16')

    @classmethod
    def from_cfg(cls, cfg, history):
        return cls(cfg['NLG'], history, cfg, cfg['logger'])

    def __call__(self, nba: str):
        return self.lexicalise(nba)

    @log_call(logger=logging.getLogger('chat_logger'))
    def lexicalise(self, actions: list[str]):
        input_text = '```\n' + self.__make_nba_obj(actions) + '\n```'
        lexicalised_text = self.query_model(self.nlg_cfg['model_name'], self.nlg_cfg['system_prompt_file'], input_text=input_text)

        return lexicalised_text
    
    def __make_nba_obj(self, functions: list[str]):
        """
        Make the NBA object from the list of actions.
        """
        ret = {}
        for function in functions:
            try:
                action, args = function.split('(', 1)
                args = args[:-1].split(', ')
            except:
                action = function
                args = []
            
            if action in ret:
                ret[action]['args'].append(args)
            else:
                ret[action] = {
                    'action': action,
                    'args': args if args else []
                }

        return json.dumps(list(ret.values()))

    def query_model(self, model_name, system, input_text=False, max_seq_len=128):
        system_prompt = open(system, 'r').read()
        user_env = os.getenv('USER')
        if user_env == 'amir.gheser':
            hist = self.history.to_msg_history(hist_len=3)
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
                            }] + self.history.to_msg_history(hist_len=0)
            if input_text:
                messages.append({
                    'role': 'user',
                    'content': input_text
                })
            self.logger.debug(messages, extra={"color": "blue"})
            response = ollama.chat(model=model_name, messages=
                messages
            )
            self.logger.info(f"[NLG]: {response.total_duration / 1e9:.2f} seconds.")
            self.logger.info(f"[NLG]: {response.eval_count / response.total_duration * 1e9:.2f} tokens/s.")
            return response['message']['content']
        else:
            raise ValueError('Unknown user environment. Please set the USER environment variable.')
