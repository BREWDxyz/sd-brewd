import os
import discord
from discord.ext import commands
from huggingface_hub import InferenceClient
from pymongo import MongoClient
import logging
import requests
from PIL import Image
from io import BytesIO
import datetime

# Environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
MONGODB_CONN_STRING = os.getenv('MONGODB_CONN_STRING')
IMGUR_CLIENT_ID = os.getenv('IMGUR_CLIENT_ID')

# Initialize MongoDB client
mongo_client = MongoClient(MONGODB_CONN_STRING)
db = mongo_client.image_generation_db  # Replace with your actual MongoDB database name
collection = db.generated_images  # Replace with your actual collection name

# Initialize Hugging Face Inference Client for SDXL
sdxl_client = InferenceClient(model="stabilityai/stable-diffusion-xl-base-1.0", token=HUGGINGFACE_TOKEN)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Discord bot setup with intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logging.info(f'{bot.user.name} has connected to Discord!')
    logging.info('MongoDB connected successfully.')

@bot.command(name='generate', help='Generates an image from a prompt')
async def generate_image(ctx, *, prompt: str):
    try:
        # Generate image using Hugging Face model
        image = sdxl_client.text_to_image(prompt, guidance_scale=9)
        image_url = save_image_to_imgur(image)

        # Log and save to MongoDB
        document = {
            "user_id": ctx.author.id,
            "prompt": prompt,
            "image_url": image_url,
            "timestamp": datetime.datetime.utcnow()
        }
        collection.insert_one(document)

        await ctx.send(image_url)
    except Exception as e:
        logging.error(f'Error generating image: {e}')
        await ctx.send("Sorry, I couldn't process the image generation.")

def save_image_to_imgur(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = buffered.getvalue()

    headers = {'Authorization': f'Client-ID {IMGUR_CLIENT_ID}'}
    response = requests.post(
        'https://api.imgur.com/3/image',
        headers=headers,
        data={'image': img_str}
    )

    if response.status_code == 200:
        return response.json()['data']['link']
    else:
        logging.error(f'Imgur upload failed: {response.content}')
        return None

bot.run(DISCORD_TOKEN)
