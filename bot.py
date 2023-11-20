import os
import discord
from discord.ext import commands
import requests
from pymongo import MongoClient
import logging

# Setting up environment variables
MONGODB_CONN_STRING = os.getenv('MONGODB_CONN_STRING')
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize Logging
logging.basicConfig(level=logging.INFO)

# Initialize MongoDB Connection
try:
    mongo_client = MongoClient(MONGODB_CONN_STRING)
    db = mongo_client['discordBotDB']
    collection = db['userPreferences']  # Example collection
    logging.info("MongoDB connected successfully.")
except Exception as e:
    logging.error(f"Error connecting to MongoDB: {e}")
    exit(1)

# Define Intents for the Bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

# Discord Bot Setup
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logging.info(f'{bot.user.name} has connected to Discord!')

@bot.command(name='generate', help='Generates an image from a prompt')
async def generate_image(ctx, *, prompt: str):
    try:
        image_url = call_huggingface_api(prompt)
        await ctx.send(image_url)
    except Exception as e:
        await ctx.send("Sorry, I couldn't process the image generation.")
        logging.error(f"Error in generate_image: {e}")

def call_huggingface_api(prompt):
    try:
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
        data = {"inputs": prompt}

        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()  # Raises HTTPError for bad requests
        image_url = response.json()[0]  # Extract image URL from response
        return image_url
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error: {e}")
        raise

if __name__ == "__main__":
    if DISCORD_TOKEN is None:
        logging.error("DISCORD_TOKEN is not set. Please set the token and retry.")
        exit(1)
    bot.run(DISCORD_TOKEN)
