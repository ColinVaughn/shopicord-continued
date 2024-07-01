import datetime
import logging
import aiohttp
import discord
from discord.ext import commands
import settings
import shopify_api as sapi  # Assuming this module supports async operations

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

authors = [257360542904090624]  # List of Discord User ID's of people that are allowed to use the bot

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

def is_us(author_id: int) -> bool:
    return author_id in authors

async def return_closed_orders() -> str:
    current_date = datetime.date.today()
    first_day_of_month = datetime.date(current_date.year, current_date.month, 1)
    first_day_of_month_str = first_day_of_month.isoformat()  # Convert to string in YYYY-MM-DD format
    closed_order_count = await sapi.closed_count(first_day_of_month_str)
    return f"**Shopify Closed:** {closed_order_count}"

async def get_balance() -> str:
    balance = await sapi.balance()
    return f"**Shopify Balance:** €{balance}\n"

async def random_quote() -> str:
    api_url = "https://api.api-ninjas.com/v1/facts"
    headers = {
        'X-Api-Key': settings.NINJA_KEY
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            logger.debug(f"Request URL: {response.url}")
            logger.debug(f"Request Headers: {response.request_info.headers}")
            logger.debug(f"Response Status: {response.status}")
            if response.status != 200:
                logger.error(f"Bad Request Response Text: {await response.text()}")
            response.raise_for_status()  # Raises an exception for 4xx/5xx responses
            data = await response.json()
            if data:
                return data[0]['fact']  # Assuming the fact is in 'fact' key
            else:
                return "No quote found"

@bot.command(name='orders')
async def orders(ctx):
    if is_us(ctx.author.id):
        shopify_orders = await sapi.get_open_orders()
        shopify = f"**Orders: **{shopify_orders}"

        shopify_desc = ""
        if int(shopify_orders) > 0:
            shopify_dict = await sapi.order_list()
            if shopify_dict:
                shopify_message = ""
                for key, value in shopify_dict.items():
                    if isinstance(value, dict):
                        shopify_message += f"**#{key}** - {value['day']}/{value['month']}/{value['year']} - Time: **{value['time']}** - **{value['country']}**\n"
                shopify_desc = f"**Shopify:**\n{shopify_message}\n"

        shopify_desc_closed = await return_closed_orders()
        shopify_balance = await get_balance()

        description = f"{shopify}\n\n"
        if shopify_desc:
            description += f"{shopify_desc}{shopify_desc_closed}\n{shopify_balance}"
        else:
            quote = await random_quote()
            description += f"{quote}\n\n{shopify_desc_closed}\n{shopify_balance}"

        orders_embed = discord.Embed(
            description=description,
            colour=discord.Colour.blurple()
        )
        await ctx.author.send(embed=orders_embed)

@bot.command(name='order')
async def order(ctx, uuid: str):
    if is_us(ctx.author.id):
        order_dict = await sapi.get_order(uuid)
        shopify_message = ""
        if isinstance(order_dict, dict):
            for key in order_dict:
                products = "".join([f"{product[0]} - **Quantity** {product[1]}\n" for product in order_dict[key]['products']])
                shopify_message += (f"**{key}**\n"
                                    f"**Name: **{order_dict[key]['name']}\n"
                                    f"**Email: **{order_dict[key]['email']}\n"
                                    f"**Price: **€{order_dict[key]['price']}\n"
                                    f"**Country: **{order_dict[key]['country']}\n\n"
                                    f"**Products:**\n{products}")
            order_embed = discord.Embed(
                description=shopify_message,
                colour=discord.Colour.blurple()
            )
        else:
            order_embed = discord.Embed(
                description=str(order_dict),
                colour=discord.Colour.blurple()
            )
        await ctx.author.send(embed=order_embed)

bot.run(settings.DISCORD_WEBHOOK)
