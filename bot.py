import discord
from discord.ext import tasks
from discord import app_commands
import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

TOKEN = load_dotenv()
PARIS_TZ = ZoneInfo("Europe/Paris")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ====== CONFIGURATION ======
config = {
    "mudae_minute": 58,
    "claim_hours": [2, 5, 8, 11, 14, 17, 20, 23],
    "channel_id": None,
    "mention_id": None,
    "mudae_message": "C'est l'heure des rolls !",
    "claim_message": "Le claim a été reset à dans 3 heures"
}

# ====== BOT READY ======
@client.event
async def on_ready():
    await tree.sync()
    print(f"Connecté en tant que {client.user}")
    reminder_loop.start()

# ====== /rappel mudae ======
@tree.command(name="rappel_mudae", description="Configurer le rappel horaire")
@app_commands.describe(
    minute="Minute du rappel (0-59)",
    salon="Salon où envoyer le message",
    mention="Utilisateur ou rôle à mentionner",
    message="Message du rappel horaire"
)
async def rappel_mudae(
    interaction: discord.Interaction,
    minute: int,
    salon: discord.TextChannel,
    mention: discord.Role | discord.Member,
    message: str
):
    if minute < 0 or minute > 59:
        await interaction.response.send_message("Minute invalide (0-59).", ephemeral=True)
        return

    config["mudae_minute"] = minute
    config["channel_id"] = salon.id
    config["mention_id"] = mention.id
    config["mudae_message"] = message

    await interaction.response.send_message(
        f"Rappel horaire configuré à {minute} min dans {salon.mention} ✅"
    )

# ====== /rappel claim ======
@tree.command(name="rappel_claim", description="Configurer les heures spéciales")
@app_commands.describe(
    heures="Liste d'heures séparées par des virgules (ex: 2,5,8,11)",
    message="Message du claim"
)
async def rappel_claim(interaction: discord.Interaction, heures: str, message: str):
    try:
        hours_list = [int(h.strip()) for h in heures.split(",")]

        for h in hours_list:
            if h < 0 or h > 23:
                raise ValueError

        config["claim_hours"] = hours_list
        config["claim_message"] = message

        await interaction.response.send_message(
            f"✅ Heures configurées : {', '.join(map(str, hours_list))}"
        )

    except:
        await interaction.response.send_message(
            "Format invalide. Exemple : 2,5,8,11,14",
            ephemeral=True
        )

# ====== BOUCLE PRINCIPALE ======
@tasks.loop(minutes=1)
async def reminder_loop():
    if not config["channel_id"]:
        return

    now = datetime.datetime.now(PARIS_TZ)
    channel = client.get_channel(config["channel_id"])

    if not channel:
        return

    mention_text = f"<@{config['mention_id']}>" if config["mention_id"] else ""

    # rappel horaire
    if now.minute == config["mudae_minute"]:
        await channel.send(f"{mention_text} {config['mudae_message']}")

    # rappel heures spécifiques
    if now.minute == 0 and now.hour in config["claim_hours"]:
        await channel.send(f"{mention_text} {config['claim_message']}")

client.run(TOKEN)