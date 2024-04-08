# QBot - a discord bot to collect and aggregate stats about pings
## What does it do?
QBot reads all messages in a set channel and keeps track of how often every user has pinged every user (including themselves).

The intended use case is the analysis of a quotes channel on a small server.

## Available commands
`/set_channelid <channelid>` - (WIP) Set the channel the bot should analyze. For now, this is done by manually editing variables.py

`/scoreboard me quotes` - Send a list showing how often the user has quoted which other users in the analyzed channel

`/scoreboard me quoted` - Send a list showing how often the user has been quoted by which other users in the analyzed channel

`/scoreboard global quoters` - Send a list showing how many quotes each user (with >= 0 quotes) has written in the analyzed channel

`/scoreboard global quotees` - Send a list showing how times each user (with >= 0 quotes) was quoted in the analyzed channel

`/scoreboard full` - Send a 2d table showing how many times each user has quoted each user. If this list is over 2000 characters long (discord character limit), send it as a .txt file

## Hosting the bot
To use the bot yourself (which you probably shouldn't - this was hacked together as a quick side project and is by no means clean code), you just need to specify the bot's token in a file called `.env` in the /src folder.
The file should contain a single line that looks like this:

DISCORD_TOKEN=123456789abcdefg

You also need to change the `channelid` in variables.py to your quotes channel's id.

For a tutorial to create an application and add the bot to your server, you could follow [this link](https://realpython.com/how-to-make-a-discord-bot-python/#how-to-make-a-discord-bot-in-the-developer-portal) or find one of the countless others online.

## Internal workings
Upon connection to discord, the bot reads the full message history of the target channel (as specified by `channelid` in src/variables.py).
Every time a message contains a ping, it creates an edge in the graph `scoreboard` that goes from the message author to the pinged user.
If there is already an edge there, the weight is increased by one.

From then on, it reads every message sent, and if it is in the quotes channel, it updaters the graph accordingly.

The scoreboard can be saved to and loaded from the file data/scoreboard via pickle.
This functionality is currently not used, because the bot is hosted on my personal machine - thus it might miss messages, and it has to analyze the full message history every time anyway.
In the future, I might implement a feature to only load messages up to the point of last logoff.
