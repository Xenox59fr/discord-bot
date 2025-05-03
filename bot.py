import discord
from discord.ext import commands
from discord.ui import View, Button, button
from discord import Embed, Interaction, ButtonStyle, File
import json
import os
import random
import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")


# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Dossiers et fichiers
DOSSIER_CARTES = "SAISON_0"
FICHIER_CREDITS = "credits.json"
FICHIER_INVENTAIRE = "inventaire.json"

# Liste des cartes disponibles
cartes_possibles = [
    {"nom": "Guerrier", "rarete": "commune", "image": "guerrier.png"},
    {"nom": "Mage", "rarete": "commune", "image": "mage.png"},
    {"nom": "archere", "rarete": "commune", "image": "archere.png"},
    {"nom": "arion", "rarete": "legendaire", "image": "arion.png"},
    {"nom": "biboo", "rarete": "epique", "image": "biboo.png"},
    {"nom": "eloran", "rarete": "unique", "image": "eloran.png"},
    {"nom": "espion", "rarete": "commune", "image": "espion.png"},
    {"nom": "fairos", "rarete": "commune", "image": "fairos.png"},
    {"nom": "garde", "rarete": "commune", "image": "garde.png"},
    {"nom": "gorzak", "rarete": "rare", "image": "gorzak.png"},
    {"nom": "grizork", "rarete": "epique", "image": "grizork.png"},
    {"nom": "herboriste", "rarete": "commune", "image": "herboriste.png"},
    {"nom": "jason", "rarete": "collab", "image": "jason.png"},
    {"nom": "loupdelaforet", "rarete": "commune", "image": "loupdelaforet.png"},
    {"nom": "morgrin", "rarete": "unique", "image": "morgrin.png"},
    {"nom": "neroth", "rarete": "legendaire", "image": "neroth.png"},
    {"nom": "nyra", "rarete": "commune", "image": "nyra.png"},
    {"nom": "nyxilith", "rarete": "rare", "image": "nyxilith.png"},
    {"nom": "zorath", "rarete": "epique", "image": "zorath.png"},
]

credits_path = "credits.json"

def load_credits(fichier):
    try:
        with open(fichier, "r") as f:
            data = json.load(f)

        # Réparer les entrées mal foutues
        for user_id, valeur in data.items():
            if isinstance(valeur, int):
                # Si c'est juste un solde, on crée un dict complet
                data[user_id] = {
                    "solde": valeur,
                    "last_daily": "1970-01-01T00:00:00+00:00"  # une date par défaut très ancienne
                }

        return data
    except FileNotFoundError:
        return {}

        return {}

def save_credits(fichier, data):
    with open(fichier, "w") as f:
        json.dump(data, f, indent=4)


# Chargement des données
credits_data = load_credits(FICHIER_CREDITS)
inventaire_data = load_credits(FICHIER_INVENTAIRE)

# Commande pour voir ses crédits
@bot.command()
async def credits(ctx):
    user_id = str(ctx.author.id)
    solde = credits_data.get(user_id, {}).get("solde", 0)
    await ctx.send(f"💰 Tu as {solde} crédits.")



# Commande pour acheter une carte
@bot.command()
async def buy(ctx, nombre: int = 1):
    user_id = str(ctx.author.id)

    if user_id not in credits_data:
        credits_data[user_id] = {
            "solde": 100,
            "total_credits": 100,  # <-- on ajoute total_credits
            "last_daily": "1970-01-01T00:00:00+00:00"
        }

    solde = credits_data[user_id]["solde"]
    cout_total = 100 * nombre

    if solde < cout_total:
        await ctx.send(f"❌ Tu n'as pas assez de crédits pour acheter {nombre} carte(s) ({cout_total} crédits nécessaires).")
        return

    # Déduire le coût
    credits_data[user_id]["solde"] -= cout_total
    save_credits(FICHIER_CREDITS, credits_data)

    if user_id not in inventaire_data:
        inventaire_data[user_id] = []

    cartes_tirees = []

    for _ in range(nombre):
        carte = tirer_carte(cartes_possibles)

        if carte["nom"] not in inventaire_data[user_id]:
            inventaire_data[user_id].append(carte["nom"])

        cartes_tirees.append(carte)

    save_inventaire()

    # Tu pourrais ici envoyer un résumé des cartes tirées !
    await ctx.send(f"🎴 Tu as tiré {nombre} carte(s) !")


    couleurs = {
        "commune": 0x2ecc71,
        "rare": 0x3498db,
        "epique": 0x9b59b6,
        "legendaire": 0xf1c40f,
        "unique": 0xe67e22,
        "collab": 0xff00ff
    }

    messages_specials = {
        "commune": "💬 Une carte commune pour débuter ton aventure. 🎴",
        "rare": "🔵 Une carte rare vient enrichir ta collection ! ✨🎯",
        "epique": "🟣 Une carte **ÉPIQUE** surgit des ténèbres ! ⚡🔥",
        "legendaire": "🌟🌟 Une **LÉGENDAIRE** carte t'a choisi ! 🌟🏆💥",
        "unique": "🧡 INCROYABLE : Une **UNIQUE** carte vient d'apparaître ! 👑🚀",
        "collab": "🌈🌈 ***TIRAGE COLLABORATIF ULTRA EXCLUSIF !*** 💎🎉🎆"
    }

    for carte in cartes_tirees:
        chemin_image = os.path.join("C:\\Users\\FlowUP\\Documents\\cartes\\SAISON_0", carte["image"])
        if not os.path.isfile(chemin_image):
            await ctx.send(f"⚠️ Erreur : l'image {carte['image']} n'existe pas.")
            continue

        rarete = carte.get("rarete", "commune").lower()
        couleur_embed = couleurs.get(rarete, 0x95a5a6)
        message_special = messages_specials.get(rarete, "Une carte mystérieuse a été obtenue.")

        file = discord.File(chemin_image, filename=carte["image"])
        embed = discord.Embed(
            title=f"🎴 {carte['nom']} obtenu !",
            description=message_special,
            color=couleur_embed
        )
        embed.set_image(url=f"attachment://{carte['image']}")
        embed.add_field(name="Rareté", value=rarete.capitalize(), inline=True)
        embed.set_footer(
            text=f"🎉 Carte obtenue par {ctx.author.display_name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
)

        await ctx.send(file=file, embed=embed)



# Fonction pour sauvegarder l'inventaire
def save_inventaire():
    with open("inventaire.json", "w") as f:
        json.dump(inventaire_data, f, indent=4)

# Fonction pour tirer une carte avec chances
def tirer_carte(cartes):
    chances = {
        "commune": 50,
        "rare": 22,
        "epique": 13,
        "legendaire": 8,
        "unique": 5,
        "collab": 2  # Collab extrêmement rare !!
    }

    tirage = random.choices(
        cartes,
        weights=[chances.get(c["rarete"].lower(), 0) for c in cartes],
        k=1
    )
    return tirage[0]

@bot.command()
async def daily(ctx):
    user_id = str(ctx.author.id)
    
    if isinstance(credits_data.get(user_id), int):
        credits_data[user_id] = {
            "solde": credits_data[user_id],
            "total_credits": credits_data[user_id],  # 🆕 on copie aussi l'ancien solde
            "last_daily": "2000-01-01T00:00:00"
    }

    
    maintenant = datetime.datetime.now(datetime.timezone.utc)
    last_daily = datetime.datetime.fromisoformat(credits_data[user_id]["last_daily"]).replace(tzinfo=datetime.timezone.utc)

    
    if (maintenant - last_daily).days >= 1:
        credits_data[user_id]["solde"] += 50
        credits_data[user_id]["last_daily"] = maintenant.isoformat()
        save_credits(FICHIER_CREDITS, credits_data)
        await ctx.send(f"🎁 Tu as reçu 50 crédits journaliers !")
    else:
        await ctx.send("⏳ Tu as déjà réclamé ton daily aujourd'hui ! Reviens demain.")
        
        
@bot.command()
async def leaderboard(ctx):
    # Trie les joueurs par total_credits décroissant
    classement = sorted(credits_data.items(), key=lambda x: x[1].get("total_credits", 0), reverse=True)

    embed = discord.Embed(
        title="🏆 Leaderboard des Crédits Totaux 🏆",
        color=discord.Color.gold()
    )

    top = classement[:10]  # Top 10 joueurs
    for idx, (user_id, data) in enumerate(top, start=1):
        user = await bot.fetch_user(int(user_id))
        embed.add_field(
            name=f"#{idx} - {user.name}",
            value=f"💰 {data.get('total_credits', 0)} crédits au total",
            inline=False
        )

    await ctx.send(embed=embed)
    
# Dictionnaire pour stocker le dernier message de chaque utilisateur
dernier_message = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore les messages des bots

    user_id = str(message.author.id)
    maintenant = datetime.datetime.now(datetime.timezone.utc)

    # Vérifie si l'utilisateur a parlé récemment
    dernier = dernier_message.get(user_id)
    if dernier and (maintenant - dernier).total_seconds() < 60:
        await bot.process_commands(message)
        return  # ⏳ Moins de 60 secondes depuis le dernier gain ➔ on ne donne pas de crédit

    # Mise à jour de l'heure du dernier message
    dernier_message[user_id] = maintenant

    # S'assurer que l'utilisateur existe dans les crédits
    if user_id not in credits_data:
        credits_data[user_id] = {
            "solde": 100,
            "total_credits": 100,
            "last_daily": "1970-01-01T00:00:00+00:00"
        }

    # 🔥 Correction : Si "total_credits" n'existe pas, on le crée !
    if "total_credits" not in credits_data[user_id]:
        credits_data[user_id]["total_credits"] = credits_data[user_id].get("solde", 0)

    # Ajouter 1 crédit
    credits_data[user_id]["solde"] += 1
    credits_data[user_id]["total_credits"] += 1
    save_credits(FICHIER_CREDITS, credits_data)

    await bot.process_commands(message)

import discord
from discord.ext import commands
from discord.ui import View, Button
import os

# ----- View pour le bouton SAISON 0 -----
class Saison0StartView(View):
    def __init__(self, ctx):
        super().__init__(timeout=180)
        self.ctx = ctx  # L'auteur de la commande (celui dont on veut voir la collection)

    @discord.ui.button(label="SAISON 0", style=discord.ButtonStyle.primary)
    async def saison0_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        # Préparer les cartes
        dossier = "C:\\Users\\FlowUP\\Documents\\cartes\\SAISON_0"
        cartes = []

        for fichier in os.listdir(dossier):
            if fichier.endswith((".png", ".jpg", ".jpeg")):
                chemin = os.path.join(dossier, fichier)
                cartes.append((fichier, chemin))

        if not cartes:
            await interaction.followup.send(
                "❌ Aucune carte trouvée dans SAISON 0.",
                ephemeral=True
            )
            return

        # Pagination : 5 cartes par page
        cartes_par_page = 5
        pages = [cartes[i:i+cartes_par_page] for i in range(0, len(cartes), cartes_par_page)]

        embeds = await generate_embeds(pages, self.ctx.author)

        fichiers_page_0 = [discord.File(chemin, filename=nom) for nom, chemin in cartes[:cartes_par_page]]

        await interaction.followup.send(
            embed=embeds[0],
            files=fichiers_page_0,
            view=Saison0PaginationView(interaction.user, embeds, cartes, cartes_par_page),
            ephemeral=True
        )

# ----- Fonction pour générer les embeds -----
async def generate_embeds(pages, author):
    embeds = []
    for cartes in pages:
        description = ""
        for fichier, _ in cartes:
            description += f"🎴 {fichier}\n"
        embed = discord.Embed(
            title=f"📦 Collection SAISON 0 de {author.display_name}",
            description=description,
            color=discord.Color.gold()
        )
        embeds.append(embed)
    return embeds

# ----- View pour la pagination -----
class Saison0PaginationView(View):
    def __init__(self, user, embeds, cartes, cartes_par_page):
        super().__init__(timeout=180)
        self.user = user  # Celui qui a cliqué (pas forcément ctx.author !)
        self.embeds = embeds
        self.cartes = cartes  # On garde juste nom/chemin, pas de discord.File ouvert !
        self.cartes_par_page = cartes_par_page
        self.page = 0

    @discord.ui.button(label="⏪", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message(
                "❌ Tu ne peux pas contrôler cette collection.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        self.page = (self.page - 1) % len(self.embeds)

        fichiers_page = [
            discord.File(chemin, filename=nom)
            for nom, chemin in self.cartes[self.page*self.cartes_par_page:(self.page+1)*self.cartes_par_page]
        ]

        await interaction.edit_original_response(
            embed=self.embeds[self.page],
            attachments=fichiers_page,
            view=self
        )

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message(
                "❌ Tu ne peux pas contrôler cette collection.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        self.page = (self.page + 1) % len(self.embeds)

        fichiers_page = [
            discord.File(chemin, filename=nom)
            for nom, chemin in self.cartes[self.page*self.cartes_par_page:(self.page+1)*self.cartes_par_page]
        ]

        await interaction.edit_original_response(
            embed=self.embeds[self.page],
            attachments=fichiers_page,
            view=self
        )

# ----- Commande principale -----
@bot.command()
async def collection(ctx):
    view = Saison0StartView(ctx)
    embed = discord.Embed(
        title=f"Collection de {ctx.author.display_name}",
        description="Clique sur un bouton pour voir sa collection par saison !",
        color=discord.Color.blurple()
    )
    await ctx.send(embed=embed, view=view)
