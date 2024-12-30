import logging

from typing import Optional, Union, Any
from abc import ABC, abstractmethod


class Event():
    # TODO [FINISH]
    def __init__(self, cfg: Any, appointmentST):
        fields = appointmentST.appointment
        event = {
        'summary': fields['appointment_name'],
        'location': fields['location'],
        'description': fields['notes'],
        'start': {
            'dateTime': '2024-01-01T10:00:00-05:00',  # Example: January 1, 2024, at 10:00 AM EST
            'timeZone': cfg['timeZone'],
        },
        'end': {
            'dateTime': '2024-01-01T11:00:00-05:00',  # Ends at 11:00 AM EST
            'timeZone': cfg['timeZone'],
        },
        'attendees': [
            {'email': attendee} for attendee in fields['invitees']
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},  # 24 hours before
                {'method': 'popup', 'minutes': 10},  # 10 minutes before
            ],
        },
    }
        self.event = event
        self.cfg = cfg
    
    @staticmethod
    def create(cfg: Any, appointmentST):
        fields = appointmentST.appointment
        event = {
        'summary': fields['appointment_name'],
        'location': fields['location'],
        'description': fields['notes'],
        'start': {
            'dateTime': '2024-01-01T10:00:00-05:00',  # Example: January 1, 2024, at 10:00 AM EST
            'timeZone': cfg['timeZone'],
        },
        'end': {
            'dateTime': '2024-01-01T11:00:00-05:00',  # Ends at 11:00 AM EST
            'timeZone': cfg['timeZone'],
        },
        'attendees': [
            {'email': attendee} for attendee in fields['invitees']
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},  # 24 hours before
                {'method': 'popup', 'minutes': 10},  # 10 minutes before
                ],
            },
        }
        return event

class DialogueST(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def update(self, parsed_input):
        pass

    @abstractmethod
    def is_valid(self):
        pass

    @abstractmethod
    def to_dict(self):
        pass

    @abstractmethod
    def __str__(self):
        pass

class BurgerST(DialogueST):
    def __init__(self):
        fields = [
            'patty_count',
            'cheese_count',
            'bacon_count',
            'tomato',
            'onions',
            'mayo',
            'ketchup',
            'cooking'
            ]
        self.order = {field : None for field in fields}
        self.sentiment = None

    def update(self, parsed_input: dict):
        """
        Updates the dialogue state for the slots from the parsed input to the order state tracker.
        :param parsed_input: dict, parsed slots dictionary from the user.
        """
        if 'intent' in parsed_input:
            if parsed_input['intent'] != 'burger_ordering':
                logging.warning('Intent is not burger_ordering.')
                return
        if 'sentiment' in parsed_input:
            self.sentiment = parsed_input['sentiment']
        
        if 'slots' not in parsed_input:
            logging.warning('No slots found in parsed input.\n' + str(parsed_input))
            return
        
        parsed_input = parsed_input['slots']
        for field in parsed_input:
            if parsed_input[field] == 'null':
                continue
            if field in self.order:
                self.order[field] = parsed_input[field]
            else:
                logging.warning(f'Field {field} not found in order fields.')

    def __str__(self):
        return ', '.join([f'{key}: {value}' for key, value in self.order.items()])

    def to_dict(self):
        return {"intent": "burger_ordering",
                "slots" : self.order,
                "sentiment" : self.sentiment}

    def is_valid(self):
        for field in self.order:
            if self.order[field] is None:
                return False
        return True
    
      
class AppointmentST(DialogueST):
    def __init__(self):
        """
        This is a set only AppointmentST.
        """
        fields = [
            "appointment_name",
            "location",
            "link",
            "date",
            "alerts",
            "travel_time",
            "invitees",
            "notes",
        ]
        self.appointment = {field: None for field in fields}

    def update(self, parsed_input: dict):
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
            if field in self.appointment:
                self.appointment[field] = parsed_input[field]
            else:
                logging.warning(f'Field {field} not found in order fields.')

    def __str__(self):
        return ', '.join([f'{key}: {value}' for key, value in self.appointment.items()])

    def to_dict(self):
        return {"intent": "set_appointment",
                "slots" : self.appointment}

    def is_valid(self):
        for field in self.appointment:
            if self.appointment[field] is None:
                return False
        return True
    
    def createEvent(self)->Event:
        return Event.create(self.appointment)
    

class CancelAppointmentST(DialogueST):
    """
    This is a cancel only AppointmentST.
    """
    def __init__(self):
        fields = [
            "appointment_name",
            "date",
            "contact_type",
            "reschedule",
            "custom_message"
        ]
        self.appointment = {field: None for field in fields}

    def update(self, parsed_input: dict):
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
            if field in self.appointment:
                self.appointment[field] = parsed_input[field]
            else:
                logging.warning(f'Field {field} not found in order fields.')

    def __str__(self):
        return ', '.join([f'{key}: {value}' for key, value in self.appointment.items()])

    def to_dict(self):
        return {"intent": "set_appointment", # Todo keep set/modify/cancel together?
                "slots" : self.appointment}

    def is_valid(self):
        for field in self.appointment:
            if self.appointment[field] is None:
                return False
        return True

class RepeatingAppointmentST(AppointmentST):
    def __init__(self,
                 frequency : Optional[str] = 'weekly',
                 end_date : Optional[str] = None):
        super().__init__()
        self.frequencies = ['yearly', 'monthly', 'weekly', 'daily', 'workdays', 'weekends']
        end_date = None
        self.appointment['frequency'] = frequency
        self.appointment['end_date'] = end_date

    def update(self, parsed_input: dict):
        super().update(parsed_input)

    def to_dict(self):
        return {"intent": "set_repeating_appointment",
                "slots" : self.appointment}
    def is_valid(self):
        return super().is_valid()

class CalendarST(DialogueST):
    def __init__(self):
        self.appointments = []
        self.repeating_appointments = []

    def update(self,
               confirmed_appointment: Union[AppointmentST, RepeatingAppointmentST]):
        if confirmed_appointment.is_appointment():
            self.appointments.append(confirmed_appointment)
        elif confirmed_appointment.is_repeating_appointment():
            self.repeating_appointments.append(confirmed_appointment)
        else:
            logging.warning('Appointment is not an appointment or repeating appointment.')
            raise ValueError('Appointment is not an appointment or repeating appointment.')
        
    def __str__(self):
        # TODO think this through
        raise NotImplementedError
    
    def expand_repeating_appointments(self):
        # Todo implement this
        raise NotImplementedError

    def to_dict(self):
        # TODO think this through
        raise NotImplementedError
    
    def is_valid(self):
        # TODO think this through
        pass
  