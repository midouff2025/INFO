import discord
from discord.ext import commands, tasks
from flask import Flask
import threading
import os
import asyncio
import aiohttp

# --- Flask Keep-Alive ---
app = Flask(__name__)
bot_name = "Loading..."

@app.route("/")
def home():
    return f"Bot {bot_name} is operational"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DEFAULT_LANG = "en"
user_languages = {}

# --- Keep-Alive Task ---
async def keep_alive():
    url = "https://info-1-rngw.onrender.com"
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await session.get(url)
            except Exception as e:
                print(f"⚠️ Keep-Alive error: {e}")
            await asyncio.sleep(300)  # كل 5 دقائق

# --- Check Ban Function ---
async def check_ban(uid):
    api_url = f"https://rawthug.onrender.com/check_ban/{uid}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status != 200:
                    return None
                data = await response.json()
                if data.get("status") == 200:
                    info = data.get("data", {})
                    return {
                        "is_banned": info.get("is_banned", 0),
                        "nickname": info.get("nickname", "Unknown"),
                        "period": info.get("period", 0),
                        "region": info.get("region", "N/A")
                    }
                return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# --- Bot Events ---
@bot.event
async def on_ready():
    global bot_name
    bot_name = str(bot.user)
    print(f"✅ Bot connected as {bot.user} ({len(bot.guilds)} servers)")

    # Start Flask Keep-Alive in background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🚀 Flask server started in background")

    # Start periodic status update
    update_status.start()

# --- Bot Commands ---
@bot.command(name="lang")
async def change_language(ctx, lang_code: str):
    lang_code = lang_code.lower()
    if lang_code not in ["en", "fr"]:
        await ctx.send("❌ Invalid language. Available: `en`, `fr`")
        return
    user_languages[ctx.author.id] = lang_code
    message = "✅ Language set to English." if lang_code == 'en' else "✅ Langue définie sur le français."
    await ctx.send(f"{ctx.author.mention} {message}")

@bot.command(name="ID")
async def check_ban_command(ctx):
    content = ctx.message.content
    user_id = content[3:].strip()
    lang = user_languages.get(ctx.author.id, DEFAULT_LANG)

    if not user_id.isdigit():
        msg = {
            "en": f"{ctx.author.mention} ❌ **Invalid UID!**",
            "fr": f"{ctx.author.mention} ❌ **UID invalide !**"
        }
        await ctx.send(msg[lang])
        return

    try:
        ban_status = await check_ban(user_id)
    except Exception as e:
        await ctx.send(f"{ctx.author.mention} ⚠️ Error:\n```{str(e)}```")
        return

    if ban_status is None:
        msg = {
            "en": f"{ctx.author.mention} ❌ Could not get information. Please try again later.",
            "fr": f"{ctx.author.mention} ❌ Impossible d'obtenir les informations. Veuillez réessayer plus tard."
        }
        await ctx.send(msg[lang])
        return

    is_banned = int(ban_status.get("is_banned", 0))
    period = ban_status.get("period", "N/A")
    nickname = ban_status.get("nickname", "NA")
    region = ban_status.get("region", "N/A")

    embed = discord.Embed(
        color=0xFF0000 if is_banned else 0x00FF00,
        timestamp=ctx.message.created_at
    )

    if is_banned:
        embed.title = "**▌ Banned Account 🛑 **" if lang == "en" else "**▌ Compte banni 🛑 **"
        embed.description = (
            f"**• {'Reason' if lang=='en' else 'Raison'}:** This account used cheats.\n"
            f"**• {'Duration' if lang=='en' else 'Durée'}:** {period}\n"
            f"**• {'Nickname' if lang=='en' else 'Pseudo'}:** {nickname}\n"
            f"**• {'Region' if lang=='en' else 'Région'}:** {region}"
        )
        embed.set_image(url="https://i.ibb.co/4gj5P7DH/banned.gif")
    else:
        embed.title = "**▌ Clean Account ✅ **" if lang == "en" else "**▌ Compte non banni ✅ **"
        embed.description = (
            f"**• {'Status' if lang=='en' else 'Statut'}:** No evidence of cheats.\n"
            f"**• {'Nickname' if lang=='en' else 'Pseudo'}:** {nickname}\n"
            f"**• {'Region' if lang=='en' else 'Région'}:** {region}"
        )
        embed.set_image(url="https://i.ibb.co/SwKrD67z/notbanned.gif")

    embed.set_footer(text="📌 Garena Free Fire")
    embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.send(embed=embed)

# --- Periodic Bot Status ---
@tasks.loop(minutes=5)
async def update_status():
    try:
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servers")
        await bot.change_presence(activity=activity)
    except Exception as e:
        print(f"⚠️ Status update failed: {e}")

# --- Run Bot ---
async def main():
    # Start Keep-Alive task
    asyncio.create_task(keep_alive())
    # Run bot directly; التوكن سيأخذه من Environment على Render
    async with bot:
       await bot.start(os.environ.get("TOKEN"))

"))

if __name__ == "__main__":
    asyncio.run(main())
