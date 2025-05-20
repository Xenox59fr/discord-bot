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
from discord import ui
from discord.ui import View, button  
from discord import ButtonStyle   
from collections import Counter
from threading import Thread
from keep_alive import keep_alive

keep_alive()


joueurs_cartes = {}

def charger_cartes():
    global joueurs_cartes
    if os.path.exists("cartes_joueurs.json") and os.path.getsize("cartes_joueurs.json") > 0:
        with open("cartes_joueurs.json", "r") as f:
            joueurs_cartes = json.load(f)
    else:
        joueurs_cartes = {}

class SaisonView(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    @discord.ui.button(label="📅 Saison 0", style=discord.ButtonStyle.primary)
    async def saison0(self, interaction: discord.Interaction, button: discord.ui.Button):

        cartes = joueurs_cartes.get(self.user_id, [])
        saison_cartes = [c for c in cartes if c.get("saison") == "0"]

        if not saison_cartes:
            await interaction.response.send_message("📭 Tu n’as encore aucune carte de la Saison 0.")
            return

        embeds = []
        for i in range(0, len(saison_cartes), 2):
            embed = discord.Embed(
                title=f"✨ Collection Saison 0 de {interaction.user.name} ✨",
                color=discord.Color.purple()
            )
            chunk = saison_cartes[i:i+2]
            for carte in chunk:
                nom = carte["nom"]
                rarete = carte["rarete"]
                image_url = carte["image"]
                embed.add_field(name=f"{nom} ({rarete})", value="\u200b", inline=False)
                embed.set_image(url=image_url)  # Remplacera à chaque carte, donc 1 image visible par embed
            embeds.append(embed)

        await interaction.response.send_message(embeds=embeds, ephemeral=False)


def load_cards():
    try:
        with open('cartes_joueurs.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Retourne un dictionnaire vide si le fichier est inexistant ou mal formé


# Fonction pour sauvegarder les cartes dans un fichier JSON
def save_cards(cards):
    with open('cartes_joueurs.json', 'w') as f:
        json.dump(cards, f, indent=4)

# Chargement initial des cartes
cards = load_cards()


intents = discord.Intents.default()  # Définir les intents
bot = commands.Bot(command_prefix='!', intents=intents)  # Utiliser commands.Bot

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')

# Fichier de sauvegarde pour les cartes des joueurs
FICHIER_SAUVEGARDE = "cartes_joueurs.json"
# Stockage en mémoire des cartes obtenues par chaque joueur
joueurs_cartes = {}

def charger_cartes():
    """Charge les cartes des joueurs depuis le fichier JSON"""
    global joueurs_cartes
    if os.path.exists(FICHIER_SAUVEGARDE):
        with open(FICHIER_SAUVEGARDE, "r") as f:
            joueurs_cartes = json.load(f)
    else:
        joueurs_cartes = {}

def sauvegarder_cartes():
    """Sauvegarde les cartes des joueurs dans le fichier JSON"""
    with open(FICHIER_SAUVEGARDE, "w") as f:
        json.dump(joueurs_cartes, f)

# Charger les cartes au démarrage
charger_cartes()

# Sauvegarder les cartes quand le bot s'arrête
@bot.event
async def on_shutdown():
    sauvegarder_cartes()
    
# Liste des cartes disponibles
cartes_disponibles = [
    {"id": "archere", "nom": "archere", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/archere.png", "rarete": "commun"},
    {"id": "skaarlphase1", "nom": "skaarlphase1", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/skaarlphase1.png", "rarete": "rare"},
    {"id": "arion", "nom": "arion", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/arion.png", "rarete": "legendaire"},
    {"id": "biboo", "nom": "biboo", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/biboo.png", "rarete": "epique"},
    {"id": "eloran", "nom": "eloran", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/eloran.png", "rarete": "unique"},
    {"id": "jason", "nom": "jason", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/jason.png", "rarete": "collab"},
    {"id": "espion", "nom": "espion", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/espion.png", "rarete": "commun"},
    {"id": "fairos", "nom": "fairos", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/fairos.png", "rarete": "commun"},
    {"id": "garde", "nom": "garde", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/garde.png", "rarete": "commun"},
    {"id": "golem", "nom": "golem", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/golem.png", "rarete": "commun"},
    {"id": "gorzak", "nom": "gorzak", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/gorzak.png", "rarete": "rare"},
    {"id": "grizork", "nom": "grizork", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/grizork.png", "rarete": "epique"},
    {"id": "guerrier", "nom": "guerrier", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/guerrier.png", "rarete": "commun"},
    {"id": "herboriste", "nom": "herboriste", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/herboriste.png", "rarete": "commun"},
    {"id": "krivak", "nom": "krivak", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/krivak.png", "rarete": "commun"},
    {"id": "mage", "nom": "mage", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/mage.png", "rarete": "commun"},
    {"id": "loupdelaforet", "nom": "loupdelaforet", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/loupdelaforet.png", "rarete": "commun"},
    {"id": "nyra", "nom": "nyra", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/nyra.png", "rarete": "commun"},
    {"id": "nyxilith", "nom": "nyxilith", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/nyxilith.png", "rarete": "rare"},
    {"id": "skaarl", "nom": "skaarl", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/skaarl.png", "rarete": "commun"},
    {"id": "skaarlphase2", "nom": "skaarlphase2", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/skaarlphase2.png", "rarete": "epique"},
    {"id": "skaarlphase3", "nom": "skaarlphase3", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/skaarlphase3.png", "rarete": "legendaire"},
    {"id": "sylgron", "nom": "sylgron", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/sylgron.png", "rarete": "commun"},
    {"id": "zorath", "nom": "zorath", "image": "https://raw.githubusercontent.com/Xenox59fr/discord-bot/main/SAISON_0/zorath.png", "rarete": "rare"}
]

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')

# Fichier de sauvegarde pour les cartes des joueurs
FICHIER_SAUVEGARDE = "cartes_joueurs.json"
# Stockage en mémoire des cartes obtenues par chaque joueur
joueurs_cartes = {}
def charger_cartes():
    """Charge les cartes des joueurs depuis le fichier JSON"""
    global joueurs_cartes
    if os.path.exists(FICHIER_SAUVEGARDE):
        with open(FICHIER_SAUVEGARDE, "r") as f:
            joueurs_cartes = json.load(f)
    else:
        joueurs_cartes = {}
def sauvegarder_cartes():
    """Sauvegarde les cartes des joueurs dans le fichier JSON"""
    with open(FICHIER_SAUVEGARDE, "w") as f:
        json.dump(joueurs_cartes, f)

# Charger les cartes au démarrage
charger_cartes()

# Sauvegarder les cartes quand le bot s'arrête
@bot.event
async def on_shutdown():
    sauvegarder_cartes()
def obtenir_description_par_defaut(carte):
    return f"Nom : {carte['nom']}\nRareté : {carte['rarete'].capitalize()}"
# Dictionnaire en mémoire : user_id -> liste de card_id
cartes_obtenues = {}
last_credit_time = {}


# Flask pour le "ping" de Render
app = Flask('')

@app.route('/')
def home():
    return "Bot actif."

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

@bot.command()
async def credits(ctx):
    user_id = str(ctx.author.id)

    try:
        response = supabase.table("users").select("solde, total_credits").eq("user_id", user_id).single().execute()
        solde = response.data["solde"]
        total = response.data["total_credits"]
    except Exception as e:
        await ctx.send("❌ Erreur : impossible de récupérer tes crédits.")
        return

    await ctx.send(f"💰 Tu as **{solde} crédits** disponibles.\n🏅 Total cumulés (classement) : **{total} crédits**.")



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

# Classe de pagination des cartes tirées
class CardPaginator(View):
    def __init__(self, ctx, tirages):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.tirages = tirages
        self.index = 0

    async def interaction_check(self, interaction):
        return interaction.user == self.ctx.author

    @button(label="⬅️ Précédent", style=ButtonStyle.primary)
    async def prev(self, interaction, button):
        if self.index > 0:
            self.index -= 1
            await interaction.response.edit_message(embed=self.make_embed(), view=self)
        else:
            await interaction.response.defer()

    @button(label="Suivant ➡️", style=ButtonStyle.primary)
    async def next(self, interaction, button):
        if self.index < len(self.tirages) - 1:
            self.index += 1
            await interaction.response.edit_message(embed=self.make_embed(), view=self)
        else:
            await interaction.response.defer()

    def make_embed(self):
        rarete, carte = self.tirages[self.index]
        rarity_data = {
            "commun": {"emoji": "⚪", "color": 0xB0B0B0, "phrase": "Une brise légère... la légende commence à peine."},
            "rare": {"emoji": "🔵", "color": 0x3498DB, "phrase": "Un éclat bleu traverse l’ombre. La chance tourne."},
            "epique": {"emoji": "🟣", "color": 0x9B59B6, "phrase": "L’écho d’un pouvoir oublié résonne dans le néant."},
            "legendaire": {"emoji": "✨", "color": 0xF1C40F, "phrase": "Une relique ancestrale vient de surgir... L’histoire s’écrit."},
            "unique": {"emoji": "🧡", "color": 0xE67E22, "phrase": "Une entité singulière t’a choisi... Invoquée du fond des âges."},
            "collab": {"emoji": "🌟", "color": 0x00FFF7, "phrase": "D’un autre monde... une convergence d’univers s’est produite."}
        }
        data = rarity_data.get(rarete, {})
        embed = Embed(
            title=f"{data.get('emoji', '')} {carte['nom']} ({rarete.upper()})",
            description=data.get("phrase", ""),
            color=data.get("color", 0x3498DB)
        )
        if carte.get("image"):
            embed.set_image(url=carte["image"])
        embed.set_footer(text=f"Carte {self.index + 1} sur {len(self.tirages)}")
        return embed

@bot.command()
async def buy(ctx, packs: int = 1):
    if packs < 1 or packs > 10:
        await ctx.send("🛑 Tu peux acheter entre 1 et 10 packs maximum.")
        return
        
    prix_par_pack = 3  # ← ici tu choisis ton prix
    cout_total = packs * prix_par_pack


    user_id = str(ctx.author.id)

    try:
        with open("cartes.json", "r") as f:
            all_cards = json.load(f)
    except FileNotFoundError:
        await ctx.send("❌ Erreur : fichier de cartes introuvable.")
        return

    try:
        response = supabase.table("users").select("solde", "total_credits").eq("user_id", user_id).single().execute()
        solde = response.data["solde"]
        total_credits = response.data["total_credits"]
    except Exception:
        await ctx.send("❌ Erreur : impossible de récupérer tes crédits.")
        return

    if solde < cout_total:
       await ctx.send(f"💸 Tu n'as pas assez de crédits. Il te faut {cout_total} crédit(s).")
       return



    def tirer_rarete():
        chances = {
            "commun": 50,
            "rare": 25,
            "epique": 15,
            "legendaire": 7,
            "unique": 2,
            "collab": 1
        }
        return random.choices(list(chances.keys()), weights=chances.values(), k=1)[0]

    tirages = []
    for _ in range(packs):
        rarete = tirer_rarete()
        cartes_possibles = [c for c in all_cards if c["rarete"] == rarete]
        if cartes_possibles:
            carte = random.choice(cartes_possibles)
            tirages.append((rarete, carte))

    if not tirages:
        await ctx.send("❌ Aucune carte n'a été tirée.")
        return

    try:
        with open("cartes_joueurs.json", "r") as f:
            cartes_joueurs = json.load(f)
    except FileNotFoundError:
        cartes_joueurs = {}

    if user_id not in cartes_joueurs:
        cartes_joueurs[user_id] = []

    to_insert = []
    for _, carte in tirages:
        cartes_joueurs[user_id].append({
            "id": carte["id"],
            "nom": carte["nom"],
            "image": carte.get("image", ""),
            "rarete": carte["rarete"],
            "season": "0"
        })
        to_insert.append({
            "user_id": user_id,
            "card_id": carte["id"],
            "nom": carte["nom"],
            "image": carte.get("image", ""),
            "rarete": carte["rarete"],
            "season": "0"
        })

    try:
        supabase.table("cartes").insert(to_insert).execute()
    except Exception:
        await ctx.send("❌ Erreur lors de l'enregistrement des cartes dans Supabase.")
        return

    with open("cartes_joueurs.json", "w") as f:
        json.dump(cartes_joueurs, f, indent=2)

    try:
        supabase.table("users").update({"solde": solde - cout_total}).eq("user_id", user_id).execute()
    except Exception:
        await ctx.send("❌ Erreur lors de la mise à jour de ton solde.")
        return

    try:
        current = supabase.table("defi").select("tirages").eq("id", "global").execute().data[0]["tirages"]
        supabase.table("defi").update({"tirages": current + packs}).eq("id", "global").execute()
    except Exception:
        pass

    paginator = CardPaginator(ctx, tirages)
    embed = paginator.make_embed()
    await ctx.send(embed=embed, view=paginator)





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

    # Requête Supabase pour récupérer toutes les cartes du joueur
    try:
        response = supabase.table("cartes").select("*").eq("user_id", user_id).execute()
        cartes = response.data  # Liste des cartes brutes
    except Exception as e:
        await ctx.send("❌ Erreur lors de la récupération de ta collection.")
        print(e)
        return

    if not cartes:
        await ctx.send("📭 Tu n’as encore aucune carte dans ta collection.")
        return

    # Compter les occurrences par ID de carte
    counter = Counter(c["card_id"] for c in cartes)

    # Récupérer une carte unique par ID
    cartes_uniques = {}
    for c in cartes:
        if c["card_id"] not in cartes_uniques:
            cartes_uniques[c["card_id"]] = c

    # Fusionner en une liste avec quantité
    cartes_fusionnees = []
    for card_id, count in counter.items():
        carte = dict(cartes_uniques[card_id])  # copie pour éviter modif originale
        carte["quantite"] = count
        cartes_fusionnees.append(carte)

    view = SaisonView(user_id, cartes_fusionnees)
    await ctx.send("Voici tes collections disponibles :", view=view)
    
class SaisonView(View):
    def __init__(self, user_id, cartes):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.cartes = cartes

    @discord.ui.button(label="📅 Saison 0", style=discord.ButtonStyle.primary)
    async def saison0(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Suppression du contrôle d'accès sur user_id pour que tout le monde puisse cliquer

        try:
            response = supabase.table("cartes").select("*").eq("user_id", self.user_id).eq("season", "0").execute()
            cartes = response.data
        except Exception as e:
            await interaction.response.send_message("❌ Erreur lors de la récupération des cartes.")
            print(e)
            return

        if not cartes:
            await interaction.response.send_message("📭 Cette personne n’a aucune carte de la Saison 0.")
            return

        from collections import Counter
        counter = Counter(c["card_id"] for c in cartes)

        cartes_uniques = {}
        for c in cartes:
            if c["card_id"] not in cartes_uniques:
                c["quantite"] = counter[c["card_id"]]
                cartes_uniques[c["card_id"]] = c

        cartes_fusionnees = list(cartes_uniques.values())

        view = CollectionView(self.user_id, cartes_fusionnees)
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)




class CollectionView(View):
    def __init__(self, user_id, cartes):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.cartes = cartes
        self.index = 0  # carte affichée

    def get_embed(self):  # ligne 583
        carte = self.cartes[self.index]
        quantite = carte.get("quantite", 1)

        titre = f"Carte {self.index + 1}/{len(self.cartes)} : {carte['nom']} ({carte['rarete'].capitalize()})"
        if quantite > 1:
            titre = f"{titre}  •  x{quantite}"

        embed = Embed(
            title=titre,
            color=RARITY_SETTINGS.get(carte['rarete'], {}).get('color', 0xFFFFFF)
        )
        embed.set_image(url=carte['image'])
        embed.set_footer(text="Utilise les boutons pour naviguer dans la collection.")
        return embed


    @discord.ui.button(label="⬅️ Précédent", style=ButtonStyle.secondary)
    async def precedent(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        self.index = (self.index - 1) % len(self.cartes)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Suivant ➡️", style=ButtonStyle.secondary)
    async def suivant(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        self.index = (self.index + 1) % len(self.cartes)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

@bot.command(name="leaderboard")
async def leaderboard(ctx):
    try:
        # Récupérer les 10 meilleurs utilisateurs selon les crédits totaux
        response = supabase.table("users").select("user_id, total_credits").order("total_credits", desc=True).limit(10).execute()
        top_users = response.data

        if not top_users:
            await ctx.send("📭 Aucun utilisateur trouvé dans le classement.")
            return

        embed = discord.Embed(
            title="🏆 Classement des plus riches (total cumulé)",
            description="Les utilisateurs avec le plus de crédits gagnés durant toute la saison.",
            color=discord.Color.gold()
        )

        for i, user in enumerate(top_users, start=1):
            user_obj = await bot.fetch_user(int(user['user_id']))
            pseudo = user_obj.name if user_obj else f"Utilisateur inconnu ({user['user_id']})"
            embed.add_field(
                name=f"{i}. {pseudo}",
                value=f"💰 {user['total_credits']} crédits cumulés",
                inline=False
            )

        await ctx.send(embed=embed)

    except Exception as e:
        print(e)
        await ctx.send("❌ Une erreur est survenue lors de la récupération du classement.")
        
@bot.command()
@commands.has_permissions(manage_guild=True)
async def addcredits(ctx, membre: discord.Member, montant: int):
    if montant <= 0:
        await ctx.send("❌ Le montant doit être supérieur à 0.")
        return

    user_id = str(membre.id)

    try:
        # Vérifie si l'utilisateur existe déjà
        response = supabase.table("users").select("solde").eq("user_id", user_id).single().execute()
        user_data = response.data

        if user_data:
            # Mise à jour du solde seulement (PAS total_credits)
            nouveau_solde = user_data["solde"] + montant
            supabase.table("users").update({"solde": nouveau_solde}).eq("user_id", user_id).execute()
        else:
            # Si l'utilisateur n'existe pas, on l'insère avec le solde uniquement
            supabase.table("users").insert({
                "user_id": user_id,
                "solde": montant,
                "total_credits": 0,
                "last_daily": None
            }).execute()

        await ctx.send(f"✅ {montant} crédits ont été ajoutés à {membre.mention} (hors classement).")

    except Exception as e:
        print("Erreur Supabase :", e)
        await ctx.send("❌ Une erreur est survenue lors de l'ajout des crédits.")
        
@bot.command()
@commands.has_permissions(administrator=True)
async def givecard(ctx, member: discord.Member, card_id: str):
    user_id = str(member.id)

    try:
        with open("cartes.json", "r") as f:
            all_cards = json.load(f)
    except FileNotFoundError:
        await ctx.send("❌ Fichier cartes.json introuvable.")
        return

    carte = next((c for c in all_cards if c["id"] == card_id), None)
    if not carte:
        await ctx.send("❌ Carte introuvable.")
        return

    try:
        supabase.table("cartes").insert([{
            "user_id": user_id,
            "card_id": carte["id"],
            "nom": carte["nom"],
            "image": carte.get("image", ""),
            "rarete": carte["rarete"],
            "season": "0"
        }]).execute()
    except Exception:
        await ctx.send("❌ Erreur lors de l'ajout de la carte.")
        return

    await ctx.send(f"✅ Carte **{carte['nom']}** donnée à {member.mention}.")
    
@bot.command()
@commands.has_permissions(administrator=True)
async def giveall(ctx, card_id: str):
    try:
        with open("cartes.json", "r") as f:
            all_cards = json.load(f)
    except FileNotFoundError:
        await ctx.send("❌ Fichier cartes.json introuvable.")
        return

    carte = next((c for c in all_cards if c["id"] == card_id), None)
    if not carte:
        await ctx.send("❌ Carte introuvable.")
        return

    try:
        users = supabase.table("users").select("user_id").execute().data
    except Exception:
        await ctx.send("❌ Erreur lors de la récupération des utilisateurs.")
        return

    insertions = [{
        "user_id": user["user_id"],
        "card_id": carte["id"],
        "nom": carte["nom"],
        "image": carte.get("image", ""),
        "rarete": carte["rarete"],
        "season": "0"
    } for user in users]

    try:
        supabase.table("cartes").insert(insertions).execute()
    except Exception:
        await ctx.send("❌ Erreur lors de l'ajout des cartes.")
        return

    await ctx.send(f"✅ Carte **{carte['nom']}** donnée à **{len(users)} joueurs**.")







print(f"TOKEN: {TOKEN}")  # A supprimer ensuite, évidemment
bot.run(TOKEN)
