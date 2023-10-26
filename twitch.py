import aiohttp
import asyncio
import schedule
import time
import sqlite3
from datetime import datetime, timedelta
from discord_webhook import DiscordWebhook

# Settings
discord_webhook_url = ""
discord_webhook_delay = 5
game_name = ""
twitch_client_id = ""
twitch_client_secret = ""
twitch_game_id = ""
twitch_max_streams = 100
twitch_recheck_time = 600
twitch_token_renewal_days = 21

conn = sqlite3.connect('announced_users.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS announced_users
             (username TEXT PRIMARY KEY, last_announcement_time TEXT)''')
conn.commit()

async def load_announced_users():
    announced_users = {}
    c.execute('SELECT * FROM announced_users')
    rows = c.fetchall()
    for row in rows:
        username, last_announcement_time = row
        last_announcement_time = datetime.fromisoformat(last_announcement_time)
        announced_users[username] = last_announcement_time
    return announced_users

async def save_announced_user(username, last_announcement_time):
    c.execute('INSERT OR REPLACE INTO announced_users (username, last_announcement_time) VALUES (?, ?)',
              (username, last_announcement_time.isoformat()))
    conn.commit()

async def get_app_access_token(client_id, client_secret):
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("access_token")
            else:
                print(f"Failed to obtain access token. Status code: {response.status}")
                return None

async def renew_access_token():
    twitch_oauth_token = await get_app_access_token(twitch_client_id, twitch_client_secret)
    if twitch_oauth_token:
        print("Twitch OAuth token renewed successfully.")
        return twitch_oauth_token
    else:
        print("Failed to obtain Twitch OAuth token. Cannot proceed.")
        return None

async def check_for_new_users():
    announced_users = await load_announced_users()
    new_users = set()

    twitch_oauth_token = await renew_access_token()
    if twitch_oauth_token is None:
        print("Failed to renew Twitch OAuth token. Cannot proceed.")
        return

    url = "https://api.twitch.tv/helix/streams"
    params = {
        "game_id": twitch_game_id,
        "first": twitch_max_streams
    }
    headers = {
        "Client-ID": twitch_client_id,
        "Authorization": f"Bearer {twitch_oauth_token}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                now = datetime.now()
                for stream in data.get("data", []):
                    user_login = stream.get('user_login')
                    last_announcement_time = announced_users.get(user_login)
                    if last_announcement_time is None or (now - last_announcement_time) >= timedelta(hours=1):
                        new_users.add(user_login)
                        await save_announced_user(user_login, now)

                for user in new_users:
                    print(f"Announcing {user} via Discord webhook...")
                    webhook = DiscordWebhook(url=discord_webhook_url,
                                             content=f"{user} is now streaming {game_name} on Twitch! https://twitch.tv/{user}")
                    webhook.execute()
                    await asyncio.sleep(discord_webhook_delay)
            else:
                print(f"Request failed with status code: {response.status}")
                if "error" in response.json():
                    print(response.json()["error"])

async def main():
    while True:
        print("Checking for new users...")
        await check_for_new_users()
        schedule.run_pending()
        print(f"Waiting for {twitch_recheck_time} seconds before the next check...")
        await asyncio.sleep(twitch_recheck_time)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
