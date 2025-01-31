import logging
import pandas as pd

from .service import Service
from .apartmentTracker import  BookApartmentST, FeedbackST, ListApartmentsST
from .stateTracker import FallbackST
from utils import ConversationHistory
from PIL import Image, ImageDraw, ImageFont
# Configure this logger to connect to a database and handle user requests

class ApartmentManager():
    def __init__(self,
                 csv_path:str,
                 history: ConversationHistory,
                 book_apartment_st: BookApartmentST,
                 feedback_st: FeedbackST,
                 list_apartments_st: ListApartmentsST,
                 fallback_st: FallbackST,
                 logger: logging.Logger):
        
        self.csv_path = csv_path
        self.history = history
        self.book_apartment_st = book_apartment_st
        self.feedback_st = feedback_st
        self.list_apartments_st = list_apartments_st
        self.fallback_st = fallback_st
        self.service = Service()
        self.logger = logger
        self.apartments = []
        self.load_apartments()

    def load_apartments(self)->str:
        self.apartments = pd.read_csv(self.csv_path, sep=';')

        self.apartments['isFree'] = self.apartments['isFree'].apply(lambda x: True if x == 1 else False)

    def get_apartments(self, filters)->str:
        filtered_apartments = self.apartments
        for key, value in filters:
            filtered_apartments = filtered_apartments[filtered_apartments[key] == value]
        
        return filtered_apartments

    def list_apartments(self)->str:
        filters = [('isFree', True)] # To make possible to filter the apartments searched
        apartments = self.get_apartments(filters)
        
        apartments = apartments.to_dict(orient='records')
        
        images = []
        msg = ''
        for apartment in apartments:
            msg += ''.join(['Apartment[', str(apartment['id']),
                  '] -- ', apartment['name'],
                  '\nMax guests: ', str(apartment['maxPeople']),
                #  + '\nPrice: ' + str(apartment['price'])
                # + '\nDescription: ' + apartment['description'] 
                  '\nPreview: - check image for preview - \n'])
            
            images.append(get_image(apartment['path'], apartment['id'], apartment['name']))
        
        self.history.add(msg, 'system', 'list_apartments')

        return 'list_apartments'
    
    def book_apartment(self)->str:
        # apartment_dict = self.book_apartment_st.apartment_booking
        if self.book_apartment_st.is_valid():
            booking_msg = self.book_apartment_st.get_booking_msg()
            self.history.add(booking_msg, 
                             'system', 
                             'confirm_booking')
            self.service.book_apartment(self.book_apartment_st.to_dict()) #! Dummy function
            return 'confirm_booking()'
        else:
            self.logger.debug('[ERROR CAUGHT] Missing information to book an apartment.')
            self.history.add('Please provide all the necessary information to book an apartment', 
                             'system', 
                             'error_handling')
            
            missing_field = None
            for field in self.book_apartment_st.apartment_booking:
                if self.book_apartment_st.apartment_booking[field] is None:
                    missing_field = field
                    break

            if field is not None:
                self.history.add('There must have been an error in the pipeline.'
                                 'I must ask the user to provide a missing field as the booking request is not fully filled.',
                                 'system', 'error_handling')
                return f'ask_info({field})'
            else:
                raise ValueError("Non-empty dictionary signaled as empty")

    def give_feedback(self)->str:
        pass

    def contact_human(self)->str:
        self.history.add('A human operator has been notified and will respond as soon as he\'s available', 'system', 'contact_operator')
        return 'contact_operator'

def show_image(path, id, name):
    img = Image.open(path)
    img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    # draw.text((x, y),"Sample Text",(r,g,b))
    font = ImageFont.load_default()
    draw.text((0, 0),f'Apartment {id} preview -- {name}',(255,255,255), font=font)
    
    # Show the image
    img.show(title=f'Apartment {id} preview -- {name}')

def get_image(path, id, name):
    img = Image.open(path)
    img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    # draw.text((x, y),"Sample Text",(r,g,b))
    font = ImageFont.load_default()
    draw.text((0, 0),f'Apartment {id} preview -- {name}',(255,255,255), font=font)
    
    # Show the image
    return img

def concat_images(images):
    pass

if __name__ == '__main__':
    am = ApartmentManager('data/apartments.csv')
    am.list_apartments()
