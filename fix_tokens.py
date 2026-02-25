import os
from pathlib import Path

def fix_tokens():
    update_token_path = Path("update_token.py")
    if update_token_path.exists():
        content = update_token_path.read_text(encoding="utf-8")
        content = content.replace("8264239620:AAEjhI1736D8fRwpW5YBNqtiUj0gL3xFcZA", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
        update_token_path.write_text(content, encoding="utf-8")
        print("Fixed update_token.py")

    restore_env_path = Path("restore_env.py")
    if restore_env_path.exists():
        content = restore_env_path.read_text(encoding="utf-8")
        content = content.replace("AIzaSyD2N-rsmfER9P2dZznBh4wXKAFZRajJ0eU", "YOUR_GEMINI_API_KEY_HERE")
        content = content.replace("8264239620:AAEjhI1736D8fRwpW5YBNqqtiUj0gL3xFcZA", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
        restore_env_path.write_text(content, encoding="utf-8")
        print("Fixed restore_env.py")

if __name__ == "__main__":
    fix_tokens()
