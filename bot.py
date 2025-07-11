import os
import discord
from discord.ext import commands

# Exact secret role name here (both hitter role and duplicate "real" role share this name)
SECRET_ROLE_NAME = "Member"

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def get_secret_roles(guild):
    """Return list of all roles with the SECRET_ROLE_NAME"""
    return [role for role in guild.roles if role.name == SECRET_ROLE_NAME]

def get_secret_role(guild):
    """Return single secret role (lowest position) or None"""
    roles = get_secret_roles(guild)
    if roles:
        # Sort by position ascending (lowest is hitter role)
        return sorted(roles, key=lambda r: r.position)[0]
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

@bot.command()
@commands.has_permissions(manage_roles=True)
async def fixroles(ctx, channel: discord.TextChannel):
    """
    For everyone who can view the channel, if they have 2 'Member' roles,
    remove the higher position one (the real member role), keep the lower (hitter).
    """
    secret_roles = get_secret_roles(ctx.guild)
    if len(secret_roles) < 2:
        await ctx.send("There are not two roles with the secret role name to fix.")
        return

    removed_count = 0
    async with ctx.typing():
        for member in channel.members:
            # Find roles the member has with that name
            member_secret_roles = [r for r in member.roles if r.name == SECRET_ROLE_NAME]
            if len(member_secret_roles) >= 2:
                # Sort by position descending: higher position is real member role to remove
                member_secret_roles_sorted = sorted(member_secret_roles, key=lambda r: r.position, reverse=True)
                role_to_remove = member_secret_roles_sorted[0]
                try:
                    await member.remove_roles(role_to_remove)
                    removed_count += 1
                    print(f"Removed role {role_to_remove} from {member}")
                except discord.Forbidden:
                    await ctx.send(f"Missing permission to remove role from {member.mention}")
                    return
                except Exception as e:
                    await ctx.send(f"Error removing role from {member.mention}: {e}")
                    return

    await ctx.send(f"✅ Fixed roles for {removed_count} members in {channel.mention}.")

bot.run(os.environ.get("DISCORD_TOKEN"))
