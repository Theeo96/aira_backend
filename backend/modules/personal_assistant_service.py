import os
import datetime
import dateutil.parser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from .cosmos_db import cosmos_service

# Scopes: Read-only access to Calendar and Gmail
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/gmail.readonly'
]

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

class PersonalAssistantService:
    def __init__(self, user_email: str):
        self.user_email = user_email
        self.creds = None
        self.authenticate()

    def authenticate(self):
        """
        Builds Google Credentials from the OAuth token stored in Cosmos DB.
        """
        print(f"[Assistant] Authenticating for Calendar/Gmail access (User: {self.user_email})...")
        
        user_data = cosmos_service.get_user_by_email(self.user_email)
        if not user_data or 'google_token' not in user_data:
            print("[Assistant] Authentication failed: No token found in DB for this user.")
            return

        token_data = user_data['google_token']
        
        try:
            client_id = os.environ.get('GOOGLE_CLIENT_ID')
            client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
            
            self.creds = Credentials(
                token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES
            )

            if not self.creds.valid:
                if self.creds.expired and self.creds.refresh_token:
                    if not client_id or not client_secret:
                        print("[Assistant] WARNING: Cannot refresh token because GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is missing from .env!")
                    else:
                        print("[Assistant] Refreshing expired token...")
                    try:
                        self.creds.refresh(Request())
                        # Note: we might want to save the newly refreshed token back to DB
                        # token_data['access_token'] = self.creds.token
                        # token_data['refresh_token'] = self.creds.refresh_token or token_data.get('refresh_token')
                        # The google_auth library doesn't expose expiry simply without a lot of tz hacking,
                        # but just knowing the token is refreshed is usually enough for the session lifecycle.
                    except Exception as e:
                        print(f"[Assistant] Token refresh failed: {e}")
                        self.creds = None
        except Exception as e:
            print(f"[Assistant] Token build failed: {e}")
            self.creds = None

    def get_upcoming_events(self, max_results=15):
        """
        Fetches upcoming calendar events for the next 365 days.
        Returns a list of formatted strings.
        """
        if not self.creds: return []
        
        events_summary = []
        try:
            service = build('calendar', 'v3', credentials=self.creds, cache_discovery=False)
            now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            one_year_later = (datetime.datetime.utcnow() + datetime.timedelta(days=365)).isoformat() + 'Z'
            
            print("[Assistant] Fetching calendar events (1 Year)...")
            events_result = service.events().list(
                calendarId='primary', timeMin=now, timeMax=one_year_later,
                maxResults=max_results, singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                summary = event.get('summary', '(No Title)')
                
                # Format time for easier reading
                try:
                    dt = dateutil.parser.parse(start)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_time = start
                    
                events_summary.append(f"- [{formatted_time}] {summary}")
                
        except Exception as e:
            print(f"[Assistant] Calendar Error: {e}")
            
        return events_summary

    def get_unread_emails(self, recent_limit=20, important_limit=5):
        """
        Fetches emails:
        1. Recent 1 month (Read/Unread) - limited to recent_limit
        2. Important (Any time) - limited to important_limit
        Merges and deduplicates.
        """
        if not self.creds: return []
        
        emails_summary = []
        try:
            service = build('gmail', 'v1', credentials=self.creds, cache_discovery=False)
            
            # 1. Recent (1 Month)
            one_month_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y/%m/%d')
            query_recent = f'after:{one_month_ago}'
            print(f"[Assistant] Fetching Recent emails ({recent_limit})...")
            res_recent = service.users().messages().list(userId='me', q=query_recent, maxResults=recent_limit).execute()
            msgs_recent = res_recent.get('messages', [])

            # 2. Important (All time)
            query_important = 'label:IMPORTANT'
            print(f"[Assistant] Fetching Important emails ({important_limit})...")
            res_important = service.users().messages().list(userId='me', q=query_important, maxResults=important_limit).execute()
            msgs_important = res_important.get('messages', [])
            
            # 3. Merge & Deduplicate
            all_msgs = {m['id']: m for m in msgs_recent + msgs_important}.values()
            
            # Fetch Details
            for msg in all_msgs:
                try:
                    txt = service.users().messages().get(userId='me', id=msg['id']).execute()
                    payload = txt.get('payload', {})
                    headers = payload.get('headers', [])
                    snippet = txt.get('snippet', '')
                    internal_date = int(txt.get('internalDate', 0)) / 1000 # timestamp

                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown)')
                    
                    if '<' in sender: sender = sender.split('<')[0].strip()
                    
                    # Date formatting
                    date_str = datetime.datetime.fromtimestamp(internal_date).strftime('%Y-%m-%d %H:%M')
                    
                    emails_summary.append({
                        "text": f"- [{date_str}] [From: {sender}] {subject} | {snippet[:50]}...",
                        "timestamp": internal_date
                    })
                except Exception:
                    continue
            
            # Sort by timestamp desc
            emails_summary.sort(key=lambda x: x['timestamp'], reverse=True)
            return [e['text'] for e in emails_summary]

        except Exception as e:
            print(f"[Assistant] Gmail Error: {e}")
            return []

    def get_context_summary(self):
        """
        Aggregates Calendar and Gmail info into a context string for the LLM.
        """
        if not self.creds: return None
        
        events = self.get_upcoming_events()
        emails = self.get_unread_emails()
        
        context_parts = []
        
        if events:
            context_parts.append("[User's Upcoming Schedule]")
            context_parts.extend(events)
            context_parts.append("") # spacer
            
        if emails:
            context_parts.append("[User's Recent & Important Emails]")
            context_parts.extend(emails)
            context_parts.append("") # spacer
            
        if not context_parts:
            return None
            
        final_context = "\n".join(context_parts)
        return final_context
