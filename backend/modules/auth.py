# Simple Auth Helper for Google Login
# Since we are using a "Token Paste" method from an external URL, 
# this module primarily validates the token matches a minimal format (email-like)
# In a production app, you would verify the ID Token signature here.

def verify_token(token):
    """
    Simulates token verification. 
    In the reference flow, the 'token' is often just the email provided by the user 
    after authenticating on the separate login page.
    """
    if not token:
        return None
    
    token = token.strip()
    
    # Basic Email validation (Regex or simple check)
    if "@" in token and "." in token:
        return token
    
    return None
