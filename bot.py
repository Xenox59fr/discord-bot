import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

CREDITS_FILE = "credits.json"

# Chargement des crédits depuis le fichier
if os.path.exists(CREDITS_FILE):
    with open(CREDITS_FILE, "r") as f:
        user_credits = json.load(f)
else:
    user_credits = {}

last_credit_time = {}

# Sauvegarde les crédits dans le fichier
def save_credits():
    with open(CREDITS_FILE, "w") as f:
        json.dump(user_credits, f, indent=4)

@bot.command()
async def credits(ctx):
    user_id = str(ctx.author.id)

    if user_id not in user_credits:
        # Donne 100 crédits de départ uniquement aux nouveaux
        user_credits[user_id] = {
            "solde": 100,
            "total_credits": 100,
            "last_daily": "1970-01-01T00:00:00+00:00"
        }
        save_credits()

    # Récupère le solde actuel
    solde = user_credits[user_id]["solde"]
    await ctx.send(f"{ctx.author.mention}, tu as {solde} crédits.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    now = datetime.datetime.utcnow()

    # Initialise les crédits si le user est nouveau
    if user_id not in user_credits:
        user_credits[user_id] = {
            "solde": 100,
            "total_credits": 100,
            "last_daily": "1970-01-01T00:00:00+00:00"
        }

    # Vérifie si 60 secondes sont passées depuis le dernier crédit donné
    last_time = last_credit_time.get(user_id)
    if last_time is None or (now - last_time).total_seconds() >= 60:
        user_credits[user_id]["solde"] += 1
        user_credits[user_id]["total_credits"] += 1
        last_credit_time[user_id] = now
        save_credits()

    # Pour que les commandes (ex: !credits) soient traitées
    await bot.process_commands(message)

bot.run(TOKEN)

