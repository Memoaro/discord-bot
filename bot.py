import os
import discord
from discord.ext import commands

# Set the secret role name here — exact name of your "secret" hitter role
SECRET_ROLE_NAME = "Member"

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def get_secret_role(guild):
    for role in guild.roles:
        if role.name == SECRET_ROLE_NAME:
            return role
    return None

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def ishitter(ctx, member: discord.Member = None):
    member = member or ctx.author
    secret_role = get_secret_role(ctx.guild)
    if secret_role is None:
        await ctx.send("Secret role not found in this server.")
        return
    if secret_role in member.roles:
        await ctx.send(f"✅ {member.mention} is a hitter.")
    else:
        await ctx.send(f"❌ {member.mention} is NOT a hitter.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def addhitter(ctx, member: discord.Member):
    secret_role = get_secret_role(ctx.guild)
    if secret_role is None:
        await ctx.send("Secret role not found.")
        return
    if secret_role in member.roles:
        await ctx.send(f"{member.mention} already has the hitter role.")
        return
    try:
        await member.add_roles(secret_role)
        await ctx.send(f"✅ Added hitter role to {member.mention}.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to add roles.")
    except Exception as e:
        await ctx.send(f"Error adding role: {e}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def removehitter(ctx, member: discord.Member):
    secret_role = get_secret_role(ctx.guild)
    if secret_role is None:
        await ctx.send("Secret role not found.")
        return
    if secret_role not in member.roles:
        await ctx.send(f"{member.mention} does not have the hitter role.")
        return
    try:
        await member.remove_roles(secret_role)
        await ctx.send(f"✅ Removed hitter role from {member.mention}.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to remove roles.")
    except Exception as e:
        await ctx.send(f"Error removing role: {e}")

# Run with token from Railway environment variable
bot.run(os.environ.get("DISCORD_TOKEN"))
