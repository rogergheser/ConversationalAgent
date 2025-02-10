import omegaconf
import logging
import os
import traceback
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
        self.dm = DM(dm_cfg, self.history, self.logger)
        self.nlg = NLG(nlg_cfg, self.history, self.logger)
        
        self.book_apartment_st = BookApartmentST()
        self.feedback_st = FeedbackST()
        self.list_apartments_st = ListApartmentsST()
        self.fallback_st = FallbackST()
        self.see_apartments_st = SeeApartmentsST()
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
            'show_apartments' : self.apartment_manager.show_apartments,
            'feedback': self.apartment_manager.give_feedback,
            'contact_operator' : self.contact_human,
            'fallback' : self.handle_fallback,
            'pass' : lambda: 'ask_clarification(user_intent)'
        })

        if os.environ['USER'] == 'amir.gheser':
            self.model, self.tokenizer = load_model(nlu_cfg['model_name'], parallel=False, device='cuda', dtype='b16')
        
        self.history.add(self.welcome_msg, 'assistant', 'welcome_msg')

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
        self.history.add(self.fallback_msg, 'tool', 'fallback')
        self.RUNNING = False
        return 'repeat_fallback_msg()'

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
                self.RUNNING = False
                return self.dm('contact_operator')
            case 'fallback':
                self.fallback_st.update(meaning_representation)
                return self.dm(self.fallback_st)
            case 'see_apartments':
                self.see_apartments_st.update(meaning_representation)
                return self.dm(self.see_apartments_st)
            case _:
                self.logger.error(f'Unknown intent: {meaning_representation["intent"]}')
                raise ValueError(f'Unknown intent: {meaning_representation["intent"]}')

    def contact_human(self):
        self.RUNNING = False
        return self.apartment_manager.contact_human()

    def info_ack(self, meaning_representations:list[str], msg)->str:
        """
        Takes the last parsed information and creates a NBA confirmation message.
        """
        ack_slots = []
        for meaning_representation in meaning_representations:
            if "slots" in meaning_representation:
                slots = meaning_representation['slots']
            for slot in slots:
                if slots[slot] is not None:
                    ack_slots.append(slot)
        
        return json.dumps(
            {
                "intent" : "send_ack",
                "slots" : {
                    "fields" : ack_slots,
                    "message" : msg
                }
            }
        )

    def run_chat(self):
        print(f'\033[92m{self.welcome_msg}\033[0m')

        while self.RUNNING:
            user_input = input('User: ')
            if user_input.lower() == 'exit':
                self.RUNNING = False
                break
            meaning_representations = self.nlu(user_input)
            self.history.add(user_input, 'user', 'input') # NLU feeds user input to the LLM internally

            NBAs = []
            NBAs.append(self.info_ack(meaning_representations, user_input))
            for meaning_representation in meaning_representations:
                try:
                    NBAs.append(self.process_intent(meaning_representation))
                except Exception as e:
                    self.logger.error('Exception: \n' + traceback.format_exc() + '\n' + str(e))
                    self.logger.error('\nError in processing the intent. Meaning representation: \n' + str(meaning_representation))
                    self.logger.error('Error handling not implemented yet.\nTODO: Implement error handling for intent processing.')

            lexicalised_response = self.nlg(NBAs)

            if self.history.actions[-1] == 'STOP' and self.history.roles[-1] == 'tool':
                self.RUNNING = False

            self.history.add(lexicalised_response, 'assistant', 'lexicalised_NBA')
            print(f'\033[92mAssistant: {lexicalised_response}\033[0m')


if __name__ == '__main__':
    conf = omegaconf.OmegaConf.load('config.yaml')
    logging.disable(logging.CRITICAL)
    file_handler = logging.FileHandler('chat.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    
    chat = Chat.from_config(conf)    