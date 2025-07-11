import discord
from discord.ext import commands
from discord.ui import Button, View
import os

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True
intents.presences = False

bot = commands.Bot(command_prefix="!", intents=intents)

SECRET_ROLE_NAME = "Member"  # The secret lower member role name
WELCOME_CHANNEL_ID = 1392933458107437056  # Put your welcome channel ID here
WELCOME_MESSAGE = "Welcome hitter, your story of rags to riches starts here. Check #how-to-mm for tips on how to hit, and remember all of these channels are disguised as staff channels. Good luck."  # Customize your welcome message here
EMBED_IMAGE_URL = "<blockquote class="imgur-embed-pub" lang="en" data-id="a/dw3wOmC" data-context="false" ><a href="//imgur.com/a/dw3wOmC"></a></blockquote><script async src="//s.imgur.com/min/embed.js" charset="utf-8"></script>"  # Put your embed image URL here

def get_secret_role(guild):
    roles = [r for r in guild.roles if r.name == SECRET_ROLE_NAME]
    if len(roles) >= 2:
        # Return the lower one by position (secret role)
        return sorted(roles, key=lambda r: r.position)[-1]
    elif len(roles) == 1:
        return roles[0]
    else:
        return None

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

@bot.command()
async def ishitter(ctx, member: discord.Member):
    secret_role = get_secret_role(ctx.guild)
    if not secret_role:
        await ctx.send("Secret role not found.")
        return

    if secret_role in member.roles:
        await ctx.send(f"✅ {member.mention} is a hitter.")
    else:
        await ctx.send(f"❌ {member.mention} is NOT a hitter.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def addhitter(ctx, member: discord.Member):
    secret_role = get_secret_role(ctx.guild)
    if not secret_role:
        await ctx.send("Secret role not found.")
        return

    await member.add_roles(secret_role)
    await ctx.send(f"✅ {member.mention} has been added as a hitter.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def removehitter(ctx, member: discord.Member):
    secret_role = get_secret_role(ctx.guild)
    if not secret_role:
        await ctx.send("Secret role not found.")
        return

    await member.remove_roles(secret_role)
    await ctx.send(f"✅ {member.mention} has been removed as a hitter.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def fixroles(ctx, channel: discord.TextChannel):
    secret_role = get_secret_role(ctx.guild)
    if not secret_role:
        await ctx.send("Secret role not found.")
        return

    # Identify all members with access to the channel
    members_with_access = [m for m in ctx.guild.members if channel.permissions_for(m).read_messages]

    count_fixed = 0
    for member in members_with_access:
        # Get all "Member" roles (by name) they have
        member_roles = [r for r in member.roles if r.name == SECRET_ROLE_NAME]
        if len(member_roles) > 1:
            # Sort by position (highest role first)
            sorted_roles = sorted(member_roles, key=lambda r: r.position, reverse=True)
            highest = sorted_roles[0]
            lowest = sorted_roles[-1]

            # Remove the highest (the "real" member role)
            if highest != lowest:
                await member.remove_roles(highest)
                count_fixed += 1

    await ctx.send(f"✅ Fixed roles for {count_fixed} members in {channel.mention}.")

# The view for the buttons in !chooseyourfate
class ChooseYourFateView(View):
    def __init__(self, secret_role, welcome_channel, welcome_message):
        super().__init__(timeout=None)  # No timeout, persistent until bot restarts
        self.secret_role = secret_role
        self.welcome_channel = welcome_channel
        self.welcome_message = welcome_message

    @discord.ui.button(label="I want to be poor", style=discord.ButtonStyle.danger)
    async def poor_button(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.user.ban(reason="Chose to be poor.")
            await interaction.response.send_message("You chose to be poor and have been banned.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban you.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error banning user: {e}", ephemeral=True)

    @discord.ui.button(label="I want to be rich", style=discord.ButtonStyle.success)
    async def rich_button(self, interaction: discord.Interaction, button: Button):
        member = interaction.user
        if self.secret_role not in member.roles:
            try:
                await member.add_roles(self.secret_role)
                await interaction.response.send_message("You are now rich! Welcome!", ephemeral=True)
                await self.welcome_channel.send(f"{member.mention} {self.welcome_message}")
            except Exception as e:
                await interaction.response.send_message(f"Error giving role or sending welcome message: {e}", ephemeral=True)
        else:
            await interaction.response.send_message("You already have the rich role.", ephemeral=True)

@bot.command()
async def chooseyourfate(ctx):
    secret_role = get_secret_role(ctx.guild)
    if not secret_role:
        await ctx.send("Secret role not found.")
        return

    welcome_channel = ctx.guild.get_channel(WELCOME_CHANNEL_ID)
    if not welcome_channel:
        await ctx.send("Welcome channel not found.")
        return

    embed = discord.Embed(title="Choose Your Fate",
                          description="Are you ready to decide your destiny?",
                          color=discord.Color.blue())
    embed.set_image(url=EMBED_IMAGE_URL)

    view = ChooseYourFateView(secret_role, welcome_channel, WELCOME_MESSAGE)

    await ctx.send(embed=embed, view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
