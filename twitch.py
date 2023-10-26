import aiohttp
import asyncio
import schedule
import time
import aiosqlite
from datetime import datetime, timedelta
from discord_webhook import DiscordWebhook

class TwitchStreamAnnouncer:
    def __init__(self):
        self.discord_webhook_url = ""
        self.discord_webhook_delay = 5
        self.game_name = ""
        self.twitch_client_id = ""
        self.twitch_client_secret = ""
        self.twitch_game_id = ""
        self.twitch_max_streams = 100
        self.twitch_recheck_time = 600
        self.twitch_token_renewal_days = 21

    async def setup_database(self):
        self.conn = await aiosqlite.connect('announced_users.db')
        self.c = await self.conn.cursor()
        await self.c.execute('''CREATE TABLE IF NOT EXISTS announced_users
                               (username TEXT PRIMARY KEY, last_announcement_time TEXT)''')
        await self.conn.commit()

    async def load_announced_users(self):
        announced_users = {}
        await self.c.execute('SELECT * FROM announced_users')
        rows = await self.c.fetchall()
        for row in rows:
            username, last_announcement_time = row
            last_announcement_time = datetime.fromisoformat(last_announcement_time)
            announced_users[username] = last_announcement_time
        return announced_users

    async def save_announced_user(self, username, last_announcement_time):
        await self.c.execute('INSERT OR REPLACE INTO announced_users (username, last_announcement_time) VALUES (?, ?)',
                       (username, last_announcement_time.isoformat()))
        await self.conn.commit()

    async def get_app_access_token(self, client_id, client_secret):
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

    async def renew_access_token(self):
        twitch_oauth_token = await self.get_app_access_token(self.twitch_client_id, self.twitch_client_secret)
        if twitch_oauth_token:
            print("Twitch OAuth token renewed successfully.")
            return twitch_oauth_token
        else:
            print("Failed to obtain Twitch OAuth token. Cannot proceed.")
            return None

    async def check_for_new_users(self):
        announced_users = await self.load_announced_users()
        new_users = set()

        twitch_oauth_token = await self.renew_access_token()
        if twitch_oauth_token is None:
            print("Failed to renew Twitch OAuth token. Cannot proceed.")
            return

        url = "https://api.twitch.tv/helix/streams"
        params = {
            "game_id": self.twitch_game_id,
            "first": self.twitch_max_streams
        }
        headers = {
            "Client-ID": self.twitch_client_id,
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
                            await self.save_announced_user(user_login, now)

                    for user in new_users:
                        print(f"Announcing {user} via Discord webhook...")
                        webhook = DiscordWebhook(url=self.discord_webhook_url,
                                                 content=f"{user} is now streaming {self.game_name} on Twitch! https://twitch.tv/{user}")
                        webhook.execute()
                        await asyncio.sleep(self.discord_webhook_delay)
                else:
                    print(f"Request failed with status code: {response.status}")
                    if "error" in response.json():
                        print(response.json()["error"])

    async def main(self):
        await self.setup_database()
        while True:
            print("Checking for new users...")
            await self.check_for_new_users()
            schedule.run_pending()
            print(f"Waiting for {self.twitch_recheck_time} seconds before the next check...")
            await asyncio.sleep(self.twitch_recheck_time)

if __name__ == "__main__":
    announcer = TwitchStreamAnnouncer()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(announcer.main())
