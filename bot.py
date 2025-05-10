import discord
from discord.ext import commands
import os
import datetime
from dotenv import load_dotenv
from flask import Flask
import threading
from supabase import create_client, Client
import random
import json
from discord.ui import Button, View
import math
from discord import Embed


last_credit_time = {}


# Flask pour le "ping" de Render
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

# Chargement du token et des variables d'environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Connexion à Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Initialiser un utilisateur
def init_user(user_id):
    # Vérifier si l'utilisateur existe déjà dans la base de données Supabase
    user = supabase.table('users').select('*').eq('user_id', user_id).execute()
    if not user.data:
        # Si l'utilisateur n'existe pas, on l'ajoute avec les crédits de départ
        supabase.table('users').insert([{
            'user_id': user_id,
            'solde': 100,
            'total_credits': 100,
            'last_daily': '1970-01-01T00:00:00+00:00'
        }]).execute()

# Ajouter des crédits
def add_credits(user_id, amount):
    init_user(user_id)
    supabase.table('users').update({
        'solde': supabase.table('users').select('solde').eq('user_id', user_id).execute().data[0]['solde'] + amount,
        'total_credits': supabase.table('users').select('total_credits').eq('user_id', user_id).execute().data[0]['total_credits'] + amount
    }).eq('user_id', user_id).execute()

# Retirer des crédits
def remove_credits(user_id, amount):
    init_user(user_id)
    supabase.table('users').update({
        'solde': max(0, supabase.table('users').select('solde').eq('user_id', user_id).execute().data[0]['solde'] - amount)
    }).eq('user_id', user_id).execute()

# Commande !credits
@bot.command()
async def credits(ctx):
    user_id = str(ctx.author.id)

try:
    response = supabase.table("users").select("total_credits").eq("user_id", user_id).single().execute()
    total_credits = response.data["total_credits"]
except Exception as e:
    await ctx.send("❌ Erreur : impossible de récupérer tes crédits.")
    return


# Commande !daily
@bot.command()
async def daily(ctx):
    user_id = str(ctx.author.id)
    now = datetime.datetime.now(datetime.timezone.utc)
    init_user(user_id)

    user = supabase.table('users').select('last_daily').eq('user_id', user_id).execute()
    last_claim = datetime.datetime.fromisoformat(user.data[0]['last_daily'])
    elapsed = (now - last_claim).total_seconds()

    if elapsed >= 86400:
        add_credits(user_id, 50)
        supabase.table('users').update({'last_daily': now.isoformat()}).eq('user_id', user_id).execute()
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

# Raretés, couleurs, messages et probabilités
RARITY_SETTINGS = {
    "commun": {
        "color": 0xFFFFFF,
        "message": "Une carte banale... mais chaque guerrier commence quelque part ⚔️",
        "chance": 50
    },
    "rare": {
        "color": 0x3498db,
        "message": "Une carte rare ! Le destin commence à tourner 🔷",
        "chance": 25
    },
    "epique": {
        "color": 0x9b59b6,
        "message": "Une carte épique ! Les ombres te reconnaissent 👁️",
        "chance": 15
    },
    "legendaire": {
        "color": 0xf1c40f,
        "message": "✨ Légendaire ! Tu viens d'éveiller une légende ancienne... ✨",
        "chance": 7
    },
    "unique": {
        "color": 0xff5c8d,
        "message": "💎 UNIQUE ! Tu as invoqué l'invocable... C'est du jamais vu ! 💎",
        "chance": 2
    },
    "collab": {
        "color": 0x00ffc8,
        "message": "🌟 COLLAB ! Une carte d'une dimension parallèle ! 🌟",
        "chance": 1
    }
}

# Charger les cartes depuis GitHub (tu peux le faire aussi localement avec open("cartes.json"))
with open("cartes.json", "r", encoding="utf-8") as f:
    all_cards = json.load(f)

# Filtrer les cartes par rareté
cards_by_rarity = {rarity: [c for c in all_cards if c["rarete"] == rarity] for rarity in RARITY_SETTINGS}

def tirer_rarete():
    total = sum(RARITY_SETTINGS[rarity]["chance"] for rarity in RARITY_SETTINGS)
    rand = random.uniform(0, total)
    cumulative = 0
    for rarete, settings in RARITY_SETTINGS.items():
        cumulative += settings["chance"]
        if rand < cumulative:
            return rarete
    return "commun"


@bot.command()
async def buy(ctx, packs: int = 1):
    if packs < 1 or packs > 10:
        await ctx.send("🛑 Tu peux acheter entre 1 et 10 packs maximum.")
        return

    user_id = str(ctx.author.id)

    # Vérifie le total_credits (correction ici: "user_id" au lieu de "id")
    try:
        response = supabase.table("users").select("total_credits").eq("user_id", user_id).single().execute()
        total_credits = response.data["total_credits"]
    except Exception:
        await ctx.send("❌ Erreur : impossible de récupérer tes crédits.")
        return

    if total_credits < packs:
        await ctx.send(f"💸 Tu n'as pas assez de crédits. Il te faut {packs} crédit(s).")
        return

    # Chargement des cartes depuis GitHub
    try:
        url = "https://raw.githubusercontent.com/TonUser/TonRepo/main/cartes.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                cards_data = await resp.json()
    except Exception:
        await ctx.send("❌ Impossible de charger les cartes.")
        return

    # Probabilités
    rarity_weights = {
        "commune": 60,
        "rare": 25,
        "epique": 10,
        "legendaire": 4,
        "collab": 1
    }

    rarity_emojis = {
        "commune": "⚪",
        "rare": "🟦",
        "epique": "🟪",
        "legendaire": "🟨",
        "collab": "🌟"
    }

    cards_by_rarity = {r: [c for c in cards_data if c["rareté"] == r] for r in rarity_weights}
    all_rarities = list(rarity_weights.keys())
    all_weights = list(rarity_weights.values())

    tirages = []

    for _ in range(packs):
        rarity = random.choices(all_rarities, weights=all_weights, k=1)[0]
        if cards_by_rarity[rarity]:
            card = random.choice(cards_by_rarity[rarity])
            tirages.append((rarity, card))

    if not tirages:
        await ctx.send("❌ Aucune carte n'a été tirée.")
        return

    # Mise à jour des crédits (attention : bien utiliser "user_id")
    try:
        supabase.table("users").update({"total_credits": total_credits - packs}).eq("user_id", user_id).execute()
    except Exception:
        await ctx.send("❌ Erreur lors de la mise à jour de tes crédits.")
        return

    # Mise à jour du défi communautaire
    try:
        supabase.table("defi").update({"tirages": supabase.table("defi").select("tirages").eq("id", "global").execute().data[0]["tirages"] + packs}).eq("id", "global").execute()
    except Exception:
        pass  # ne bloque pas la commande si le défi échoue

    # Envoi de l'embed
    embed = discord.Embed(
        title=f"🎁 {ctx.author.name} a ouvert {packs} pack{'s' if packs > 1 else ''} !",
        color=0x00ffcc
    )

    for rarity, card in tirages:
        emoji = rarity_emojis.get(rarity, "")
        embed.add_field(
            name=f"{emoji} {card['nom']} ({rarity.upper()})",
            value=f"ID: `{card['id']}`",
            inline=False
        )

    await ctx.send(embed=embed)




@bot.command()
async def givecredits(ctx):
    owner_id = 617293126494846996  # Ton ID Discord ici

    if ctx.author.id != owner_id:
        await ctx.send("❌ Cette commande est réservée au développeur.")
        return

    user_id = str(ctx.author.id)
    init_user(user_id)

    # Récupérer le solde actuel
    user = supabase.table('users').select('solde', 'total_credits').eq('user_id', user_id).execute()
    solde_actuel = user.data[0]['solde']
    total_actuel = user.data[0]['total_credits']

    # Ajouter 1000 crédits
    montant = 1000
    supabase.table('users').update({
        'solde': solde_actuel + montant,
        'total_credits': total_actuel + montant
    }).eq('user_id', user_id).execute()

    await ctx.send(f"✅ Tu as reçu {montant} crédits pour les tests. Nouveau solde : {solde_actuel + montant} crédits.")


@bot.command()
async def collection(ctx):
    user_id = str(ctx.author.id)
    response = supabase.table("new_user_cards").select("*").eq("user_id", user_id).eq("season", 0).execute()
    cartes = response.data
    user_id = ctx.author.id  # ✅ ici on récupère l'ID Discord (int)
    print(f"Résultat Supabase : {cartes}")
    print("Commande !collection déclenchée")


    # Ensuite tu peux utiliser cet ID pour faire une requête Supabase
    response = supabase.table("cartes").select("*").eq("user_id", user_id).eq("season", 0).execute()
    cartes = response.data

    if not cartes:
        await ctx.send(f"{ctx.author.mention}, tu n'as aucune carte pour la Saison 0 📭")
        return

    class Saison0View(discord.ui.View):
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
                color=0x3498db
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

    class SaisonButtonView(discord.ui.View):
        def __init__(self):
            super().__init__()

        @discord.ui.button(label="SAISON 0", style=discord.ButtonStyle.primary)
        async def saison0_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            view = Saison0View(cartes)
            await interaction.response.send_message(embed=view.get_embed(), view=view, ephemeral=True)

    await ctx.send("📚 Choisis une saison :", view=SaisonButtonView())

print(f"TOKEN: {TOKEN}")  # A supprimer ensuite, évidemment
bot.run(TOKEN)
