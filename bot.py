import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents et setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Fichier pour stocker les crédits
CREDITS_FILE = "credits.json"

# Chargement des crédits depuis le fichier JSON
def load_credits():
   
if os.path.exists(CREDITS_FILE):
    with open(CREDITS_FILE, "r") as f:
        user_credits = json.load(f)
else:
    user_credits = {}
# Sauvegarde des crédits dans le fichier JSON
def save_credits():
    with open(CREDITS_FILE, "w") as f:
        json.dump(user_credits, f)

user_credits = {}  # ✅ nouveau nom

@bot.command()
async def credits(ctx):
    user_id = str(ctx.author.id)
    if user_id not in user_credits:
        user_credits[user_id] = 100  # crédits de départ
        save_credits()

    await ctx.send(f"{ctx.author.mention}, tu as {user_credits[user_id]} crédits.")


bot.run(TOKEN)  # lance le bot
