import discord
from discord.ext import commands
import json
import os
from flask import Flask
from threading import Thread

# --------- Flask Web Server to Keep Alive ---------
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --------- Discord Bot Setup ---------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

HITTERS_FILE = "hitters.json"

# Load hitters from file or create empty set
if os.path.exists(HITTERS_FILE):
    with open(HITTERS_FILE, "r") as f:
        hitters = set(json.load(f))
else:
    hitters = set()

def save_hitters():
    with open(HITTERS_FILE, "w") as f:
        json.dump(list(hitters), f)

def get_secret_member_role(guild: discord.Guild):
    roles_named_member = [r for r in guild.roles if r.name == "Member"]
    if len(roles_named_member) < 2:
        return None
    # Return the lowest-positioned one = secret member role
    return sorted(roles_named_member, key=lambda r: r.position)[0]

def get_real_member_role(guild: discord.Guild):
    roles_named_member = [r for r in guild.roles if r.name == "Member"]
    if len(roles_named_member) < 2:
        return None
    # Return the highest-positioned one = real/public member role
    return sorted(roles_named_member, key=lambda r: r.position, reverse=True)[0]

async def remove_old_member_roles(member: discord.Member, secret_role: discord.Role):
    for role in member.roles:
        if role.name == "Member" and role != secret_role:
            try:
                await member.remove_roles(role)
                print(f"Removed old 'Member' role from {member.display_name}")
            except discord.Forbidden:
                print(f"⚠️ Missing permissions to remove role {role.name} from {member.display_name}")

async def sync_hitter_roles(guild: discord.Guild):
    secret_role = get_secret_member_role(guild)
    real_role = get_real_member_role(guild)
    if not secret_role:
        print("⚠️ Secret 'Member' role not found for syncing.")
        return

    print(f"🔄 Syncing roles in guild '{guild.name}'...")

    async for member in guild.fetch_members(limit=None):
        has_secret_role = secret_role in member.roles
        is_hitter = member.id in hitters

        # Auto-add members who already have the secret role
        if has_secret_role and member.id not in hitters:
            hitters.add(member.id)
            print(f"Detected hitter with secret role: {member.display_name}")

        # Ensure correct member role
        has_any_member_role = any(r.name == "Member" for r in member.roles)

        if is_hitter and not has_secret_role:
            try:
                await remove_old_member_roles(member, secret_role)
                await member.add_roles(secret_role)
                print(f"✅ Added secret role to hitter {member.display_name}")
            except discord.Forbidden:
                print(f"❌ Missing permission to update hitter roles for {member.display_name}")
        elif not is_hitter and has_secret_role:
            try:
                await member.remove_roles(secret_role)
                if real_role:
                    await member.add_roles(real_role)
                    print(f"✅ Removed secret role and re-added public role to {member.display_name}")
                else:
                    print(f"⚠️ No public Member role found to reassign to {member.display_name}")
            except discord.Forbidden:
                print(f"❌ Missing permission to update non-hitter roles for {member.display_name}")
        elif not has_secret_role and has_any_member_role:
            # Fix for general members not in hitters
            try:
                await remove_old_member_roles(member, secret_role)
                await member.add_roles(secret_role)
                print(f"🛠️ Corrected role for non-hitter {member.display_name}")
            except discord.Forbidden:
                print(f"❌ Could not correct roles for {member.display_name}")

    save_hitters()

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    for guild in bot.guilds:
        await sync_hitter_roles(guild)
    print("✅ Role sync complete.")

# --------- Commands ---------

@bot.command(name='ping')
async def ping_cmd(ctx):
    await ctx.send("Pong!")

@bot.command(name='addhitter')
@commands.has_permissions(administrator=True)
async def add_hitter_cmd(ctx, member: discord.Member):
    if member.id in hitters:
        await ctx.send(f"{member.display_name} is already a hitter.")
        return

    hitters.add(member.id)
    save_hitters()

    secret_role = get_secret_member_role(ctx.guild)
    if secret_role:
        try:
            await remove_old_member_roles(member, secret_role)
            await member.add_roles(secret_role)
            await ctx.send(f"{member.display_name} added as a hitter, secret role given, and old 'Member' role removed.")
        except discord.Forbidden:
            await ctx.send(f"⚠️ Failed to add secret role to {member.display_name} (missing permissions).")
    else:
        await ctx.send("⚠️ Secret 'Member' role not found. Please create two roles named 'Member'.")

@bot.command(name='removehitter')
@commands.has_permissions(administrator=True)
async def remove_hitter_cmd(ctx, member: discord.Member):
    if member.id not in hitters:
        await ctx.send(f"{member.display_name} is not on the hitter list.")
        return

    hitters.remove(member.id)
    save_hitters()

    secret_role = get_secret_member_role(ctx.guild)
    real_role = get_real_member_role(ctx.guild)

    if secret_role:
        try:
            await member.remove_roles(secret_role)
            msg = f"{member.display_name} removed from hitters and secret role removed."
            if real_role:
                await member.add_roles(real_role)
                msg += " Real Member role re-added."
            await ctx.send(msg)
        except discord.Forbidden:
            await ctx.send(f"⚠️ Failed to update roles for {member.display_name} (missing permissions).")
    else:
        await ctx.send("⚠️ Secret 'Member' role not found. Please create two roles named 'Member'.")

@bot.command(name='listhitters')
@commands.has_permissions(administrator=True)
async def list_hitters_cmd(ctx):
    if not hitters:
        await ctx.send("No hitters currently.")
        return

    names = []
    for user_id in hitters:
        user = bot.get_user(user_id)
        if user:
            names.append(user.name)
        else:
            names.append(f"Unknown User ({user_id})")

    await ctx.send("Hitters: " + ", ".join(names))

@bot.command(name='is_hitter')
async def is_hitter_cmd(ctx, member: discord.Member):
    if member.id in hitters:
        await ctx.send(f"✅ {member.display_name} is a hitter.")
    else:
        await ctx.send(f"❌ {member.display_name} is not a hitter.")

# Handle permission errors nicely
@add_hitter_cmd.error
@remove_hitter_cmd.error
@list_hitters_cmd.error
async def on_admin_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    else:
        raise error

# --------- Start the webserver and bot ---------
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
