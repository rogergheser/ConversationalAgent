import random
import string
import json
import logging
import omegaconf
import sys
import pickle
import os
sys.path.append('/Users/amirgheser/ConversationalAgent')
from faker import Faker
from data_generation.templates_nlu import *
from data_generation.templates_dm import *
from components.validate import Validator
from utils.msg_parsing import parse_json
# from components import NLU, DM
# from utils import ConversationHistory
"""
This will hold the generator class with the task of generating data for evaluation by using string injection.
"""
class Metrics():
    pass

def random_natural_date():
    months = ["January", "February", "March", "April", "June", "July", "September", "October", "November", "December"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    options = [
        "tomorrow", 
        "next Monday", 
        "next Tuesday",  
        "next Friday",  
        "next Sunday", 
        "this weekend", 
        "next weekend", 
        "in two weeks", 
        "on February 10th", 
        "in three days", 
        "on the 15th of next month"
    ]
    return random.choice(options)

# Generate a random date in "DD/MM/YY" format
def random_date():
    fake = Faker()
    date_obj = fake.date_between(start_date="today", end_date="+60d")
    return date_obj.strftime("%d/%m/%y")

# Randomly choose between structured and natural format
def random_date_format():
    return random.choice([random_date(), random_natural_date()])

def extract_fields(template, data):
    formatter = string.Formatter()
    fields = [field_name for _, field_name, _, _ in formatter.parse(template) if field_name]
    # extract data values that can be injected
    data_values = {field: data.get(field, '') for field in fields}
    return fields, data_values

def generate_random_booking_data():
    fake = Faker()
    return {
        "apartment_number": random.randint(1000, 9999),  # Apartment numbers between 100 and 999
        "guest_number": random.randint(1, 5),  # Random number of guests
        "name": fake.first_name(),
        "surname": fake.last_name(),
        "document_type": random.choice(["passport", "ID card", "driver's license"]),
        "document_number": fake.random_number(digits=8),
        "start_date": fake.date_between(start_date="today", end_date="+30d").strftime("%d/%m/%y"),
        "end_date": fake.date_between(start_date="+31d", end_date="+60d").strftime("%d/%m/%y"),
    }

def complete_booking(val : str):
    return """
{
    "intent" : "book_apartment",
    "slots" : {
""" + val.strip('\n') + """
    }
}
"""

def complete_see_apart(val : str):
    return """
{
    "intent" : "see_apartments",
    "slots" : {
""" + val.strip('\n') + """
    }
}
"""

def natural_language_join(lst):
    if len(lst) > 1:
        return ', '.join([str(x) for x in lst[:-1]]) + ' and ' + str(lst[-1])
    elif len(lst) == 1:
        return str(lst[0])

def generate_nlu_data(templates):
    nlu_data = []
    for temp_name, temp_list in templates.items():
        if temp_name == 'book_apartment':
            for _ in range(50):
                template = random.choice(temp_list)
                data = generate_random_booking_data()
                formattable_fields, formattable_data = extract_fields(template, data)
                data_values = {field: formattable_data.get(field, 'null') for field in data}
                nlu_data.append({
                        'sample': template.format(**formattable_data),
                        'label': complete_booking(book_apartment_gt.format(**data_values)),
                        'intent': temp_name
                    }
                )
        elif temp_name == 'see_apartments':
            for _ in range(25):
                template = random.choice(temp_list)
                data = {
                    "apartment_numbers" : list(filter(lambda x : random.getrandbits(1), range(4)))
                }
                if data['apartment_numbers'] == []:
                    data['apartment_numbers'] = [random.randint(1, 4)]

                formattable_fields, formattable_data = extract_fields(template, data)
                data_values = {field: formattable_data.get(field, 'null') for field in data}
                formattable_data['apartment_numbers'] = natural_language_join(data['apartment_numbers'])
                nlu_data.append({
                        'sample': template.format(**formattable_data),
                        'label': complete_see_apart(see_apartment_gt.format(**data_values)),
                        'intent': temp_name
                    }
                )
        else:
            output = json.dumps({
                "intent": temp_name,
                "slots": {}
            })
            for temp in temp_list:
                nlu_data.append(
                    {
                        'sample': temp,
                        'label': output,
                        'intent': temp_name
                    }
                )
    return nlu_data

def generate_dm_data(dm_input_data):
    final_data = []
    for value in dm_input_data:
        if value['intent'] == 'book_apartment':
            if 'null' in value['meaning_representation']:
                action = 'ask_info'
                slots = json.loads(value['meaning_representation'])
                slots = [key for key in slots if slots[key] == 'null']
            else:
                action = 'confirm_booking'
                slots = []
        elif value['intent'] == 'see_apartments':
            if 'null' in value['meaning_representation']:
                action = 'ask_info'
                slots = 'apartment_numbers'
            else:
                action = 'show_apartments'
                slots = json.loads(value['meaning_representation'])['slots']['apartment_numbers']
        else:
            action = value['intent']
            slots = []            

        system_action = {
            "action" : action,
            "argument" : slots
        }

        final_data.append({
            'meaning_representation' : value['meaning_representation'],
            'label' : json.dumps(system_action),
            'intent' : value['intent'],
            'action' : action
        })

    return final_data

def integrate_complete_booking(dm_data: list[dict]):
    
    for _ in range(20):
        data = generate_random_booking_data()
        system_action = json.dumps({
            "action" : 'confirm_booking',
            "argument" : []
        })

        dm_data.append({
            'meaning_representation' : complete_booking(book_apartment_gt.format(**data)),
            'label' : system_action,
            'intent' : 'book_apartment',
            'action' : 'confirm_booking'
        })

    return dm_data

def get_nlu_data():
    nlu_templates = {
        'book_apartment': book_apartment_templates,
        'list_apartments': list_apartment_templates,
        'contact_operator': contact_operator_templates,
        'fallback': fallback_templates,
        'see_apartments': see_apartment_templates
    }
    logger = logging.getLogger('__main__')
    validator = Validator()
    with open('config.yaml') as f:
        cfg = omegaconf.OmegaConf.load('config.yaml')

    nlu_data = generate_nlu_data(nlu_templates)

    with open('data/test/nlu_data.pkl', 'wb') as f:
        pickle.dump(nlu_data, f)
    
def get_dm_data():
    if not os.path.exists('data/test/nlu_data.pkl'):
        get_nlu_data()
    with open('data/test/nlu_data.pkl', 'rb') as f:
        nlu_data = pickle.load(f)

    dm_input_data = [{'intent' : x['intent'], 'meaning_representation' : x['label'] } for x in nlu_data]
    dm_data = generate_dm_data(dm_input_data)
    dm_data = integrate_complete_booking(dm_data)
    with open('data/test/dm_data.pkl', 'wb') as f:
        pickle.dump(dm_data, f)

if __name__ == '__main__':
    nlu_templates = {
        'book_apartment': book_apartment_templates,
        'list_apartments': list_apartment_templates,
        'contact_operator': contact_operator_templates,
        'fallback': fallback_templates,
        'see_apartments': see_apartment_templates
    }
    logger = logging.getLogger('__main__')
    validator = Validator()
    with open('config.yaml') as f:
        cfg = omegaconf.OmegaConf.load('config.yaml')

    nlu_data = generate_nlu_data(nlu_templates)
    dm_input_data = [{'intent' : x['intent'], 'meaning_representation' : x['label'] } for x in nlu_data]
    dm_data = generate_dm_data(dm_input_data)
    dm_data = integrate_complete_booking(dm_data)
    with open('data/test/nlu_data.pkl', 'wb') as f:
        pickle.dump(nlu_data, f)
    with open('data/test/dm_data.pkl', 'wb') as f:
        pickle.dump(dm_data, f)