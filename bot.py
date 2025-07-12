import os
import discord
from discord.ext import commands
from discord.ui import View, button, Button

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

SECRET_ROLE_NAME = "Member"  # Your secret hitter role (lower one)
PUBLIC_ROLE_NAME = "Member"  # The public-facing member role
WELCOME_CHANNEL_ID = 1392933458107437056  # Replace with actual channel ID
EMBED_IMAGE_URL = "https://cdn.discordapp.com/attachments/1392914867241091204/1393428926906368134/OIP.png?ex=68732350&is=6871d1d0&hm=88a24fe53aaff79dfcdf03c6c4b57ce091d3a5f0a652e2c5d4abb39847e88b50&"  # Replace with a real image link


def get_role_by_name(guild, name):
    matches = [role for role in guild.roles if role.name == name]
    return sorted(matches, key=lambda r: r.position)[-1] if matches else None


class ChooseYourFateView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="I want to be poor", style=discord.ButtonStyle.danger, custom_id="poor")
    async def poor_button(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        member = interaction.user
        secret_role = get_role_by_name(guild, SECRET_ROLE_NAME)

        if secret_role in member.roles:
            await interaction.response.send_message("You’re already a hitter. You may stay. 😈", ephemeral=True)
            return

        await interaction.response.send_message("You chose poorly. 💀", ephemeral=True)
        await member.ban(reason="Chose to be poor")

    @button(label="I want to be rich", style=discord.ButtonStyle.success, custom_id="rich")
    async def rich_button(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        member = interaction.user
        secret_role = get_role_by_name(guild, SECRET_ROLE_NAME)
        public_role = get_role_by_name(guild, PUBLIC_ROLE_NAME)

        if secret_role in member.roles:
            await interaction.response.send_message("You're already a hitter. 🕵️", ephemeral=True)
            return

        if public_role in member.roles:
            await member.remove_roles(public_role)

        if secret_role:
            await member.add_roles(secret_role)

        embed = discord.Embed(
            title="Welcome to the dark side. 🌌",
            description=f"{member.mention} has chosen to be rich.",
            color=discord.Color.green()
        )
        embed.set_image(url=EMBED_IMAGE_URL)

        welcome_channel = guild.get_channel(WELCOME_CHANNEL_ID)
        if welcome_channel:
            await welcome_channel.send(embed=embed)

        await interaction.message.delete()
        await interaction.response.send_message("Welcome to the elite. 💼", ephemeral=True)


@bot.command()
async def chooseyourfate(ctx):
    embed = discord.Embed(
        title="Choose your fate wisely...",
        description="You must decide your path.",
        color=discord.Color.purple()
    )
    embed.set_image(url=EMBED_IMAGE_URL)

    view = ChooseYourFateView()
    await ctx.send(embed=embed, view=view)


@bot.command()
async def ishitter(ctx, member: discord.Member):
    role = get_role_by_name(ctx.guild, SECRET_ROLE_NAME)
    if role in member.roles:
        await ctx.send(f"✅ {member.mention} is a hitter.")
    else:
        await ctx.send(f"❌ {member.mention} is NOT a hitter.")


@bot.command()
async def addhitter(ctx, member: discord.Member):
    role = get_role_by_name(ctx.guild, SECRET_ROLE_NAME)
    if not role:
        await ctx.send("Secret role not found.")
        return

    await member.add_roles(role)
    await ctx.send(f"✅ {member.mention} has been added as a hitter.")


@bot.command()
async def removehitter(ctx, member: discord.Member):
    role = get_role_by_name(ctx.guild, SECRET_ROLE_NAME)
    if not role:
        await ctx.send("Secret role not found.")
        return

    await member.remove_roles(role)
    await ctx.send(f"✅ {member.mention} has been removed as a hitter.")


@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms")


bot.run(os.getenv("DISCORD_TOKEN"))
