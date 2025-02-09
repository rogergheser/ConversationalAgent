import random
import string
import json
import logging
import omegaconf
import sys
sys.path.append('/Users/amirgheser/ConversationalAgent')
from faker import Faker
from templates import *
from components.validate import Validator
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

def generate_random_data():
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

def complete_booking(val):
    return """
{
    "intent" : "book_apartment,
    "slots" : {
""" + val + """
    }
}
"""

if __name__ == '__main__':
    templates = {
        'book_apartment': book_apartment_templates,
        'list_apartment' : list_apartment_templates,
        'contact_operator' : contact_operator_templates,
        'fallback' : fallback_templates
    }
    logger = logging.getLogger('__main__')
    metrics = Metrics()
    validator = Validator()
    with open('config.yaml') as f:
        cfg = omegaconf.OmegaConf.load('config.yaml')
    # history = ConversationHistory()

    # nlu = NLU.from_cfg(cfg, history)
    # dm = DM.from_cfg(cfg, history)
    
    data = {}
    nlu_data = []
    for temp_name, temp_list in templates.items():
        if temp_name == 'book_apartment':
            for _ in range(50):
                template = random.choice(temp_list)
                data = generate_random_data()
                formattable_fields, formattable_data = extract_fields(template, data)
                data_values = {field: formattable_data.get(field, 'null') for field in formattable_data}
                nlu_data.append({
                        'sample' : template.format(**formattable_data),
                        'label' : complete_booking(book_apartment_gt.format(**data_values))
                    }
                )
        else:
            output = json.dump({
                "intent" : temp_name,
                "slots" : {}
            })
            for temp in temp_list:
                nlu_data.append(
                    {
                        'sample' : temp,
                        'label' : output
                    }
                )

