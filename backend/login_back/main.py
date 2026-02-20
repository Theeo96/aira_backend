import os
import uvicorn
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from azure.cosmos import CosmosClient
import datetime
import uuid

# Load Environment Variables (Azure App Service Configuration)
# These will be set in Azure Portal -> Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
COSMOS_DB_ENDPOINT = os.environ.get('COSMOS_DB_ENDPOINT')
COSMOS_DB_KEY = os.environ.get('COSMOS_DB_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# --- Database Setup ---
cosmos_client = None
user_container = None

def init_db():
    global cosmos_client, user_container
    if COSMOS_DB_ENDPOINT and COSMOS_DB_KEY:
        try:
            cosmos_client = CosmosClient(COSMOS_DB_ENDPOINT, COSMOS_DB_KEY)
            database = cosmos_client.create_database_if_not_exists(id="samantha_db")
            user_container = database.create_container_if_not_exists(
                id="users",
                partition_key="/email" # Partition by Email for efficient lookup
            )
            print("Cosmos DB Connected.")
        except Exception as e:
            print(f"Cosmos DB Error: {e}")

# --- OAuth Setup ---
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile https://www.googleapis.com/auth/calendar.readonly',
        'prompt': 'consent' # Force consent screen to get refresh_token
    }
)

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get('/')
async def homepage(request: Request):
    user = request.session.get('user')
    if user:
        token_display = request.session.get('token')
        return HTMLResponse(f'''
            <html>
                <body style="font-family: Arial, sans-serif; text-align: center; padding-top: 50px;">
                    <h1>Login Successful!</h1>
                    <p>Welcome, {user.get("name")}</p>
                    <p>Email: {user.get("email")}</p>
                    <hr>
                    <h3>Copy this Token for your Desktop App:</h3>
                    <div style="background: #f0f0f0; padding: 15px; display: inline-block; border-radius: 5px;">
                        <code style="font-size: 1.2em; font-weight: bold;">{token_display}</code>
                    </div>
                    <br><br>
                    <a href="/logout">Logout</a>
                </body>
            </html>
        ''')
    return HTMLResponse('''
        <html>
            <body style="font-family: Arial, sans-serif; text-align: center; padding-top: 50px;">
                <h1>Samantha Backend</h1>
                <a href="/login" style="background: #4285F4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Login with Google</a>
            </body>
        </html>
    ''')

@app.get('/login')
async def login(request: Request, redirect_target: str = "http://localhost:3000"):
    # Save target URL to session
    request.session['redirect_target'] = redirect_target
    
    # Dynamic Redirect URI based on Host (works for both Localhost and Azure)
    redirect_uri = request.url_for('auth')
    # If using Azure App Service behind a proxy (HTTPS), you might need to force https scheme if not automatic
    if 'azurewebsites.net' in str(redirect_uri):
        redirect_uri = str(redirect_uri).replace('http://', 'https://')
        
    return await oauth.google.authorize_redirect(request, redirect_uri, access_type='offline') # access_type='offline' for refresh_token

@app.get('/auth')
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if not user_info:
             user_info = await oauth.google.userinfo(token=token)

        # Save/Update User in Cosmos DB
        if user_container:
            # Prepare data
            user_data = {
                "id": str(uuid.uuid4()), # New UUID for potentially new entry
                "email": user_info['email'],
                "name": user_info.get('name'),
                "picture": user_info.get('picture'),
                "last_login": datetime.datetime.utcnow().isoformat(),
                "google_token": token # Contains access_token, refresh_token (if consent), expiry
            }
            
            # Check if user exists to preserve their ID
            try:
                # Query by email
                query = "SELECT * FROM c WHERE c.email = @email"
                params = [{"name": "@email", "value": user_info['email']}]
                items = list(user_container.query_items(
                    query=query, parameters=params, enable_cross_partition_query=True
                ))
                
                if items:
                    user_data['id'] = items[0]['id'] # Use existing ID
                
                user_container.upsert_item(user_data)
                print(f"User {user_info['email']} saved/updated.")
                
            except Exception as e:
                print(f"DB Save Error: {e}")
        
        # Session Setting
        request.session['user'] = user_info
        
        # We use Email as the "Token" for the Desktop App to identify the user
        token_str = user_info['email']
        request.session['token'] = token_str
        
        # [Auto-Login Logic]
        target_url = request.session.pop('redirect_target', 'http://localhost:3000')
        final_redirect = f"{target_url}?token={token_str}"
        
        return RedirectResponse(url=final_redirect)

    except Exception as e:
        return HTMLResponse(f"<h1>Auth Error</h1><p>{e}</p>")

@app.get('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    request.session.pop('token', None)
    return RedirectResponse(url='/')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
