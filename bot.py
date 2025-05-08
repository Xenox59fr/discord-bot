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
    init_user(user_id)
    user = supabase.table('users').select('solde').eq('user_id', user_id).execute()
    solde = user.data[0]['solde']
    await ctx.send(f"{ctx.author.mention}, tu as {solde} crédits.")

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

# Fonction pour choisir une rareté selon les chances
def tirer_rarete():
    rand = random.uniform(0, 100)
    cumulative = 0
    for rarity, data in RARITY_SETTINGS.items():
        cumulative += data["chance"]
        if rand <= cumulative:
            return rarity
    return "commun"

@bot.command()
async def buy(ctx, nombre: int = 1):
    user_id = str(ctx.author.id)

    if nombre not in [1, 5, 10]:
        await ctx.send(f"{ctx.author.mention}, tu peux acheter 1, 5 ou 10 packs seulement.")
        return

    init_user(user_id)
    result = supabase.table("users").select("solde").eq("user_id", user_id).execute()

    if result.data:
        solde = result.data[0]["solde"]
    else:
        solde = 0

    if solde < nombre:
        await ctx.send(f"{ctx.author.mention}, tu n'as pas assez de crédits pour acheter {nombre} pack(s) ❌.")
        return

    remove_credits(user_id, nombre)

    for _ in range(nombre):
        rarete = tirer_rarete()
        carte = random.choice(cards_by_rarity[rarete])
        couleur = RARITY_SETTINGS[rarete]["color"]
        message = RARITY_SETTINGS[rarete]["message"]

        embed = discord.Embed(
            title=f"🃏 Tu as tiré : {carte['nom']}",
            description=message,
            color=couleur
        )

        # Ajouter l'image de la carte
        embed.set_image(url=carte["image"])

        # Ajouter le nom d'utilisateur et sa photo de profil dans l'embed
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)

        # Ajouter la rareté dans le footer
        embed.set_footer(text=f"Rareté : {rarete.upper()}")

        # Envoyer l'embed
        await ctx.send(embed=embed)
         # Vérification avant l'insertion dans la base
        print(f"Insertion carte : user_id={user_id}, card_id={carte['id']}, rarity={rarete}")

        # Insérer la carte dans la base de données
        supabase.table("new_user_cards").insert({
            "user_id": user_id,
            "card_id": carte["id"],      # Assure-toi que chaque carte dans cartes.json a un champ "id"
            "rarity": rarete
        }).execute()
        # Enregistrer la carte obtenue dans Supabase
    supabase.table("cartes").insert({
        "user_id": user_id,
        "card_id": carte["id"],      # Assure-toi que chaque carte dans cartes.json a un champ "id"
        "rarity": rarete
    }).execute()


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

# Fonction pour afficher la collection de l'utilisateur
@bot.command()
async def collection(ctx):
    # Création du bouton Saison 0
    saison_button = Button(label="SAISON 0", custom_id="season0")
    saison_view = View()
    saison_view.add_item(saison_button)

    # Envoi du message avec le bouton SAISON 0
    await ctx.send("Clique sur le bouton pour voir tes cartes de la SAISON 0 🎴", view=saison_view)

# Événement quand un utilisateur clique sur un bouton
@bot.event
async def on_socket_response(payload):
    if payload["t"] == "INTERACTION_CREATE":
        custom_id = payload["d"]["data"]["custom_id"]
        user_id = str(payload["d"]["member"]["user"]["id"])

        # Si l'utilisateur clique sur SAISON 0
        if custom_id == "season0":
            # Créer des boutons pour chaque rareté
            rarity_buttons = [
                Button(label="Commun", custom_id="rarity_commun"),
                Button(label="Rare", custom_id="rarity_rare"),
                Button(label="Épique", custom_id="rarity_epique"),
                Button(label="Légendaire", custom_id="rarity_legendaire")
            ]
            rarity_view = View()
            for button in rarity_buttons:
                rarity_view.add_item(button)

            # Envoie un message avec les boutons de rareté
            await bot.get_channel(int(payload["d"]["channel_id"])).send(
                "Choisis une rareté pour voir tes cartes 🎴", view=rarity_view
            )

        # Si l'utilisateur clique sur un bouton de rareté
        elif custom_id.startswith("rarity_"):
            rarity = custom_id.split("_")[1]

            # Filtrer les cartes de cet utilisateur par rareté et saison 0
            cartes_utilisateur = supabase.table("new_user_cards").select("*").eq("user_id", user_id).eq("rarity", rarity).eq("season", "0").execute()

            if not cartes_utilisateur.data:
                await bot.get_channel(int(payload["d"]["channel_id"])).send(f"{user_id}, tu n'as pas encore de cartes de rareté {rarity} dans la SAISON 0.")
                return

            # Créer l'embed pour afficher les cartes filtrées
            embed = discord.Embed(
                title=f"Cartes de rareté {rarity.capitalize()}",
                description="Voici tes cartes filtrées ! 🎴",
                color=RARITY_SETTINGS[rarity]["color"]
            )

            # Ajouter chaque carte avec son image
            for carte in cartes_utilisateur.data:
                image_url = carte.get("image_url", "")  # Assure-toi que l'image est stockée dans la base de données
                embed.add_field(
                    name=carte["card_id"],
                    value=f"**{carte['card_id']}**\nRareté: {rarity.capitalize()}",
                    inline=False
                )
                if image_url:
                    embed.set_thumbnail(url=image_url)

            # Envoie de l'embed avec les cartes
            await bot.get_channel(int(payload["d"]["channel_id"])).send(embed=embed)




bot.run(TOKEN)







