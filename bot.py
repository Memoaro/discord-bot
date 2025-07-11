import os
import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import Embed, Interaction

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# === CONFIGURATION ===
SECRET_ROLE_NAME = "Member"  # Secret "hitter" role (lower one)
WELCOME_CHANNEL_ID = 1392933458107437056  # Replace with your real welcome channel ID
WELCOME_MESSAGE = "Welcome hitter, your story of rags to riches starts here. Check #how-to-mm for tips on how to hit, and remember all of these channels are disguised as staff channels. Good luck."  # Custom welcome message
EMBED_IMAGE_URL = "https://ibb.co/p6VQGwGW"  # Replace with your direct image URL

# === BOT EVENTS ===
@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")


# === BASIC COMMANDS ===
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


@bot.command()
async def ishitter(ctx, member: discord.Member):
    secret_role = discord.utils.get(ctx.guild.roles, name=SECRET_ROLE_NAME)
    if secret_role in member.roles:
        await ctx.send(f"✅ {member.mention} **is a hitter.**")
    else:
        await ctx.send(f"❌ {member.mention} is NOT a hitter.")


@bot.command()
@commands.has_permissions(manage_roles=True)
async def addhitter(ctx, member: discord.Member):
    secret_role = discord.utils.get(ctx.guild.roles, name=SECRET_ROLE_NAME)
    if not secret_role:
        await ctx.send("❌ Secret role not found.")
        return
    if secret_role in member.roles:
        await ctx.send(f"{member.mention} already has the secret role.")
        return
    await member.add_roles(secret_role)
    await ctx.send(f"✅ {member.mention} has been added as a hitter.")


@bot.command()
@commands.has_permissions(manage_roles=True)
async def removehitter(ctx, member: discord.Member):
    secret_role = discord.utils.get(ctx.guild.roles, name=SECRET_ROLE_NAME)
    if not secret_role:
        await ctx.send("❌ Secret role not found.")
        return
    if secret_role not in member.roles:
        await ctx.send(f"{member.mention} does not have the secret role.")
        return
    await member.remove_roles(secret_role)
    await ctx.send(f"✅ {member.mention} has been removed as a hitter.")


# === CHOOSE YOUR FATE BUTTON VIEW ===
class ChooseYourFateView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="I want to be poor", style=discord.ButtonStyle.danger)
    async def poor_button(self, button: Button, interaction: Interaction):
        guild = interaction.guild
        member = interaction.user
        secret_role = discord.utils.get(guild.roles, name=SECRET_ROLE_NAME)

        if secret_role in member.roles:
            await interaction.response.send_message("You're already a hitter. I can't ban you. 😉", ephemeral=True)
            return

        try:
            await interaction.user.ban(reason="Chose to be poor via !chooseyourfate")
            await interaction.message.delete()
        except Exception:
            await interaction.response.send_message(
                "❌ I couldn't ban you. Please check my permissions.", ephemeral=True)

    @discord.ui.button(label="I want to be rich", style=discord.ButtonStyle.success)
    async def rich_button(self, button: Button, interaction: Interaction):
        guild = interaction.guild
        member = interaction.user
        secret_role = discord.utils.get(guild.roles, name=SECRET_ROLE_NAME)

        if not secret_role:
            await interaction.response.send_message("❌ Secret role not found.", ephemeral=True)
            return

        if secret_role in member.roles:
            await interaction.response.send_message("You're already a hitter. 🤑", ephemeral=True)
            return  # DO NOT remove embed

        try:
            await member.add_roles(secret_role)
        except Exception:
            await interaction.response.send_message(
                "❌ I couldn't add the role. Check my permissions.", ephemeral=True)
            return

        welcome_channel = guild.get_channel(WELCOME_CHANNEL_ID)
        if welcome_channel:
            await welcome_channel.send(f"{member.mention} {WELCOME_MESSAGE}")

        await interaction.message.delete()  # Remove embed for successful new hitters


# === FATE COMMAND ===
@bot.command()
async def chooseyourfate(ctx):
    embed = Embed(title="Choose Your Fate", color=discord.Color.purple())
    embed.set_image(url=EMBED_IMAGE_URL)

    view = ChooseYourFateView()
    await ctx.send(embed=embed, view=view)


# === RUN BOT USING RAILWAY VARIABLE ===
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ ERROR: DISCORD_TOKEN environment variable not set.")
else:
    bot.run(TOKEN)
