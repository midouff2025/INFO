import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def check_ban(uid):
    api_url = f"https://api.paulalfredo.me/check_ban/{uid}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status != 200:
                    return None
                data = await response.json()
                if data.get("status") == 200:
                    info = data.get("data")
                    return {
                        "is_banned": info.get("is_banned", 0),
                        "nickname": info.get("nickname", ""),
                        "period": info.get("period", 0),
                        "region": info.get("region", "N/A")
                    }
                return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
