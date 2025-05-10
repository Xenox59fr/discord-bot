import discord
from discord.ext import commands
from supabase import create_client, Client
import json
import random
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Chargement des cartes
with open("cards.json", "r", encoding="utf-8") as f:
    all_cards = json.load(f)

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

def choisir_rarete():
    rand = random.uniform(0, 100)
    total = 0
    for rarete, chance in rarity_probabilities.items():
        total += chance
        if rand <= total:
            return rarete
    return "commun"

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")

@bot.command()
async def credits(ctx):
    user_id = str(ctx.author.id)
    response = supabase.table("users").select("credits").eq("user_id", user_id).execute()
    user = response.data[0] if response.data else None

    if user:
        await ctx.send(f"💰 {ctx.author.mention}, vous avez **{user['credits']}** crédits.")
    else:
        supabase.table("users").insert({"user_id": user_id, "credits": 10, "total_credits": 10}).execute()
        await ctx.send(f"👋 Bienvenue, {ctx.author.mention} ! Vous avez reçu 10 crédits.")

@bot.command()
async def daily(ctx):
    user_id = str(ctx.author.id)
    response = supabase.table("users").select("credits", "total_credits").eq("user_id", user_id).execute()
    user = response.data[0] if response.data else None

    if user:
        supabase.table("users").update({
            "credits": user["credits"] + 5,
            "total_credits": user["total_credits"] + 5
        }).eq("user_id", user_id).execute()
        await ctx.send(f"🗓️ {ctx.author.mention}, vous avez reçu **5 crédits** aujourd'hui !")
    else:
        supabase.table("users").insert({"user_id": user_id, "credits": 5, "total_credits": 5}).execute()
        await ctx.send(f"🗓️ Bienvenue {ctx.author.mention}, vous avez reçu **5 crédits** aujourd'hui !")

@bot.command()
async def buy(ctx, nombre: int = 1):
    if nombre < 1:
        await ctx.send("Vous devez acheter au moins un pack.")
        return

    user_id = str(ctx.author.id)
    response = supabase.table("users").select("credits").eq("user_id", user_id).execute()
    user_data = response.data[0] if response.data else None

    if not user_data:
        await ctx.send("Vous n'avez pas de compte enregistré.")
        return

    credits = user_data["credits"]
    cout_total = nombre * 1

    if credits < cout_total:
        await ctx.send(f"Il vous faut {cout_total} crédits, vous n'en avez que {credits}.")
        return

    cartes_tirees = []
    for _ in range(nombre):
        rarete = choisir_rarete()
        cartes_rarite = [c for c in all_cards if c["rarity"] == rarete]
        carte = random.choice(cartes_rarite)
        cartes_tirees.append((carte, rarete))

        data = {
            "user_id": user_id,
            "card_id": carte["id"],
            "rarity": rarete,
            "season": 0
        }
        supabase.table("user_cards").insert(data).execute()

    supabase.table("users").update({"credits": credits - cout_total}).eq("user_id", user_id).execute()
    
    for carte, rarete in cartes_tirees:
        embed = discord.Embed(
            title=f"{rarity_emojis[rarete]} Nouvelle carte obtenue !",
            description=f"**{carte['name']}**",
            color=rarity_colors[rarete]
        )
        embed.set_image(url=carte['image'])
        embed.set_footer(text=f"Rareté : {rarete.capitalize()} | Saison 0")
        await ctx.send(embed=embed)

    await ctx.send(f"{ctx.author.mention}, vous avez tiré {nombre} carte(s) pour {cout_total} crédit(s).")

@bot.command()
async def defi(ctx):
    response = supabase.table("progression_defi").select("progression").eq("id", 1).execute()
    progression = response.data[0]["progression"] if response.data else 0
    objectif = 200
    barre = int((progression / objectif) * 20) * "█" + int((1 - progression / objectif) * 20) * "░"
    embed = discord.Embed(title="Défi communautaire", color=0x00FF00)
    embed.add_field(name=f"Progrès : {progression}/{objectif}", value=barre, inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def collection(ctx):
    user_id = str(ctx.author.id)
    response = supabase.table("user_cards").select("card_id, rarity").eq("user_id", user_id).execute()
    cartes = response.data

    if not cartes:
        await ctx.send("Vous n'avez aucune carte.")
        return

    pages = []
    for c in cartes:
        carte_info = next((x for x in all_cards if x["id"] == c["card_id"]), None)
        if not carte_info:
            continue
        embed = discord.Embed(
            title=f"{rarity_emojis[c['rarity']]} {carte_info['name']}",
            color=rarity_colors[c['rarity']]
        )
        embed.set_image(url=carte_info["image"])
        embed.set_footer(text=f"Rareté : {c['rarity'].capitalize()} | Saison 0")
        pages.append(embed)

    if not pages:
        await ctx.send("Vous n'avez aucune carte.")
        return

    message = await ctx.send(embed=pages[0])
    await message.add_reaction("◀️")
    await message.add_reaction("▶️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message.id == message.id

    i = 0
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "▶️" and i < len(pages) - 1:
                i += 1
                await message.edit(embed=pages[i])
            elif str(reaction.emoji) == "◀️" and i > 0:
                i -= 1
                await message.edit(embed=pages[i])
            await message.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            break

@bot.command()
async def leaderboard(ctx):
    response = supabase.table("users").select("user_id, total_credits").order("total_credits", desc=True).limit(10).execute()
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



bot.run(TOKEN)







