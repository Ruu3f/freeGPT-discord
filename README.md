# freeGPT-discord

Discord chatbot and image generator powered by freeGPT.

## Support this repository:
- ⭐ **Star the project:** Star this and the [freeGPT repository](https://github.com/Ruu3f/freeGPT). It means a lot to me! 💕
- 🎉 **Join my Discord Server:** Chat with me and others. [Join here](https://dsc.gg/devhub-rsgh):

[![DiscordWidget](https://discordapp.com/api/guilds/1137347499414278204/widget.png?style=banner2)](https://dsc.gg/devhub-rsgh)

## Getting Started:

1. **Download the Source Code:** Start by downloading the bot's source code.

2. **Install Dependencies:** Open your terminal and run:
```pip install -r requirements.txt```

3. **Application Setup:**
    - Create a new application on the [Discord Developer Portal](https://discord.com/developers).
    - In the app's settings, enable the `message content` intent and copy the token.

4. **Get your Huggingface token:** Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) and create a token with 'Read' role and copy it.

5. **Add Your Bot Token and Huggingface Token:** Paste the copied tokens in bot.py:
  ```python
  HF_TOKEN = "yourHuggingFaceToken"
  TOKEN = "yourBotToken"
  ```

6. **Run the Bot:** Open your terminal and run:
```python bot.py```
