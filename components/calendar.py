from __future__ import print_function
import datetime
import os.path
import omegaconf

from typing import Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class Calendar():
    """
    Calendar class to manage appointments, configure when API are available.
    """
    def __init__(self, credentials_file, token_file, scopes, calendar_id, cfg):
        self.creds = None
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes
        self.service = None
        self.calendar_id = calendar_id
        self.cfg = cfg

        self.creds = self._get_credentials()
        self.service = self._build_service()

        events_result = self.service.events().list(calendarId=calendar_id).execute()
        events = events_result.get('items', [])

    @classmethod
    def from_config(cls, cfg: dict):
        cfg = cfg['Calendar']
        return cls(cfg['credentials_file'], cfg['token_file'], cfg['scopes'], cfg['calendar_id'], cfg)

    def _get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f'Error refreshing access token: {e}')
                    return None
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())
        return self.creds

    def _build_service(self):
        """Builds the Calendar service object.

        Returns:
            The Calendar service object.
        """
        if self.creds:
            self.service = build('calendar', 'v3', credentials=self.creds)
        return self.service

    def list_appointments(self, argument):
        # Todo Implement functions
        print("This is a temporary list of appointments")


    def set_appointment(self, appointmentST):
        # TODO
        event = Event.create(self.cfg, appointmentST)
        pass

    def create_repeating_appointment(self, argument):
        # Todo Implement functions
        pass

    def list_available_slots(self, argument):
        # Todo Implement functions
        pass

    def cancel_appointment(self, argument):
        # Todo Implement functions
        pass

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
    

if __name__ == '__main__':
    path = 'config.yaml'
    cfg = omegaconf.OmegaConf.load(path)

    calendar = Calendar.from_config(cfg)

    