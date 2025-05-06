import discord
from discord.ext import commands
import sqlite3
import os
import datetime
from dotenv import load_dotenv
from flask import Flask
import threading

# Flask pour le "ping" de Render
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

# Discord token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Connexion base de données SQLite
conn = sqlite3.connect("/data/credits.db")
cursor = conn.cursor()

# Création de la table si elle n'existe pas
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    solde INTEGER DEFAULT 100,
    total_credits INTEGER DEFAULT 100,
    last_daily TEXT DEFAULT '1970-01-01T00:00:00+00:00'
)
""")
conn.commit()

last_credit_time = {}

# Initialiser un utilisateur
def init_user(user_id):
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (user_id) VALUES (?)",
            (user_id,)
        )
        conn.commit()

# Ajouter des crédits
def add_credits(user_id, amount):
    init_user(user_id)
    cursor.execute("""
        UPDATE users
        SET solde = solde + ?, total_credits = total_credits + ?
        WHERE user_id = ?
    """, (amount, amount, user_id))
    conn.commit()

# Retirer des crédits
def remove_credits(user_id, amount):
    init_user(user_id)
    cursor.execute("""
        UPDATE users
        SET solde = MAX(solde - ?, 0)
        WHERE user_id = ?
    """, (amount, user_id))
    conn.commit()

# Commande !credits
@bot.command()
async def credits(ctx):
    user_id = str(ctx.author.id)
    init_user(user_id)
    cursor.execute("SELECT solde FROM users WHERE user_id = ?", (user_id,))
    solde = cursor.fetchone()[0]
    await ctx.send(f"{ctx.author.mention}, tu as {solde} crédits.")

# Commande !daily
@bot.command()
async def daily(ctx):
    user_id = str(ctx.author.id)
    now = datetime.datetime.now(datetime.timezone.utc)
    init_user(user_id)

    cursor.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
    last_claim = datetime.datetime.fromisoformat(cursor.fetchone()[0])
    elapsed = (now - last_claim).total_seconds()

    if elapsed >= 86400:
        add_credits(user_id, 50)
        cursor.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (now.isoformat(), user_id))
        conn.commit()
        await ctx.send(f"{ctx.author.mention}, tu as reçu tes 50 crédits quotidiens ! 💰")
    else:
        remaining = int(86400 - elapsed)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60
        await ctx.send(f"{ctx.author.mention}, tu as déjà réclamé tes crédits quotidiens. Reviens dans {hours}h {minutes}m {seconds}s ⏳.")

# Gagner 1 crédit chaque minute
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






