import logging
import ollama
import os
import re

from utils import *
from typing import Union, Optional

logger = logging.getLogger(__name__)

class PreNLU():
    def __init__(self,
                 cfg: dict,
                 history: ConversationHistory,
                 logger: Any):
        self.cfg = cfg
        self.history = history
        self.logger = logger
        if os.environ['USER'] == 'amir.gheser':
            self.model, self.tokenizer = load_model(cfg['model_name'], parallel=False, device='cuda', dtype='b16')

    def __call__(self, prompt: str):
        intent_list = self.query_model(self.cfg['model_name'], self.cfg['system_prompt_file'], prompt)
        intent_list = re.search(r"\[.*?\]", intent_list).group(0)
        try:
            parsed_list = eval(intent_list)
        except:
            logger.debug('\033[91m' + 'Error in parsing the intent list. Please try again.\n\n'
                         + intent_list)
            raise ValueError('Error in parsing the intent list. Please try again.')

        return parsed_list

    def query_model(self, model_name: str, system: str, input_text: Union[str, bool]=False, max_seq_len: int=128):
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
            logger.debug(messages, extra={"color": "blue"})
            response = ollama.chat(model=model_name, messages=
                messages
            )
            return response['message']['content']
        else:
            raise ValueError('Unknown user environment. Please set the USER environment variable.')
        

class NLU():
    """
    Natural Language Understanding (NLU) component.
    """
    def __init__(self,
                 pre_nlu_cfg: dict, 
                 nlu_cfg: dict,
                 history: ConversationHistory,
                 logger: Optional[Any]=None):
        """
        :param pre_nlu_cfg: Configuration for the pre-NLU component.
        :param nlu_cfg: Configuration for the NLU component.
        :param history: Conversation history.
        :param logger: Logger object.

        --- Callable ---
        :param prompt: The user prompt.
        :return: The meaning representation of the user prompt.
        """
        self.logger = logger if logger else logging.getLogger('NLU')
        self.pre_nlu = PreNLU(pre_nlu_cfg, history, self.logger)
        self.nlu_cfg = nlu_cfg
        self.history = history
        if os.environ['USER'] == 'amir.gheser':
            self.model, self.tokenizer = load_model(nlu_cfg['model_name'], parallel=False, device='cuda', dtype='b16')

    @classmethod
    def from_cfg(cls, cfg, history):
        # get logger name from cfg
        raise NotImplementedError

    def __call__(self, prompt: str):
        """
        :param prompt: The user prompt.
        :return: The meaning representation of the user prompt.
        """
        chunks = self.pre_nlu(prompt)
        logger.debug(chunks)

        if len(chunks) == 1:
            return self.get_meaning_representation(chunks[0])
        else:
            # Assuming that the chunks are in the right priority order.
            logger.warning('\033[91m' + 'Not implemented yet.' + '\033[0;0m \n\t' + '\n\t'.join(chunks))
            raise NotImplementedError

    @log_call(logging.getLogger('NLU'))
    def get_meaning_representation(self, input_prompt: str):
        raw_meaning_rep = self.query_model(self.nlu_cfg['model_name'], self.nlu_cfg['system_prompt_file'], input_prompt)
        try:
            meaning_representation = parse_json(raw_meaning_rep)
        except:
            logger.debug('\033[91m' + 'Error in parsing the meaning representation. Please try again.\n\n'
                         + raw_meaning_rep)
            raise ValueError('Error in parsing the meaning representation. Please try again.')
        logger.info(meaning_representation)
        
        return meaning_representation
    
    
    def query_model(self, model_name: str, system: str, input_text: Union[str, bool]=False, max_seq_len: int=128):
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
            logger.debug(messages, extra={"color": "blue"})
            response = ollama.chat(model=model_name, messages=
                messages
            )
            return response['message']['content']
        else:
            raise ValueError('Unknown user environment. Please set the USER environment variable.')