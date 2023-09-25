# ChatGPT Telegram Bot
Simple implementation using ChatGPT (and GPT-4) API, deployed as a Telegram Bot.

Feel free to open issues if you encounter any problems or have suggestions for improvement. 
However, I cannot guarantee that all issues will be addressed or resolved in a timely manner.

# How to Use
1. Environmental requirements:

    A server (only tested on Linux)
    
    python 3.8+
    
    pip install -r requirements.txt

2. API keys

    Fill your **OpenAI API key** and **Telegram Bot Token** in the 'config.json' file.
  
    You can obtain OpenAI API key from your openai account, specifically, access to GPT-4 is currently limited to invited users only.
  
    To create a Telegram Bot Token, please refer to https://core.telegram.org/bots#how-do-i-create-a-bot.

3. White list

    Fill telegram user id in the 'whitelist.json' file, only users in the white list can access the bot.
    
    You can get your user id by sending messege to [userinfo_bot](https://telegram.me/userinfobot).

4. Run

    python app.py


# Example


https://github.com/sky24h/ChatGPT_Telegram_Bot/assets/26270672/3985ad66-f965-4ea3-ac0c-fafa36fd4d43











