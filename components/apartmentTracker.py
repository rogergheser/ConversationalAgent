import logging
import textwrap
import json
from .stateTracker import DialogueST

class BookApartmentST(DialogueST):
    def __init__(self):
        self.fields = [
            "name",
            "surname",
            "document_type",
            "document_number",
            "start_date",
            "end_date",
            "guest_number",
            "apartment_number",
        ]
        self.apartment_booking = { field: None for field in self.fields }

    def update(self, parsed_input):
        if 'intent' in parsed_input:
            if 'book' not in parsed_input['intent'] and 'apartment' not in parsed_input['intent']:
                logging.warning(f'Intent is not book apartment. {parsed_input["intent"]}')
                return
        if 'slots' not in parsed_input:
            logging.warning(f'No slots found in parsed input.\nParsed input:\n{parsed_input}')
            return

        parsed_input = parsed_input['slots']
        for field in parsed_input:
            if parsed_input[field] == 'null' or parsed_input[field] is None:
                continue
            if field in self.apartment_booking:
                self.apartment_booking[field] = parsed_input[field]
            else:
                logging.warning(f'Field {field} not found in order fields.')

    def __str__(self):
        return ', '.join([f'{key}: {value}' for key, value in self.apartment_booking.items()])

    def to_dict(self):
        return json.dumps({
            "intent": "book_apartment",
            "slots" : self.apartment_booking
        })

    def is_valid(self):
        for field in self.apartment_booking:
            if self.apartment_booking[field] is None:
                return False
        return True
    
    def get_booking_details(self):
        return textwrap.dedent("""
            Booking details:
            
            Apartment number: {apartment_number}
            Full Name: {name} {surname}
            Document type: {document_type}
            Document number: {document_number}
            Number of guests: {guest_number}
            From: {start_date}
            To: {end_date}
        """).format(**self.apartment_booking)
    
    def get_booking_msg(self):
        return "Please confirm the booking details.\n" + self.get_booking_details()

class FeedbackST(DialogueST):
    def __init__(self):
        self.fields = [
            "type",
            "feedback"
        ]
        self.feedback = { field: None for field in self.fields }

    def update(self, parsed_input):
        if 'intent' in parsed_input:
            if 'appointment' not in parsed_input['intent']:
                logging.warning('Intent is not burger_ordering.')
                return
        if 'slots' not in parsed_input:
            logging.warning('No slots found in parsed input.')
            return

        parsed_input = parsed_input['slots']
        for field in parsed_input:
            if parsed_input[field] == 'null':
                continue
            if field in self.feedback:
                self.feedback[field] = parsed_input[field]
            else:
                logging.warning(f'Field {field} not found in order fields.')

    def __str__(self):
        return ', '.join([f'{key}: {value}' for key, value in self.feedback.items()])
    
    def to_dict(self):
        return json.dumps({
            "intent": "feedback",
            "slots" : self.feedback
        })
    
    def is_valid(self):
        for field in self.feedback:
            if self.feedback[field] is None:
                return False
        return True
    
class RequestExplanationST(DialogueST):
    def __init__(self):
        self.fields = [
            "issue",
        ]
        self.feedback = { field: None for field in self.fields }

        raise NotImplementedError

    def update(self, parsed_input):
        if 'intent' in parsed_input:
            if 'appointment' not in parsed_input['intent']:
                logging.warning('Intent is not burger_ordering.')
                return
        if 'slots' not in parsed_input:
            logging.warning('No slots found in parsed input.')
            return

        parsed_input = parsed_input['slots']
        for field in parsed_input:
            if parsed_input[field] == 'null':
                continue
            if field in self.feedback:
                self.feedback[field] = parsed_input[field]
            else:
                logging.warning(f'Field {field} not found in order fields.')

    def __str__(self):
        return ', '.join([f'{key}: {value}' for key, value in self.feedback.items()])

    def to_dict(self):
        return json.dumps({
            "intent": "feedback",
            "slots" : self.feedback
        })

    def is_valid(self):
        for field in self.feedback:
            if self.feedback[field] is None:
                return False
        return True
    
class ListApartmentsST(DialogueST):
    def __init__(self):
        self.fields = []

        self.list_apartments = { field: None for field in self.fields }

    def update(self, parsed_input):
        if 'intent' in parsed_input:
            if 'list' not in parsed_input['intent'] and 'apartment' not in parsed_input['intent']:
                logging.warning('Intent is not list apartments.')
                return
        if 'slots' not in parsed_input:
            logging.warning('No slots found in parsed input.')
            return

    def __str__(self):
        return ', '.join([f'{key}: {value}' for key, value in self.apartment_booking.items()])
    
    def to_dict(self):
        return json.dumps({
            "intent": "list_apartments",
            "slots" : {}})
    
    def is_valid(self):
        for field in self.list_apartments:
            if self.list_apartments[field] is None:
                return False
        return True
