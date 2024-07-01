from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Retrieve keys and add them to the project
SHOPIFY_API_KEY: str = os.getenv("SHOPIFY_API_KEY")
DISCORD_WEBHOOK: str = os.getenv("DISCORD_WEBHOOK")
SHOPIFY_URL: str = os.getenv("SHOPIFY_URL")
NINJA_KEY: str = os.getenv("NINJA_KEY")

# Error handling to ensure all environment variables are set
required_env_vars = {
    "SHOPIFY_API_KEY": SHOPIFY_API_KEY,
    "DISCORD_WEBHOOK": DISCORD_WEBHOOK,
    "SHOPIFY_URL": SHOPIFY_URL,
    "NINJA_KEY": NINJA_KEY
}
print("DISCORD_WEBHOOK:", DISCORD_WEBHOOK)

missing_vars = [var for var, value in required_env_vars.items() if value is None]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
