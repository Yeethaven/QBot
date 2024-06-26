import os
import discord as dc
from discord.ext import commands
from dotenv import load_dotenv
import networkx as nx
from variables import *
from pickle import dump, load
import numpy as np
from texttable import Texttable
import json
from vis import visualize

scoreboard = nx.DiGraph()

def save_scoreboard():
    """Save the scoreboard file"""
    global scoreboard
    #nx.write_graphml(scoreboard, filepath)
    dump(scoreboard, open(filepath, 'wb'))
    return

def load_scoreboard():
    """Read the scoreboard file"""
    global scoreboard
    #scoreboard = nx.read_graphml(path=filepath)
    scoreboard = load(open(filepath, 'rb'))
    return

def update_channelid(newid : int):
    with open("./src/variables.py", 'r') as variables:
        lines = variables.readlines()
        lines[3] = f"channelid = {newid}"

        with open("./src/variables.py", 'r') as variables:
            variables.writelines(lines)

    return

def update_scoreboard(msg : dc.message):
    """Updates the scoreboard variable (not the file). This method does so regardless of channel"""
    if msg.author.bot: # ignore bot messages
        return
    auth = msg.author.id # message author
    
    for m in msg.mentions:
        mid = m.id # mentioned user id
        debug(f"mention: {mid}")
        if scoreboard.has_edge(auth, mid):
            scoreboard[auth][mid]['weight'] += 1
        else:
            debug("adding edge")
            scoreboard.add_edge(auth, mid, weight=1)        

    #print_scoreboard()
    return

# This is async, there might be race conditions here...
#  I'm gonna pretend I didn't see that.
async def update_by_history(channel : dc.PartialMessageable):
    async for msg in channel.history(limit=None):
        update_scoreboard(msg)
    return

def format_leaderboard(leaderboard: list((int, int))):
    """
    params
    ------
    leaderboard : array of format [(userid, amount)]

    returns
    -------
    a string of format: "<@userid>: score\\n" for each entry
    """
    leaderboard = sorted(leaderboard, key=lambda x: -x[1])
    #outstring = ""
    #for entry in leaderboard:
    #    outstring += f"<@{entry[0]}>: {entry[1]}\n"
    #return outstring

    t = Texttable()
    alignment = ["c", "c"]
    t.set_cols_align(alignment)
    t.set_cols_valign(alignment)
    #t.set_deco(Texttable.BORDER | Texttable.HEADER)
        
    for entry in leaderboard:
        if entry[1] == 0:
            break
        #t.add_row([f"<@{entry[0]}>", entry[1]])
        t.add_row([entry[0], entry[1]])

    debug(t.draw())
    # code formatting messes up pings, so we use display_name insted
    return "```\n"+t.draw()+"```" # TODO: if this is >2000 chars, discord is unhappy - I'm gonna turn a blind eye to that

async def get_name(g:dc.Guild, uid:int, client:commands.Bot):
    '''Translates between uid and name. It does so by looking for a translation
    in namefile; if none is found, it makes an API call to discord and stores
    the result in namefile.
    Params
    ------
    g: dc.Guild
        The Guild the username should be looked up in

    uid: int
        ID of the user

    client: commands.bot
        The Bot

    Returns
    -------
    The display name of the user in the guild. If the uid isn't found in the specified
    guild (user leaving or no access to guild), the discord username is returned
    
    '''
    with open(namefile, "r") as file:
            names = json.load(file)

    if str(uid) in names:
        return names[str(uid)]
    
    try:
        name = (await g.fetch_member(uid)).display_name
    except dc.errors.NotFound:
        try:
            name = (await client.get_or_fetch_user(uid)).name
        except:
            name = "[deleted]"

    names[str(uid)] = name
    with open(namefile, "w") as file:
        json.dump(names, file)

    return name

def get_client():
    intents = dc.Intents.none()
    intents.guild_messages = True
    intents.message_content = True

    #client = dc.Client(intents=intents)
    client = commands.Bot(intents=intents)

    @client.event
    async def on_ready():
        global scoreboard
        debug(f'{client.user} has connected to Discord!')
        ch = await client.fetch_channel(channelid)
        scoreboard = nx.DiGraph()
        await update_by_history(ch)
        print_scoreboard()

    @client.event
    async def on_message(message : dc.Message):
        if message.author.bot: # ignore bot messages
            return
        debug(f'-----\nreceived message "{message.author.display_name}: {message.content}" in channel {message.channel.id}')

        if not message.channel.id == channelid:
            debug("Wrong channel, skipping.")
            return
                
        update_scoreboard(message)

    @client.command( #TODO this command doesn't show in discord
        description="set the channel to be watched [WIP]"
    )
    async def set_channelid(ctx:dc.ApplicationContext):
        #TODO use update_channelid, only if user is admin
        await ctx.respond("bruh")

    sc_coms = client.create_group("scoreboard", "get personal or global scoreboards")
    me = sc_coms.create_subgroup("me", "personal scoreboards")
    glob = sc_coms.create_subgroup("global", "global scoreborads")

    @sc_coms.command(
            description="All the stats. Warning: format might be fucked"
    )
    async def full(ctx:dc.ApplicationContext):
        tempmsg = (await ctx.respond("Working on it!"))
        nlist = sorted(scoreboard.nodes)
        mat = nx.to_numpy_array(scoreboard, nlist, dtype=int).astype(str)
        
        nlist_t = [(await get_name(ctx.guild, uid, client)) for uid in nlist] # nodelist translated into names

        t = Texttable()
        alignment = ["c"] * (len(nlist_t) + 1)
        t.set_cols_align(alignment)
        t.set_cols_valign(alignment)
        t.set_max_width(0)
        t.header(["quoter \ quoted"] + nlist_t)
        #t.set_deco(Texttable.BORDER | Texttable.HEADER)
        
        for i, name in enumerate(nlist_t):
            row = np.concatenate(([name], mat[i]))
            t.add_row(row)
        
        debug(t.draw())
        response = t.draw()
        if len(response) > (2000 - 6): # max msg length minus the backticks
            with open("./data/table.txt", "w", encoding="utf-8") as file:
                file.write(response)
            await ctx.send(file=dc.File("./data/table.txt"))
            os.remove("./data/table.txt")
            visualize(scoreboard)
            await ctx.send(file=dc.File("./data/plot.png"))
        else:
            await ctx.send("```\n"+response+"```")
        await tempmsg.delete_original_response()

    @me.command(
        description="How often was I quoted by whom?"
    )
    async def quoted(ctx:dc.ApplicationContext):
        tempmsg = await ctx.respond("Working on it!")
        leaderboard = []
        g = ctx.guild
        for usr, _, data in scoreboard.in_edges(ctx.author.id, data=True):
            leaderboard.append(((await get_name(ctx.guild, usr, client)), data['weight']))
        
        await ctx.send(f"{ctx.author.display_name} has been quoted by these people the most:\n" + format_leaderboard(leaderboard))
        await tempmsg.delete_original_response()

    @me.command(
        description="How often have I quoted whom?"
    )
    async def quotes(ctx:dc.ApplicationContext):
        tempmsg = await ctx.respond("Working on it!")
        leaderboard = []
        g = ctx.guild
        for _, usr, data in scoreboard.out_edges(ctx.author.id, data=True):
            leaderboard.append(((await get_name(ctx.guild, usr, client)), data['weight']))
        
        await ctx.send(f"{ctx.author.display_name} has quoted these people the most:\n" + format_leaderboard(leaderboard))
        await tempmsg.delete_original_response()

    @glob.command(
        description="Top quotees"
    )
    async def quotees(ctx:dc.ApplicationContext):
        tempmsg = await ctx.respond("Working on it!")
        leaderboard = []
        for usr, _ in scoreboard.adjacency():
            incoming = scoreboard.in_edges(usr, data=True)
            score = 0
            for entry in incoming:
                score += entry[2]['weight']
            
            leaderboard.append(((await get_name(ctx.guild, usr, client)), score))

        await ctx.send("These people have been quoted the most:\n" + format_leaderboard(leaderboard))
        await tempmsg.delete_original_response()

    @glob.command(
        description="Top quoters"
    )
    async def quoters(ctx:dc.ApplicationContext):
        tempmsg = await ctx.respond("Working on it!")
        leaderboard = []
        g = ctx.guild
        for usr, nbrdict in scoreboard.adjacency():
            score = 0
            for entry in nbrdict:
                score += nbrdict[entry]['weight']

            #name = await get_name(g, usr, client)
            leaderboard.append(((await get_name(g, usr, client)), score))

        await ctx.send("These people have written the most quotes:\n" + format_leaderboard(leaderboard))
        await tempmsg.delete_original_response()

    return client

def main():
    """Start the bot"""
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    global scoreboard
    load_scoreboard()

    client = get_client()
    client.run(TOKEN)
    return

def print_scoreboard():
    if DEBUG:
        global scoreboard
        debug(scoreboard)
        for n, nbrdict in scoreboard.adjacency():
            debug(n)
            debug(nbrdict)
    return

def clear_scoreboard_file():
    global scoreboard
    scoreboard = nx.DiGraph()
    save_scoreboard()
    return

if __name__ == "__main__":
    #clear_scoreboard()
    main()
    save_scoreboard()

    #load_scoreboard()
    #nlist = sorted(scoreboard.nodes)
    #arr = np.concatenate(([nlist], nx.to_numpy_array(scoreboard, nlist, dtype=int)))
    #debug(arr)
    #nlist = [-1] + nlist
    #for i, line in enumerate(arr):
    #    debug(f"{nlist[i]}  {line}")

    #c = get_client()
    #print_scoreboard()
