import logging
import ollama
import os
import re
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import *
from typing import Union, Optional
from .validate import Validator

logger = logging.getLogger(__name__)

class PreNLU():
    def __init__(self,
                 cfg: dict,
                 history: ConversationHistory,
                 logger: logging.Logger):
        self.cfg = cfg
        self.history = history
        self.logger = logger
        if os.environ['USER'] == 'amir.gheser':
            self.model, self.tokenizer = load_model(cfg['model_name'], parallel=False, device='cuda', dtype='b16')

    def __call__(self, prompt: str, iteration: int=0):
        if iteration > 5:
            raise "Too many iterations in querying the PreNLU."
        chunk_list = self.query_model(self.cfg['model_name'], self.cfg['system_prompt_file'], prompt)
        try:
            chunk_list = parse_json(chunk_list, with_list=True)
            
            if 'chunk' in chunk_list and 'intent' in chunk_list \
                    and isinstance(chunk_list, dict):
                chunk_list = [chunk_list]
            
            if len(chunk_list) > 1:
                self.logger.debug(chunk_list)
                chunk_dict = self.post_process(chunk_list)
                
            
            chunk_list = [val["chunk"] for val in chunk_list]
        except Exception as e:
            return self.__call__(prompt, iteration=iteration + 1)

        return chunk_list

    def post_process(self, chunk_list)->dict:
        """
        Post-process the chunks to fix errors and assign correct priority
        """
        # print(chunk_list)
        ret_chunk_dict = {}
        # Group chunks based on intent

        for val in chunk_list:
            intent, chunk = val['intent'], val['chunk']
            if intent in ret_chunk_dict:
                ret_chunk_dict[intent] += ' ' + chunk
            else:
                ret_chunk_dict[intent] = chunk

        if len(ret_chunk_dict) < len(chunk_list):
            self.logger.error('\033[91m' + '[HANDLED ERROR]' + '\033[0;0m' + 'Detected and merged chunks.')
        
        # print(ret_chunk_dict)
        return ret_chunk_dict

    def query_model(self, model_name: str, system: str, input_text: Union[str, bool]=False, max_seq_len: int=128):
        system_prompt = open(system, 'r').read()
        user_env = os.getenv('USER')
        if user_env == 'amir.gheser':
            hist = self.history.to_msg_history()
            hist = hist[-2:] if len(hist > 2) else hist
            history = "\n".join([f"{k['role']}: {k['content']}"  for k in hist])
            input = system_prompt + '\n' + history + '\n' + input_text
            # input = system_prompt + '\nUser:\n' + input_text

            input = self.tokenizer(input, return_tensors="pt").to(self.model.device)
            response = generate(self.model, input, self.tokenizer, max_new_tokens=max_seq_len)

            return response
        elif user_env == 'amirgheser':
            # we are on the local machine
            messages = [{
                            'role':'system',
                            'content': system_prompt
                            }] + self.history.to_msg_history(hist_len=2)
            if input_text:
                messages.append({
                    'role': 'user',
                    'content': input_text
                })
            logger.debug(messages, extra={"color": "blue"})
            response = ollama.chat(model=model_name, messages=
                messages
            )
            self.logger.info(f"[PreNLU]: {response.total_duration / 1e9:.2f} seconds.")
            self.logger.info(f"[PreNLU]: {response.eval_count / response.total_duration * 1e9:.2f} tokens/s.")
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
        self.validator = Validator()

        if os.environ['USER'] == 'amir.gheser':
            self.model, self.tokenizer = load_model(nlu_cfg['model_name'], parallel=False, device='cuda', dtype='b16')

    @classmethod
    def from_cfg(cls, cfg, history):
        return cls(
            cfg['PreNLU'],
            cfg['NLU'],
            history
    )

    def __call__(self, prompt: str):
        """
        :param prompt: The user prompt.
        :return: The meaning representation of the user prompt.
        """
        chunks = self.pre_nlu(prompt)
        logger.debug(chunks)

        if len(chunks) == 1:
            return [self.get_meaning_representation(chunks[0])]
        elif chunks[0] == chunks[1]:
            return [self.get_meaning_representation(chunks[0])]
        else:
            # Assuming that the chunks are in the right priority order.
            meaning_representations = []
            for chunk in chunks:
                meaning_representations.append(self.get_meaning_representation(chunk))
            
            meaning_representations = self.post_process(meaning_representations)

            return meaning_representations

    def post_process(self, meaning_representations):
        self.logger.debug("NLU PostProcessing not implemented yet.")
        merged_representations = {}
        for rep in meaning_representations:
            intent = rep['intent']
            if intent in merged_representations:
                # Merge the slots if the intent already exists
                for slot, value in rep['slots'].items():
                    if slot in merged_representations[intent]['slots']:
                        if merged_representations[intent]['slots'][slot] is None:
                            merged_representations[intent]['slots'][slot] = value
                    else:
                        merged_representations[intent]['slots'][slot] = value
            else:
                merged_representations[intent] = rep
        
        return list(merged_representations.values())

    @log_call(logging.getLogger('NLU'))
    def get_meaning_representation(self, input_prompt: str, iteration: int=0):
        if iteration > 5:
            raise "Too many iterations in querying the NLU."
        raw_meaning_rep = self.query_model(self.nlu_cfg['model_name'], self.nlu_cfg['system_prompt_file'], input_prompt, iteration=iteration)
        try:
            meaning_representation = parse_json(raw_meaning_rep)
        except:
            logger.debug('\033[91m' + 'Error in parsing the meaning representation. Please try again.\n\n'
                         + raw_meaning_rep)
            logger.debug("Error parsing the output. Reprompting.")
            return self.get_meaning_representation(input_prompt, iteration=iteration+1)
        
        logger.info(meaning_representation)
        
        meaning_representation = self.validator.post_process(meaning_representation)
        if not self.validator.validate(meaning_representation):
            self.logger.error(f"Meaning representation is not valid. Repeating!\n{meaning_representation}")
            return self.get_meaning_representation(input_prompt, iteration=iteration+1)

        return meaning_representation        

    def query_model(self, model_name: str, system: str, input_text: Union[str, bool]=False, max_seq_len: int=128, iteration: int=0):
        system_prompt = "#NOTE: Today is the {}\n".format(datetime.today()) + open(system, 'r').read()
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
                            }] + self.history.to_msg_history(hist_len=3)
            if iteration > 0:
                messages.append({
                    'role': 'tool',
                    'content': "Do not answer the user. Your role is to extract the intent and slots from the input message."
                })
            if input_text:
                messages.append({
                    'role': 'user',
                    'content': input_text
                })
            logger.debug(messages, extra={"color": "blue"})
            response = ollama.chat(model=model_name, messages=
                messages
            )
            self.logger.info(f"[NLU]: {response.total_duration / 1e9:.2f} seconds.")
            self.logger.info(f"[NLU]: {response.eval_count / response.total_duration * 1e9:.2f} tokens/s.")
            return response['message']['content']
        else:
            raise ValueError('Unknown user environment. Please set the USER environment variable.')