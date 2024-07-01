from urllib.parse import quote_plus
import aiohttp
import settings
from mergedeep import merge
import datetime

app_token = str(settings.SHOPIFY_API_KEY)

# Check if SHOPIFY_URL ends with a slash
api_url = str(settings.SHOPIFY_URL) if str(settings.SHOPIFY_URL).endswith('/') else f"{str(settings.SHOPIFY_URL)}/"

headers = {
    'X-Shopify-Access-Token': app_token,
}

async def fetch_json(url: str, params: dict = None) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            return await response.json()

async def get_open_orders() -> int:
    response = await fetch_json(f'{api_url}orders/count.json', params={'status': 'open'})
    return response["count"]

async def order_list() -> dict:
    response = await fetch_json(f'{api_url}orders.json', params={'status': 'open'})
    return {
        order["order_number"]: {
            "year": order["created_at"][:4],
            "month": order["created_at"][5:7],
            "day": order["created_at"][8:10],
            "time": order["created_at"][11:16],
            "country": order["shipping_address"].get("country_code") or order["billing_address"].get("country_code"),
            "id": order["id"]
        }
        for order in response["orders"]
    }

async def closed_order_list() -> dict:
    response = await fetch_json(f'{api_url}orders.json', params={'status': 'any', 'limit': 150})
    return {
        order["order_number"]: {
            "year": order["created_at"][:4],
            "month": order["created_at"][5:7],
            "day": order["created_at"][8:10],
            "time": order["created_at"][11:16],
            "country": order["shipping_address"].get("country_code") or order["billing_address"].get("country_code"),
            "id": order["id"]
        }
        for order in response["orders"]
    }

async def closed_count(today: str) -> int:
    response = await fetch_json(f'{api_url}orders/count.json', params={'status': 'closed', 'created_at_min': today})
    return response["count"]

async def get_order(uuid: str) -> dict:
    orders = await order_list()
    order = orders.get(int(uuid))

    if not order:
        orders = await closed_order_list()
        order = orders.get(int(uuid))

        if not order:
            return {"error": "That order number doesn't exist."}

    url = f'https://clickeys-nl.myshopify.com/admin/api/2022-04/orders/{order["id"]}.json'
    response = await fetch_json(url)
    order_full = response['order']

    products = [(product['name'], product['quantity']) for product in order_full['line_items']]
    return {
        order_full['name']: {
            "name": order_full['shipping_address']['name'],
            "email": order_full['contact_email'],
            "price": order_full['total_line_items_price_set']['shop_money']['amount'],
            "country": order_full['shipping_address']['country_code'],
            "products": products
        }
    }

async def random_quote() -> str:
    api_url = 'https://api.api-ninjas.com/v1/facts'
    headers = {'X-Api-Key': str(settings.NINJA_KEY)}
    params = {'limit': 1}

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers, params=params) as response:
            response.raise_for_status()
            result = await response.json()
            return result[0]["fact"]

async def balance() -> str:
    response = await fetch_json(f'{api_url}shopify_payments/balance.json')
    return str(response['balance'][0]['amount'])
