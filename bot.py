import discord
from discord.ext import commands
import json
import os

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True
intents.presences = False

bot = commands.Bot(command_prefix="!", intents=intents)

HITTERS_FILE = "hitters.json"
SECRET_ROLE_NAME = "Member"  # Make sure this matches your secret role EXACTLY

# Load hitters list from JSON file
def load_hitters():
    if not os.path.exists(HITTERS_FILE):
        return []
    with open(HITTERS_FILE, "r") as f:
        return json.load(f)

# Save hitters list to JSON file
def save_hitters(hitters):
    with open(HITTERS_FILE, "w") as f:
        json.dump(hitters, f, indent=2)

# Add a user to the hitter list
def add_hitter(user_id):
    hitters = load_hitters()
    if user_id not in hitters:
        hitters.append(user_id)
        save_hitters(hitters)

# Remove a user from the hitter list
def remove_hitter(user_id):
    hitters = load_hitters()
    if user_id in hitters:
        hitters.remove(user_id)
        save_hitters(hitters)

# Get the secret role object from the guild
def get_secret_role(guild):
    roles = [r for r in guild.roles if r.name == SECRET_ROLE_NAME]
    if len(roles) >= 2:
        return sorted(roles, key=lambda r: r.position)[-1]  # The lower one is the secret
    return None

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

@bot.event
async def on_member_update(before, after):
    secret_role = get_secret_role(after.guild)
    if secret_role is None:
        return

    had_role = secret_role in before.roles
    has_role = secret_role in after.roles

    if not had_role and has_role:
        add_hitter(after.id)
        print(f"Added hitter: {after.name}")
    elif had_role and not has_role:
        remove_hitter(after.id)
        print(f"Removed hitter: {after.name}")

@bot.command()
async def ishitter(ctx, member: discord.Member):
    hitters = load_hitters()
    if member.id in hitters:
        await ctx.send(f"✅ {member.mention} is a hitter.")
    else:
        await ctx.send(f"❌ {member.mention} is NOT a hitter.")

@bot.command()
async def listhitters(ctx):
    hitters = load_hitters()
    if not hitters:
        await ctx.send("There are currently no hitters.")
        return

    display = []
    for uid in hitters:
        member = ctx.guild.get_member(uid)
        if member:
            display.append(member.mention)

    msg = ", ".join(display)
    if len(msg) > 4000:
        await ctx.send("Too many hitters to display.")
    else:
        await ctx.send("**Hitters:** " + msg)

@bot.command()
async def addhitter(ctx, member: discord.Member):
    secret_role = get_secret_role(ctx.guild)
    if not secret_role:
        await ctx.send("Secret role not found.")
        return

    await member.add_roles(secret_role)
    await ctx.send(f"✅ {member.mention} has been added as a hitter.")

@bot.command()
async def removehitter(ctx, member: discord.Member):
    secret_role = get_secret_role(ctx.guild)
    if not secret_role:
        await ctx.send("Secret role not found.")
        return

    await member.remove_roles(secret_role)
    await ctx.send(f"✅ {member.mention} has been removed as a hitter.")

import os
bot.run(os.getenv("DISCORD_TOKEN"))


