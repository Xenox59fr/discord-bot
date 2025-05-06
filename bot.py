import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
import datetime
from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

CREDITS_FILE = "credits.json"

# Chargement des crédits depuis le fichier
def load_credits():
    if os.path.exists(CREDITS_FILE):
        with open(CREDITS_FILE, "r") as f:
            data = json.load(f)
            print("Crédits chargés depuis le fichier.")
            return data
    else:
        print("Aucun fichier de crédits trouvé, création d'un fichier vide.")
        return {}

user_credits = load_credits()
last_credit_time = {}

# Sauvegarde les crédits dans le fichier
def save_credits():
    with open(CREDITS_FILE, "w") as f:
        json.dump(user_credits, f, indent=4)
    print("Crédits sauvegardés dans le fichier.")

# Initialisation de l'utilisateur
def init_user(user_id):
    if user_id not in user_credits:
        user_credits[user_id] = {
            "solde": 100,
            "total_credits": 100,
            "last_daily": "1970-01-01T00:00:00+00:00"
        }
        save_credits()

# Ajouter des crédits
def add_credits(user_id, amount):
    init_user(user_id)
    user_credits[user_id]["solde"] += amount
    user_credits[user_id]["total_credits"] += amount
    save_credits()

# Retirer des crédits
def remove_credits(user_id, amount):
    init_user(user_id)
    user_credits[user_id]["solde"] = max(0, user_credits[user_id]["solde"] - amount)
    save_credits()

@bot.command()
async def credits(ctx):
    user_id = str(ctx.author.id)
    init_user(user_id)

    solde = user_credits[user_id]["solde"]
    await ctx.send(f"{ctx.author.mention}, tu as {solde} crédits.")

@bot.command()
async def daily(ctx):
    user_id = str(ctx.author.id)
    now = datetime.datetime.now(datetime.timezone.utc)

    init_user(user_id)

    last_claim = datetime.datetime.fromisoformat(user_credits[user_id]["last_daily"])
    elapsed = (now - last_claim).total_seconds()

    if elapsed >= 86400:
        add_credits(user_id, 50)
        user_credits[user_id]["last_daily"] = now.isoformat()
        save_credits()
        await ctx.send(f"{ctx.author.mention}, tu as reçu tes 50 crédits quotidiens ! 💰")
    else:
        remaining = int(86400 - elapsed)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60
        await ctx.send(f"{ctx.author.mention}, tu as déjà réclamé tes crédits quotidiens. Reviens dans {hours}h {minutes}m {seconds}s ⏳.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    now = datetime.datetime.utcnow()

    init_user(user_id)

    last_time = last_credit_time.get(user_id)
    if last_time is None or (now - last_time).total_seconds() >= 60:
        add_credits(user_id, 1)
        last_credit_time[user_id] = now

    await bot.process_commands(message)

bot.run(TOKEN)





