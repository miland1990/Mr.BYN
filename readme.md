# Mr.BYN

Everybody need good money management. There are a lot of apps, but all of free apps I'd found were limited in functionality or only for one person usage. To solve the problem I decided to write Telegram bot, simply swichable to any Telegram group. It helps you categorize expenses and see current month total summ after every purchase (groupped by currencies).

## Getting Started

1) Install the Telegram app on your phone or desktop.
2) Create bot using BotFather. Edit bot name, avatar picture if you want. Get token to fill credentials.py. Add actual command:
```
1. Enter command to BotFather: /setcommands
2. Choose exact bot.
3. Enter two commands like:
```
```
stat - Show mounth categorization
category_expenses - Show category detalization
```
3) Create group chat using BotFather if you want to manage multiuser budget, or simply have dialog with bot if you are the only user. If you choose multiuser variant - add all participants to the group and edit bot settings using BotFather to allow bot add/edit messages in the group (BotSettings/GroupPrivacy/TurnOff).
4) You can run bot locally, but it's a good practice to host your bot on a virtual machine (I prefer DigitalOcean VM). 
5) Clone this repo to your working machine.
```
git clone https://github.com/miland1990/Mr.BYN.git
```
6) Create credentials.py and complete two variables like in credentials.example.py
```
token = '123456789:BBEg1PKYQCpV2ej-xtblBY7KruNI_Nebo6w'
ALLOWED_USERS_IDS = (123456789,)
```
Token is unique string for your bot, which BotFather gave you earlier. ALLOWED_USERS_IDS - tuple of user_id in Telegram. To get you can use @get_id_bot. Ask every participant of a group this user_id and put it in the tuple.
### Run the bot using virtualenv and supervisor:

Install virtualenv, create enviroment and run requirements.txt:

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

Stop the bot if you need:
```
supervisorctl stop bot
```

### Or run the bot using Docker
```
docker build -t bot .
docker run -d -v $PWD/vol:/code/vol --name bot bot
```

### Using

Expense should be formatted like "5 usd ice-cream", which create callback message for choosing category for ice-cream expense. 
If you use BYN as default currency, you can write only "5 ice-cream". 
If you repeat message with the note "ice-cream" three times with the same category - it's category will be set automatically next time, notifying you about it. You also can write multiple expenses in the same format, divided by double space or by ";". Menu for choosing category appears for every expense (except remembered). Every expense ends with statistics message.
```
/stats
```
Add this command to your bot using  BotFather. This command helps to categorize expenses by exact mounth. 

```
rm 55
```
You can delete purchase using it's id (example above)

```
/category_expenses
```
Add this command to your bot using  BotFather. This command helps to list all expenses by category during current mounth. 



## Authors

* **Mihail Landyuk** - *Initial work* - [Finance Telegram Bot](https://github.com/miland1990/financer)
