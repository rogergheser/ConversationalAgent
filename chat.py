import omegaconf
import logging
import os

from components import (
    PreNLU,
    NLU,
    DM,
    NLG
)

from components.stateTracker import *
from utils import *

class Chat():
    def __init__(self,
                 pre_nlu_cfg: dict, 
                 nlu_cfg: dict, 
                 dm_cfg: dict, 
                 nlg_cfg: dict, 
                 calendar_st: CalendarST,
                 cfg: dict):
        self.RUNNING = True
        self.nlu_cfg = nlu_cfg
        self.dm_cfg = dm_cfg
        self.nlg_cfg = nlg_cfg

        self.calendar_st = calendar_st
        self.appointment_st = AppointmentST()
        self.cancel_appointment_st = CancelAppointmentST()
        self.repeating_appointment_st = RepeatingAppointmentST()

        self.logger = logging.getLogger('Chat')
        logger_cfg(self.logger, debug_color="red", info_color="white")


        self.history = ConversationHistory()
        self.welcome_msg = cfg['CHAT']['welcome_msg']
        self.nlu = NLU(pre_nlu_cfg, nlu_cfg, self.history, self.logger)
        self.nlg = NLG(nlg_cfg, self.history, self.logger)
        self.dm = DM(dm_cfg, self.history, self.logger)

        if os.environ['USER'] == 'amir.gheser':
            self.model, self.tokenizer = load_model(nlu_cfg['model_name'], parallel=False, device='cuda', dtype='b16')
        
        self.run_chat()

    @classmethod
    def from_config(cls, config, state_tracker):
        return cls(
            config['PreNLU'],
            config['NLU'],
            config['DM'],
            config['NLG'],
            state_tracker,
            config
        )
    def process_intent(self, meaning_representation):
        # TODO Process meaning representation based on intent
        match meaning_representation['intent']:
            case 'set_appointment':
                self.appointment_st.update(meaning_representation)
                return self.dm(self.appointment_st)
            case 'create_repeating_appointment':
                self.repeating_appointment_st.update(meaning_representation)
                return self.dm(self.repeating_appointment_st)
            case 'cancel_appointment':
                # TODO Implement cancel appointment
                raise NotImplementedError
            case _:
                self.logger.error(f'Unknown intent: {meaning_representation["intent"]}')
                raise ValueError(f'Unknown intent: {meaning_representation["intent"]}')

    def run_chat(self):
        print(self.welcome_msg)
        while self.RUNNING:
            user_input = input('User: ')
            if user_input.lower() == 'exit':
                self.RUNNING = False
                break
            self.history.add(user_input, 'user', 'input')

            meaning_representation = self.nlu(user_input)
            next_best_action, argument = self.process_intent(meaning_representation)

            lexicalised_response = self.nlg(next_best_action)

            self.history.add(lexicalised_response, 'system', 'lexicalised_NBA')
            print(f'System: {lexicalised_response}')


if __name__ == '__main__':
    conf = omegaconf.OmegaConf.load('config.yaml')

    dialogue_st = CalendarST()
    
    chat = Chat.from_config(conf, dialogue_st)
    
    chat.run_chat()
    
    