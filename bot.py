import discord
from discord.ext import commands
from discord.ui import View, Button
import os

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

WELCOME_CHANNEL_ID = 1392933458107437056  # Replace with your real welcome channel ID
EMBED_IMAGE_URL = "https://cdn.discordapp.com/attachments/1392914867241091204/1393443309329973352/Choose_Wisely_2.png?ex=687330b5&is=6871df35&hm=49c0d9aa8f757145c671ebcd5a78a75e042a6ca6c49e51dad6615de4ba45496c&"  # Replace with a valid image URL

class ChooseYourFateView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="I want to be poor", style=discord.ButtonStyle.danger)
    async def poor_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        guild = interaction.guild

        member_roles = [r for r in guild.roles if r.name == "Member"]
        if len(member_roles) < 2:
            await interaction.response.send_message("❌ Error: Member roles misconfigured.", ephemeral=True)
            return

        real_member_role, hitter_role = sorted(member_roles, key=lambda r: r.position, reverse=True)

        if hitter_role in member.roles:
            await interaction.response.send_message("⚠️ You are a hitter and cannot be banned.", ephemeral=True)
            return

        await interaction.message.delete()
        await interaction.response.send_message(f"👋 {member.mention} has chosen to be poor and is now banned.", ephemeral=False)
        await member.ban(reason="Chose to be poor")

    @discord.ui.button(label="I want to be rich", style=discord.ButtonStyle.primary)
    async def rich_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        guild = interaction.guild

        member_roles = [r for r in guild.roles if r.name == "Member"]
        if len(member_roles) < 2:
            await interaction.response.send_message("❌ Error: Could not find both member roles.", ephemeral=True)
            return

        real_member_role, hitter_role = sorted(member_roles, key=lambda r: r.position, reverse=True)

        if hitter_role in member.roles:
            await interaction.response.send_message("⚠️ You are already a hitter.", ephemeral=True)
            return

        if real_member_role not in member.roles:
            await interaction.response.send_message("❌ You must be a member to choose.", ephemeral=True)
            return

        await member.remove_roles(real_member_role)
        await member.add_roles(hitter_role)

        await interaction.message.delete()
        await interaction.response.send_message(f"✅ Welcome {member.mention}! You chose wisely.", ephemeral=False)

        welcome_channel = guild.get_channel(WELCOME_CHANNEL_ID)
        if welcome_channel:
            await welcome_channel.send(f"🎉 Welcome {member.mention}, our newest hitter!")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
async def ishitter(ctx, member: discord.Member):
    roles = [r for r in ctx.guild.roles if r.name == "Member"]
    if len(roles) < 2:
        await ctx.send("❌ Roles are not set correctly.")
        return
    real_member_role, hitter_role = sorted(roles, key=lambda r: r.position, reverse=True)
    if hitter_role in member.roles:
        await ctx.send(f"✅ {member.mention} is a hitter.")
    else:
        await ctx.send(f"❌ {member.mention} is NOT a hitter.")

@bot.command()
async def addhitter(ctx, member: discord.Member):
    roles = [r for r in ctx.guild.roles if r.name == "Member"]
    if len(roles) < 2:
        await ctx.send("❌ Roles are not set correctly.")
        return
    real_member_role, hitter_role = sorted(roles, key=lambda r: r.position, reverse=True)
    await member.remove_roles(real_member_role)
    await member.add_roles(hitter_role)
    await ctx.send(f"✅ {member.mention} has been added as a hitter.")

@bot.command()
async def removehitter(ctx, member: discord.Member):
    roles = [r for r in ctx.guild.roles if r.name == "Member"]
    if len(roles) < 2:
        await ctx.send("❌ Roles are not set correctly.")
        return
    real_member_role, hitter_role = sorted(roles, key=lambda r: r.position, reverse=True)
    await member.remove_roles(hitter_role)
    await member.add_roles(real_member_role)
    await ctx.send(f"✅ {member.mention} has been removed as a hitter.")

@bot.command()
async def chooseyourfate(ctx):
    embed = discord.Embed(title="Choose Your Fate", description="Make your choice wisely.", color=0x3498db)
    embed.set_image(url=EMBED_IMAGE_URL)
    await ctx.send(embed=embed, view=ChooseYourFateView())

bot.run(os.getenv("DISCORD_TOKEN"))
