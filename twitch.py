import aiohttp
import asyncio
import aiosqlite
from datetime import datetime, timedelta
from discord_webhook import DiscordWebhook
import json

DATABASE_NAME = 'announced_users.db'
CONFIG_FILE = 'twitch_config.json'

class TwitchStreamAnnouncer:
    def __init__(self, config):
        self.config = config
        self.session = aiohttp.ClientSession()

    async def setup_database(self):
        self.conn = await aiosqlite.connect(DATABASE_NAME)
        self.c = await self.conn.cursor()
        await self.c.execute('''
            CREATE TABLE IF NOT EXISTS announced_users
            (username TEXT PRIMARY KEY, last_announcement_time TEXT)
        ''')
        await self.conn.commit()

    async def get_announced_users(self):
        await self.c.execute('SELECT * FROM announced_users')
        rows = await self.c.fetchall()
        return {row[0]: datetime.fromisoformat(row[1]) for row in rows}

    async def save_announced_user(self, username, last_announcement_time):
        await self.c.execute('''
            INSERT OR REPLACE INTO announced_users (username, last_announcement_time)
            VALUES (?, ?)
        ''', (username, last_announcement_time.isoformat()))
        await self.conn.commit()

    async def get_app_access_token(self):
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": self.config["twitch_client_id"],
            "client_secret": self.config["twitch_client_secret"],
            "grant_type": "client_credentials"
        }
        async with self.session.post(url, params=params) as response:
            if response.status == 200:
                return (await response.json()).get("access_token")
            print(f"Failed to obtain access token. Status code: {response.status}")
            return None

    async def check_for_new_users(self):
        announced_users = await self.get_announced_users()
        twitch_oauth_token = await self.get_app_access_token()
        if not twitch_oauth_token:
            print("Failed to renew Twitch OAuth token. Cannot proceed.")
            return

        url = "https://api.twitch.tv/helix/streams"
        params = {"game_id": self.config["twitch_game_id"], "first": self.config["twitch_max_streams"]}
        headers = {"Client-ID": self.config["twitch_client_id"], "Authorization": f"Bearer {twitch_oauth_token}"}
        async with self.session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                now = datetime.now()
                data = await response.json()
                for stream in data.get("data", []):
                    user_login = stream.get('user_login')
                    last_announcement_time = announced_users.get(user_login)
                    if not last_announcement_time or (now - last_announcement_time) >= timedelta(hours=self.config["twitch_streamer_cooldown_hours"]):
                        print(f"Announcing {user_login} via Discord webhook...")
                        webhook = DiscordWebhook(url=self.config["discord_webhook_url"], content=f"{user_login} is now streaming {self.config['game_name']} on Twitch! https://twitch.tv/{user_login}")
                        webhook.execute()
                        await asyncio.sleep(self.config["discord_webhook_delay"])
                        await self.save_announced_user(user_login, now)
            else:
                print(f"Request failed with status code: {response.status}")
                if "error" in await response.json():
                    print((await response.json())["error"])

    async def main(self):
        await self.setup_database()
        while True:
            print("Checking for new users...")
            await self.check_for_new_users()
            print(f"Waiting for {self.config['twitch_recheck_seconds']} seconds before the next check...")
            await asyncio.sleep(self.config["twitch_recheck_seconds"])


def load_config():
    with open(CONFIG_FILE, 'r') as config_file:
        return json.load(config_file)


if __name__ == "__main__":
    config = load_config()
    announcer = TwitchStreamAnnouncer(config)
    asyncio.run(announcer.main())