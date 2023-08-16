# LuckyBot (deprecated)

[<img src='cover.png' width='160'/>](cover.png)

My second bot.
> https://t.me/LuckyBeast_bot

This bot was made to remind you of the things you don't want to forget. <br>
You can save text notes in the database. A couple of times a day LuckyBot will take a random note and send it to you. <br>
All notes are stored in an encrypted form.

## Bot architecture

[<img src='design.png' width='760'/>](design.png)

If you want to run a copy, you need to get a bot API from BotFather. <br>
You also need following secrets:

- Webhook secret token - random urlsafe string
- salt - for hashing
- Encryption key - for Fernet
- Your Telegram UID - for admin commands

Look into the lucky_bot.helpers.constants.py for configuration.


