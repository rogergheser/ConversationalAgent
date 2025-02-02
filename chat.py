import omegaconf
import logging
import os

from components import (
    NLU,
    DM,
    NLG,
    ApartmentManager
)
from components.apartmentTracker import *
from components.stateTracker import FallbackST
from utils import *

class Chat():
    def __init__(self,
                 pre_nlu_cfg: dict, 
                 nlu_cfg: dict, 
                 dm_cfg: dict, 
                 nlg_cfg: dict, 
                 cfg: dict):
        self.RUNNING = True
        self.nlu_cfg = nlu_cfg
        self.dm_cfg = dm_cfg
        self.nlg_cfg = nlg_cfg

        # self.request_explanation_st = RequestExplanationST() #! Not implemented

        self.logger = logging.getLogger('Chat')
        logger_cfg(self.logger, debug_color="red", info_color="white")

        self.history = ConversationHistory()
        self.welcome_msg = cfg['CHAT']['welcome_msg']
        self.fallback_msg = cfg['CHAT']['fallback_msg']
        self.nlu = NLU(pre_nlu_cfg, nlu_cfg, self.history, self.logger)
        self.nlg = NLG(nlg_cfg, self.history, self.logger)
        self.dm = DM(dm_cfg, self.history, self.logger)
        
        self.book_apartment_st = BookApartmentST()
        self.feedback_st = FeedbackST()
        self.list_apartments_st = ListApartmentsST()
        self.fallback_st = FallbackST()
        self.apartment_manager = ApartmentManager(
            'data/apartments.csv',
            self.history,
            self.book_apartment_st,
            self.feedback_st,
            self.list_apartments_st,
            self.fallback_st,
            self.logger
        )

        self.dm.update_possible_actions({
            'list_apartments': self.apartment_manager.list_apartments,
            'confirm_booking': self.apartment_manager.book_apartment,
            'feedback': self.apartment_manager.give_feedback,
            'contact_operator' : self.apartment_manager.contact_human,
            'fallback' : self.handle_fallback
        })

        if os.environ['USER'] == 'amir.gheser':
            self.model, self.tokenizer = load_model(nlu_cfg['model_name'], parallel=False, device='cuda', dtype='b16')
        
        self.history.add(self.welcome_msg, 'system', 'welcome_msg')

        self.run_chat()

    @classmethod
    def from_config(cls, config):
        return cls(
            config['PreNLU'],
            config['NLU'],
            config['DM'],
            config['NLG'],
            config
        )
    
    def handle_fallback(self):
        self.logger.error('Fallback action triggered.')
        self.logger.error('Not implemented.')
        self.history.add(self.fallback_msg, 'system', 'fallback')
        return 'repeat_fallback_msg'

    def process_intent(self, meaning_representation):
        match meaning_representation['intent']:
            case 'list_apartments':
                self.list_apartments_st.update(meaning_representation)
                return self.dm(self.list_apartments_st)
            case 'book_apartment':
                self.book_apartment_st.update(meaning_representation)
                return self.dm(self.book_apartment_st)
            case 'feedback':
                self.feedback_st.update(meaning_representation)
                return self.dm(self.feedback_st)
            case 'contact_operator':
                return self.dm('contact_operator')
            case 'fallback':
                self.fallback_st.update(meaning_representation)
                return self.dm(self.fallback_st)
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
            try:
                next_best_action = self.process_intent(meaning_representation)
            except:
                self.logger.error('Error in processing the intent. Meaning representation: \n' + str(meaning_representation))
                self.logger.error('Error handling not implemented yet.\nTODO: Implement error handling for intent processing.')


            lexicalised_response = self.nlg(next_best_action)

            self.history.add(lexicalised_response, 'system', 'lexicalised_NBA')
            print(f'System: {lexicalised_response}')


if __name__ == '__main__':
    conf = omegaconf.OmegaConf.load('config.yaml')
    
    chat = Chat.from_config(conf)    
    