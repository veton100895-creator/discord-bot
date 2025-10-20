import discord
from discord.ext import commands
from discord import app_commands
import os
import io
from dotenv import load_dotenv
import asyncio
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

# Configuration des intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

class TicketModal(discord.ui.Modal, title="Create a ticket"):
    name = discord.ui.TextInput(
        label="Subject",
        placeholder="Enter your ticket subject",
        required=True,
        max_length=100
    )
    description = discord.ui.TextInput(
        label="Description",
        placeholder="Describe your issue in detail",
        required=True,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Vérifier si la catégorie Support existe
        category = discord.utils.get(interaction.guild.categories, name="Support Tickets")
        if not category:
            category = await interaction.guild.create_category("Support Tickets")
        
        # Trouver le rôle Staff
        staff_role = discord.utils.get(interaction.guild.roles, name="Staff")
        if not staff_role:
            staff_role = await interaction.guild.create_role(
                name="Staff",
                color=discord.Color.red(),
                mentionable=True,
                reason="Created for ticket system"
            )
        
        # Configurer les permissions
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                read_messages=False,
                send_messages=False
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_messages=True,
                attach_files=True,
                embed_links=True
            ),
            staff_role: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_messages=True,
                attach_files=True,
                embed_links=True
            ),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                attach_files=True,
                embed_links=True
            )
        }

        # Créer le salon
        channel = await category.create_text_channel(
            f"ticket-{interaction.user.name}",
            overwrites=overwrites,
            topic=f"Support ticket for {interaction.user.name} | Subject: {self.name.value}"
        )

        # Créer l'embed principal
        embed = discord.Embed(
            title=f"🎫 New Support Ticket",
            description=f"**From:** {interaction.user.mention}\n"
                      f"**Subject:** {self.name.value}\n\n"
                      f"**Description:**\n{self.description.value}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Ticket ID: {channel.name}")

        # Créer l'embed d'instructions
        instructions = discord.Embed(
            title="📝 Ticket Instructions",
            color=discord.Color.green()
        )
        instructions.add_field(
            name="👋 For the User",
            value="• Please be patient while waiting for staff\n"
                  "• Provide any additional information if needed\n"
                  "• Use `/attach` to add files if necessary",
            inline=False
        )
        instructions.add_field(
            name="👥 For Staff",
            value="• Use the buttons below to manage the ticket\n"
                  "• Close the ticket when resolved\n"
                  "• Remember to be professional and helpful",
            inline=False
        )

        # Envoyer les messages
        view = TicketView()
        await channel.send(f"{staff_role.mention} - New ticket from {interaction.user.mention}")
        await channel.send(embed=embed)
        await channel.send(embed=instructions, view=view)

        # Confirmation
        confirmation = discord.Embed(
            title="✅ Ticket Created",
            description=f"Your ticket has been created: {channel.mention}\nA staff member will assist you shortly.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=confirmation, ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.channel.name.startswith("ticket-"):
            return

        confirm_view = CloseConfirmView()
        await interaction.response.send_message(
            "Would you like to receive a transcript of the ticket?",
            view=confirm_view,
            ephemeral=True
        )

class CloseConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_transcript(self, channel):
        messages = []
        async for message in channel.history(limit=None, oldest_first=True):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            content = f"[{timestamp}] {message.author.name}: {message.content}"
            if message.attachments:
                content += "\nAttachments:\n"
                content += "\n".join([f"- {attachment.url}" for attachment in message.attachments])
            messages.append(content)
        return "\n".join(messages)

    @discord.ui.button(label="✅ Yes, with transcript", style=discord.ButtonStyle.success)
    async def close_with_transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        transcript = await self.create_transcript(interaction.channel)
        transcript_file = discord.File(
            io.StringIO(transcript),
            filename=f"transcript-{interaction.channel.name}.txt"
        )

        try:
            await interaction.user.send(
                "Here is your ticket transcript:",
                file=transcript_file
            )
            await interaction.response.send_message("Transcript sent to your DMs. Closing ticket...")
        except:
            await interaction.response.send_message("Unable to send transcript to DMs. Please check your privacy settings.")
            return

        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="❌ No, close directly", style=discord.ButtonStyle.danger)
    async def close_without_transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Closing ticket in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📝 Create ticket",
        style=discord.ButtonStyle.primary,
        custom_id="create_ticket"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal())

@bot.command(name="setup-tickets")
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    # Créer et envoyer le message de configuration
    embed = discord.Embed(
        title="🎫 Support System - Tickets",
        description="Welcome to our ticket support system!\n\n"
                  "📝 To create a ticket, click the button below.\n"
                  "⏱️ A staff member will respond as soon as possible.\n"
                  "🔒 Your ticket will be private and secure.",
        color=discord.Color.red()
    )
    embed.add_field(
        name="📌 Instructions",
        value="1. Click the 'Create ticket' button\n"
              "2. Fill out the form with your subject\n"
              "3. Describe your issue in detail\n"
              "4. Wait for a staff member's response",
        inline=False
    )
    embed.set_footer(text="Support - Tickets | One ticket per user")
    
    await ctx.send(embed=embed, view=TicketButton())
    await ctx.message.delete()

@bot.tree.command(name="membres", description="View member list")
async def membres(interaction: discord.Interaction):
    guild = interaction.guild
    online = sum(1 for m in guild.members if m.status != discord.Status.offline)
    
    embed = discord.Embed(
        title="📊 Member Statistics",
        color=discord.Color.red()
    )
    embed.add_field(
        name="Online Members",
        value=f"🟢 {online}/{len(guild.members)}",
        inline=False
    )
    
    roles_count = {}
    for member in guild.members:
        for role in member.roles:
            if role.name != "@everyone":
                roles_count[role.name] = roles_count.get(role.name, 0) + 1
    
    roles_text = "\n".join([f"• {role}: {count}" for role, count in roles_count.items()])
    if roles_text:
        embed.add_field(name="Roles", value=roles_text, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot is ready and logged in as {bot.user.name}")
    print("----------------------------------------")
    print(f"Connected to {len(bot.guilds)} servers")
    print(f"Serving {sum(guild.member_count for guild in bot.guilds)} users")
    print("----------------------------------------")
    await bot.change_presence(activity=discord.Game(name="Support Tickets | !help"))

# Lancer le bot avec le token depuis les variables d'environnement
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("⚠️ Error: No DISCORD_TOKEN found in environment variables!")
    exit(1)
bot.run(token)