# Personal finance telegram bot

Everybody need good money management. There are a lot of apps, but all of free apps I found were limited in functionality or only for one person usage. To solve a problem I decided to write Telegram bot, simply swichable to any chat. It helps you categorize expenses and see current month total summ after every purchase (groupped by currencies).

## Getting Started

You should install the Telegram app on your phone or desktop, create a chat with members you want to manage money. Add the bot to this chat, giving to bot all privileges. Edit settings of bot, using BotFather (name, avatar etc.). Also you have to run bot.py file. I solved this purpose using DigitalOcean cheap 5$ dropplet, where bot.py file is running using supervisor.

### Installing

Let's run the bot!

You have to create credentials.py file in the repo directory, where you should have your a bot token and ids of all users, who are invited to the chat with bot. Example of non-existing variables:

```
token = '419039058:ABGpPqHni0XPsh-8ZFsX9P7d-AhkNTExiYA'
ALLOWED_USERS_IDS = (123258728, 214253721)
```

Token should be given by BotFather, ALLOWED_USERS_IDS - ids of Users in chat (find it by debugging you may).

Install virtualenv, create enviroment and run requirements installation:

```
pip install -r requirements.txt
```

Install supervisor and create it's config. Config important part:

```
[program:bot]
directory=/root/projects/financer
environment=PATH="/root/projects/financer/env/bin"
command=python3 bot.py
user=root
autostart=true
autorestart=true
```

Run supervisorctl:

```
supervisorctl start bot
```
It's working now!

### Rules of interface using

Expense should be formatted like "5usd ice-cream", which create callback message for choosing category for ice-cream expense. If you use BYN as default currency, you can write only "5 ice-cream". If you repeat message with the note "ice-cream" three times with the same category - category for expense will be set automatically, notifying you about it. You also can write multiple expenses in the same format, divided by double space or by ";". For every expense (except remembered) menu for choosing category appears. Every expense ends with statistics message. You can  call such message using command.

## Authors

* **Mihail Landyuk** - *Initial work* - [Finance Telegram Bot](https://github.com/miland1990/financer)
