"""
TEMPLATES
"""

book_apartment_templates = [
    """I want to book apartment {apartment_number} for {guest_number} guests from {start_date} to {end_date}.""",
    """Can I reserve a place for {guest_number} people starting {start_date} and ending {end_date}?""",
    """Please book apartment {apartment_number} for me, my name is {name} {surname}, and I'll be staying from {start_date} to {end_date}.""",
    """I'd like to rent an apartment. My ID is {document_type} {document_number}. I need it from {start_date} to {end_date}."""
]

book_apartment_gt = """
        "apartment_number": "{apartment_number}",
        "name": "{name}",
        "surname": "{surname}",
        "document_type": "{document_type}",
        "document_number": "{document_number}",
        "guest_number": "{guest_number}",
        "start_date": "{start_date}",
        "end_date": "{end_date}"
"""

see_apartment_gt = """
        "apartment_numbers": {apartment_numbers}
"""

list_apartment_templates = [
    "Show me the available apartments.",
    "What apartments do you have right now?",
    "Can I see a list of available rentals?",
    "I haven't seen the apartments yet",
    "I don't know what apartments you've got",
    "I don't know the apartment numbers",
    "Are there any apartments open for booking?",
    "I need a place to stay. What are my options?"
]

see_apartment_templates = [
    "Show me apartment {apartment_numbers}.",
    "I'd like to see apartments {apartment_numbers}.",
    "Let me see apartment {apartment_numbers}.",
    "Can you show me apartment {apartment_numbers}?",
    "I want to see apartment {apartment_numbers}.",
    "Display apartment {apartment_numbers}.",
    "Pull up apartment {apartment_numbers}.",
    "Give me a look at apartment {apartment_numbers}.",
    "I’d like to view apartment {apartment_numbers}.",
    "Can you bring up apartment {apartment_numbers}?",
]


contact_operator_templates = [
    "I need help with my booking.",
    "Can I talk to a representative?",
    "Something is wrong with my apartment. I need assistance.",
    "I want to order food to my apartment.",
    "I need help with my booking.",
    "Can I talk to a representative?",
    "Something is wrong with my apartment. I need assistance.",
    "I want to order food to my apartment.",
    "I lost my key. What should I do?",
    "The heating is not working. Can someone fix it?",
]

fallback_templates = [
    "What’s the best restaurant in Paris?",
    "Tell me about the history of the Eiffel Tower.",
    "I had an argument with my wife",
    "My boss fired me",
    "I'd like to purchase BookMe",
    "Can I buy the apartment?",
     "What’s the best restaurant in Paris?",
    "Tell me about the history of the Eiffel Tower.",
    "How’s the weather today?",
    "Can you book me a flight to Rome?",
    "What’s the stock price of Tesla right now?",
    "Who won the Champions League last year?"
]
