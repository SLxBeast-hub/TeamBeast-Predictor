import discord
from discord.ext import commands
import json
import os
import datetime
import openai

# ========== CONFIGURATION ==========
DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN"
OPENAI_API_KEY = "YOUR_OPENAI_API"
openai.api_key = OPENAI_API_KEY

HISTORY_ALL_FILE = "history_all.json"
HISTORY_RECENT_FILE = "history_recent.json"
MAX_RECENT = 20

LIME_COLOR = discord.Color.from_rgb(50, 205, 50)  # Lime green color

# ========== INITIALIZATION ==========
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== HELPERS ==========
def load_history(file):
    if not os.path.exists(file):
        return []
    try:
        with open(file, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_history(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def add_round(color, status):
    all_history = load_history(HISTORY_ALL_FILE)
    recent_history = load_history(HISTORY_RECENT_FILE)

    round_number = len(all_history) + 1
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = {
        "round": round_number,
        "status": status.upper(),
        "color": color.upper(),
        "timestamp": timestamp,
        "source": "Coinryze"
    }

    all_history.append(entry)
    recent_history.append(entry)
    if len(recent_history) > MAX_RECENT:
        recent_history.pop(0)

    save_history(HISTORY_ALL_FILE, all_history)
    save_history(HISTORY_RECENT_FILE, recent_history)

def format_history_text(history):
    if not history:
        return "No history found."
    lines = [
        f"Round {item['round']}: [{item['status']}] {item['color']} at {item['timestamp']} ({item['source']})"
        for item in history
    ]
    return "\n".join(lines)

async def get_gpt_prediction(recent_history):
    prompt = """
You are a professional color predictor for a game called Coinryze, where players choose RED, GREEN, or VIOLET based on previous results. Predict the next most likely color based on the last 20 results. Return only the color name (RED, GREEN, or VIOLET).

Recent results:
"""
    for item in recent_history:
        prompt += f"- {item['result']}\n"

    prompt += "\nPrediction:"

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful predictor."},
            {"role": "user", "content": prompt}
        ]
    )

    prediction = response.choices[0].message.content.strip()
    return prediction

# ========== EVENTS ==========
@bot.event
async def on_ready():
    print(f"✅ Bot is now online as {bot.user}")

     
     #Send a ready message to a specific channel if needed (optional)
    channel_id = 1381914810425413675  # Replace with your channel ID
    channel = bot.get_channel(channel_id)
    if channel:
        embed = discord.Embed(
            title=f"✅ Bot is now online as {bot.user}",
            description="🔥 Get Ready to Earn Money with TeamBeast Predictions! 💰\nType `!predict` to start your winning streak!",
            color=LIME_COLOR
        )
        await channel.send(embed=embed)

# ========== COMMANDS ==========
@bot.command()
async def predict(ctx):
    recent = load_history(HISTORY_RECENT_FILE)
    if len(recent) < 5:
        embed = discord.Embed(
            description="⚠️ Need at least 5 rounds of history to predict. Use !win or !lose to add.",
            color=LIME_COLOR
        )
        await ctx.send(embed=embed)
        return

    await ctx.message.delete()
    prediction = await get_gpt_prediction(recent)
    embed = discord.Embed(
        title="🎯 Prediction Result",
        description=f"Based on the last {len(recent)} rounds, my next color prediction is:",
        color=LIME_COLOR
    )
    embed.add_field(name="🧠 GPT Suggests", value=f"**{prediction.upper()}**", inline=False)
    embed.set_footer(text="Prediction powered by GPT-4o AI")
    await ctx.send(embed=embed)

@bot.command()
async def win(ctx, color: str):
    await ctx.message.delete()
    add_round(color, "WIN")
    embed = discord.Embed(
        title="✅ Win Recorded",
        description=f"Round added as WIN for **{color.upper()}**. Let's keep tracking! 🧠",
        color=LIME_COLOR
    )
    await ctx.send(embed=embed)

@bot.command()
async def lose(ctx, color: str):
    await ctx.message.delete()
    add_round(color, "LOSE")
    embed = discord.Embed(
        title="❌ Loss Recorded",
        description=f"Round logged as LOSE for **{color.upper()}**. Learning from this, adjusting strategy! 🔄",
        color=LIME_COLOR
    )
    await ctx.send(embed=embed)

@bot.command(name="showhistory")
async def showhistory(ctx):
    await ctx.message.delete()
    all_data = load_history(HISTORY_ALL_FILE)
    text = format_history_text(all_data)
    with open("history.txt", "w", encoding="utf-8") as f:
        f.write(text)
    embed = discord.Embed(
        title="📜 Full History Log",
        description="Here's the full history log so far. (Sent as a file)",
        color=LIME_COLOR
    )
    await ctx.send(embed=embed)
    await ctx.send(file=discord.File("history.txt"))

@bot.command(name="history")
async def history(ctx):
    await ctx.message.delete()
    recent = load_history(HISTORY_RECENT_FILE)
    if not recent:
        embed = discord.Embed(description="📜 No recent history found.", color=LIME_COLOR)
        await ctx.send(embed=embed)
        return
    text = format_history_text(recent)
    embed = discord.Embed(title="📜 Last 20 Rounds History", description=text, color=LIME_COLOR)
    await ctx.send(embed=embed)

@bot.command()
async def reset(ctx):
    await ctx.message.delete()
    save_history(HISTORY_ALL_FILE, [])
    save_history(HISTORY_RECENT_FILE, [])
    embed = discord.Embed(
        title="🔄 History Reset",
        description="All history has been reset. Starting fresh!",
        color=LIME_COLOR
    )
    await ctx.send(embed=embed)

@bot.command()
async def status(ctx):
    await ctx.message.delete()
    recent = load_history(HISTORY_RECENT_FILE)
    all_data = load_history(HISTORY_ALL_FILE)
    embed = discord.Embed(
        title="📊 Current Stats",
        description=f"- Total rounds: {len(all_data)}\n- Recent rounds (last 20): {len(recent)}",
        color=LIME_COLOR
    )
    await ctx.send(embed=embed)

@bot.command()
async def say(ctx, *, msg):
    await ctx.message.delete()
    embed = discord.Embed(
        description=f"📢 {msg}",
        color=LIME_COLOR
    )
    await ctx.send(embed=embed)

@bot.command()
async def clearchat(ctx):
    await ctx.channel.purge()
    embed = discord.Embed(
        title="🧹 Chat Cleared",
        description="Chat cleared!",
        color=LIME_COLOR
    )
    await ctx.send(embed=embed)

# ========== RUN BOT ==========
bot.run(DISCORD_TOKEN)
