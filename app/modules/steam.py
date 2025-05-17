import re
import json
from bs4 import BeautifulSoup
from aiohttp import ClientSession
from urllib.parse import unquote, quote



class SteamItem:
    def __init__(self, market_hash_name: str, app_id: str, icon_url: str, type: str, price_history: list[list], url: str):
        self.market_hash_name = market_hash_name
        self.app_id = app_id
        self.icon_url = f"https://community.cloudflare.steamstatic.com/economy/image/{icon_url}"
        self.type = type
        self.price_history = price_history
        self.url = url



class SteamAPI:
    async def get_url_from_message(self, text: str) -> tuple[str, str]:
        status = "ok"
        url = None

        try:
            parts = text.split(" ")
            url = parts[0] if parts else None

            if not url:
                raise ValueError("не удалось найти валидную steam-ссылку в вашем сообщении")

        except Exception as e:
            status = f"get_url_from_message - {e}"

        return status, url



    async def get_params_from_url(self, url: str) -> tuple[str, int, str]:
        status = "ok"
        app_id = None
        market_hash_name = None

        try:
            pattern = r'https://steamcommunity\.com/market/listings/(\d+)/([^?]+)'
            match = re.match(pattern, url)
            
            app_id = int(match.group(1))
            market_hash_name = str(unquote(match.group(2)))

        except Exception as e:
            status = f"get_params_from_url - {e}"

        return status, app_id, market_hash_name



    async def get_usd_rate(self) -> tuple[str, float]:
        status = "ok"
        usd_rate = 0

        try:
            return status, 82.18

            # TODO: проверить апи сервиса, последнее время барахлит
            
            url = "https://sert.somespecial.one/history"
            async with ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()
                    history = data["RUB"]
                    usd_rate = float(history[0][0])
        
        except Exception as e:
            status = f"get_usd_rate - {e}"
        
        return status, usd_rate



    async def get_item(self, app_id: int, market_hash_name: str) -> tuple[str, SteamItem]:
        status = "ok"
        steam_item = None

        try:
            status, usd_rate = await self.get_usd_rate()

            if status != "ok":
                raise ValueError(status)

            params = { "country" : "EU", "language" : "english", "currency" : "1", }

            url = f"https://steamcommunity.com/market/listings/{app_id}/{quote(market_hash_name)}"
            
            async with ClientSession() as session:
                async with session.get(url, params = params) as response:
                    if response.status != 200:
                        raise ValueError(f"не удалось отправить запрос, код {response.status}")
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, "lxml")

                    scripts = soup.find_all("script")

                    embedded_data_script = None

                    for script in scripts:
                        if script.string and "var g_rgAssets" in script.string:
                            embedded_data_script = script.string
                            break

                    if not embedded_data_script:
                        raise ValueError("не удалось найти встроенные данные на странице")

                    embedded_data = embedded_data_script.split("var g_rgAssets = ")[1].split("}}}};")[0] + "}}}}"
                    item_info_data = json.loads(embedded_data)[str(app_id)]
                    item_info_data = item_info_data[next(iter(item_info_data))]
                    item_info_data = item_info_data[next(iter(item_info_data))]

                    price_data_script = None
                    
                    for script in scripts:
                        if script.string and "var line1=" in script.string:
                            price_data_script = script.string
                            break

                    if not price_data_script:
                        raise ValueError("не удалось найти данные о ценах на странице")

                    price_data = price_data_script.split("var line1=")[1].split(";")[0]
                    price_history = [[entry[0], round(float(entry[1]) * usd_rate, 3), entry[2]] for entry in json.loads(price_data)]

                    steam_item = SteamItem(
                        market_hash_name = item_info_data["market_hash_name"],
                        app_id = app_id,
                        icon_url = item_info_data["icon_url"],
                        type = item_info_data["type"],
                        price_history = price_history,
                        url = url,
                    )
        
        except Exception as e:
            status = f"get_item - {e}"

        return status, steam_item



async def get_steam_item_from_url(text: str) -> tuple[str, SteamItem]:
    status = "ok"
    steam_item = None

    try:
        status, url = await api.get_url_from_message(text)

        if status != "ok":
            raise ValueError(status)

        status, app_id, market_hash_name = await api.get_params_from_url(url)

        if status != "ok":
            raise ValueError(status)

        status, steam_item = await api.get_item(app_id, market_hash_name)

    except Exception as e:
        status = f"get_steam_item_from_url - {e}"

    return status, steam_item



api = SteamAPI()