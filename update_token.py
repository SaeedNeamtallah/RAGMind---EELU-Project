import os
from pathlib import Path

# Path to .env file
env_file = Path("c:/Users/abdul/Documents/EELU/RAGMind/.env")

# Read current content
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update or add TELEGRAM_BOT_TOKEN
    token_found = False
    for i, line in enumerate(lines):
        if line.startswith('TELEGRAM_BOT_TOKEN='):
            lines[i] = 'TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE\n'
            token_found = True
            break
    
    if not token_found:
        lines.append('TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE\n')
    
    # Write back
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✓ Token updated successfully!")
else:
    print("✗ .env file not found!")
