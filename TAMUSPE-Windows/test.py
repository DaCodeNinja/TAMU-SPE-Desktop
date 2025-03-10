from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), 'etc/.env'))
AUTH_KEY = os.getenv("RESPONSE_KEY")

print(AUTH_KEY)