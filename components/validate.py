import logging
from .apartmentTracker import BookApartmentST, FeedbackST, ListApartmentsST, SeeApartmentsST

class Validator():
    def __init__(self):
        self.book_apartment_st = BookApartmentST()
        self.feedback_st = FeedbackST()
        self.list_apartments_st = ListApartmentsST()
        self.see_apartments_st = SeeApartmentsST()

        self.str2cls = {
            'book_apartment': self.book_apartment_st,
            'give_feedback': self.feedback_st,
            'list_apartments': self.list_apartments_st,
            'see_apartments' : self.see_apartments_st,
            'contact_operator': None,
            'fallback': None
        }

    def post_process(self, meaning_representation):
        if 'intent' not in meaning_representation or 'slots' not in meaning_representation:
            return False
        intent, slots = meaning_representation['intent'], meaning_representation['slots']
        st = self.str2cls[intent]
        meaning_representation_copy = meaning_representation.copy()
        if st is not None:
            for slot in slots:
                if slot not in st.fields:
                    del meaning_representation_copy['slots'][slot]
        return meaning_representation_copy

    def validate(self, meaning_representation):
        if 'intent' not in meaning_representation or 'slots' not in meaning_representation:
            return False
        intent, slots = meaning_representation['intent'], meaning_representation['slots']
        st = self.str2cls[intent]
        if st is not None:
            for slot in slots:
                if slot not in st.fields:
                    logging.error(f'Invalid slot {slot} for intent {intent}.')
                    return False
        
        return True