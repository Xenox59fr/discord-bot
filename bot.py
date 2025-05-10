import discord
from discord.ext import commands
from supabase import create_client, Client
import json
import random
import datetime
import os
from discord.ui import Button, View
from dotenv import load_dotenv
import threading
from flask import Flask

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Connexion Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Flask pour faire tourner le bot sur Render
app = Flask("")

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run).start()

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Chargement des cartes depuis un fichier JSON
with open("cards.json", "r", encoding="utf-8") as f:
    all_cards = json.load(f)

# Probabilités des raretés
rarity_probabilities = {
    "commun": 60,
    "rare": 25,
    "epique": 10,
    "legendaire": 4,
    "unique": 0.9,
    "collab": 0.1
}

rarity_emojis = {
    "commun": "⬜",
    "rare": "🟦",
    "epique": "🟪",
    "legendaire": "🟨",
    "unique": "🟥",
    "collab": "🟧"
}

rarity_colors = {
    "commun": 0xB0BEC5,
    "rare": 0x2196F3,
    "epique": 0x9C27B0,
    "legendaire": 0xFFD700,
    "unique": 0xE53935,
    "collab": 0xFF5722
}

# Fonction de sélection de rareté
def choisir_rarete():
    rand = random.uniform(0, 100)
    total = 0
    for rarete, chance in rarity_probabilities.items():
        total += chance
        if rand <= total:
            return rarete
    return "commun"

# Initialiser un utilisateur
def init_user(user_id):
    user = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if not user.data:
        supabase.table("users").insert([{
            "user_id": user_id,
            "credits": 100,
            "total_credits": 100,
            "last_daily": "1970-01-01T00:00:00+00:00",
            "cards_collected": 0
        }]).execute()

# Ajouter des crédits
def add_credits(user_id, amount):
    init_user(user_id)
    supabase.table("users").update({
        "credits": supabase.table("users").select("credits").eq("user_id", user_id).execute().data[0]["credits"] + amount,
        "total_credits": supabase.table("users").select("total_credits").eq("user_id", user_id).execute().data[0]["total_credits"] + amount
    }).eq("user_id", user_id).execute()

# Retirer des crédits
def remove_credits(user_id, amount):
    init_user(user_id)
    supabase.table("users").update({
        "credits": max(0, supabase.table("users").select("credits").eq("user_id", user_id).execute().data[0]["credits"] - amount)
    }).eq("user_id", user_id).execute()

# Commande !credits
@bot.command()
async def credits(ctx):
    user_id = str(ctx.author.id)
    init_user(user_id)
    user = supabase.table("users").select("credits").eq("user_id", user_id).execute()
    credits = user.data[0]["credits"]
    await ctx.send(f"{ctx.author.mention}, tu as {credits} crédits.")

# Commande !daily
@bot.command()
async def daily(ctx):
    user_id = str(ctx.author.id)
    now = datetime.datetime.now(datetime.timezone.utc)
    init_user(user_id)

    user = supabase.table("users").select("last_daily").eq("user_id", user_id).execute()
    last_claim = datetime.datetime.fromisoformat(user.data[0]["last_daily"])
    elapsed = (now - last_claim).total_seconds()

    if elapsed >= 86400:
        add_credits(user_id, 50)
        supabase.table("users").update({"last_daily": now.isoformat()}).eq("user_id", user_id).execute()
        await ctx.send(f"{ctx.author.mention}, tu as reçu tes 50 crédits quotidiens ! 💰")
    else:
        remaining = int(86400 - elapsed)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60
        await ctx.send(f"{ctx.author.mention}, tu as déjà réclamé tes crédits quotidiens. Reviens dans {hours}h {minutes}m {seconds}s ⏳.")

# Fonction pour choisir une rareté selon les chances
def tirer_rarete():
    rand = random.uniform(0, 100)
    cumulative = 0
    for rarity, data in rarity_probabilities.items():
        cumulative += data
        if rand <= cumulative:
            return rarity
    return "commun"

# Commande !buy
@bot.command()
async def buy(ctx, nombre: int = 1):
    user_id = str(ctx.author.id)
    init_user(user_id)

    result = supabase.table("users").select("credits").eq("user_id", user_id).execute()

    if result.data:
        credits = result.data[0]["credits"]
    else:
        credits = 0

    if credits < nombre:
        await ctx.send(f"{ctx.author.mention}, tu n'as pas assez de crédits pour acheter {nombre} pack(s) ❌.")
        return

    remove_credits(user_id, nombre)

    for _ in range(nombre):
        rarete = tirer_rarete()
        carte = random.choice([c for c in all_cards if c["rarity"] == rarete])
        embed = discord.Embed(
            title=f"{rarity_emojis[rarete]} Tu as tiré une carte !",
            description=f"**{carte['name']}**",
            color=rarity_colors[rarete]
        )
        embed.set_image(url=carte["image"])
        embed.set_footer(text=f"Rareté : {rarete.capitalize()} | Saison 0")
        await ctx.send(embed=embed)

        data = {
            "user_id": user_id,
            "card_id": carte["id"],
            "rarity": rarete,
            "season": 0
        }

        supabase.table("user_cards").insert(data).execute()

# Commande pour la collection
@bot.command()
async def collection(ctx):
    user_id = str(ctx.author.id)
    response = supabase.table("user_cards").select("*").eq("user_id", user_id).eq("season", 0).execute()
    cartes = response.data

    if not cartes:
        await ctx.send(f"{ctx.author.mention}, tu n'as aucune carte pour la Saison 0 📭")
        return

    class CollectionView(discord.ui.View):
        def __init__(self, cartes):
            super().__init__(timeout=None)
            self.cartes = cartes
            self.page = 0
            self.total_pages = len(cartes)

        def get_embed(self):
            carte = self.cartes[self.page]
            embed = discord.Embed(
                title=f"📘 Collection Saison 0 - {self.page + 1}/{self.total_pages}",
                description=f"**Carte ID :** `{carte['card_id']}`\n**Rareté :** {carte['rarity']}",
                color=rarity_colors[carte['rarity']]
            )
            if "image" in carte:
                embed.set_image(url=carte["image"])
            return embed

        @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
        async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.page > 0:
                self.page -= 1
                await interaction.response.edit_message(embed=self.get_embed(), view=self)
            else:
                await interaction.response.defer()

        @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
        async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.page < self.total_pages - 1:
                self.page += 1
                await interaction.response.edit_message(embed=self.get_embed(), view=self)
            else:
                await interaction.response.defer()

    view = CollectionView(cartes)
    await ctx.send(embed=view.get_embed(), view=view)

# Commande pour afficher le leaderboard
@bot.command()
async def leaderboard(ctx):
    response = supabase.table("users").select("*").order("total_credits", desc=True).limit(10).execute()
    users = response.data
    if not users:
        await ctx.send("Aucun joueur trouvé dans le classement.")
        return

    embed = discord.Embed(title="🏆 Classement des plus riches", color=0xFFD700)
    for i, user in enumerate(users, start=1):
        mention = f"<@{user['user_id']}>"
        embed.add_field(
            name=f"{i}. {mention}",
            value=f"💰 {user['total_credits']} crédits gagnés au total",
            inline=False
        )
    await ctx.send(embed=embed)



bot.run(TOKEN)







