# This simulated API services being called and handled by the application

class Service():
    def __init__(self):
        pass

    def get_data(self):
        return "Data from service"
    
    def book_apartment(self, booking):
        print("BOOKED AN APARTMENT")
        print(booking)
