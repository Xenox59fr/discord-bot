import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

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

# Fonction bien indentée ici 👇
def save_credits():
    with open(CREDITS_FILE, "w") as f:
        json.dump(user_credits, f)

@bot.command()
async def credits(ctx):
    user_id = str(ctx.author.id)
    if user_id not in user_credits:
        user_credits[user_id] = {
            "solde": 100,
            "total_credits": 100,
            "last_daily": "1970-01-01T00:00:00+00:00"
        }
        save_credits()
    solde = user_credits[user_id]["solde"]
    await ctx.send(f"{ctx.author.mention}, tu as {solde} crédits.")



bot.run(TOKEN)  # lance le bot
