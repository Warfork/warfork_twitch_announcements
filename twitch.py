import requests
import time
from datetime import datetime, timedelta
from discord_webhook import DiscordWebhook

# Credentials
oauth_token = ""
game_name = "Warfork"
discord_webhook_url = ""

def load_announced_users(filename):
    announced_users = {}
    try:
        with open(filename, 'r') as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    username, last_announcement_time = parts
                    last_announcement_time = datetime.fromisoformat(last_announcement_time)
                    announced_users[username] = last_announcement_time
    except FileNotFoundError:
        pass
    return announced_users

def save_announced_users(filename, announced_users):
    with open(filename, 'w') as file:
        for username, last_announcement_time in announced_users.items():
            file.write(f"{username},{last_announcement_time.isoformat()}\n")

def check_for_new_users():
    announced_users = load_announced_users("announced_users.txt")
    new_users = set()

    url = "https://api.twitch.tv/helix/streams"
    params = {
        "game_name": game_name,
        "first": 100  # Max Streams
    }
    headers = {
        "Client-ID": "",  # Twitch API client ID
        "Authorization": f"Bearer {oauth_token}"
    }
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()
        now = datetime.now()
        for stream in data.get("data", []):
            user_login = stream.get('user_login')
            last_announcement_time = announced_users.get(user_login)
            if last_announcement_time is None or (now - last_announcement_time) >= timedelta(hours=1):
                new_users.add(user_login)
                announced_users[user_login] = now

        for user in new_users:
            webhook = DiscordWebhook(url=discord_webhook_url, content=f"{user} is now streaming Warfork on Twitch! https://twitch.tv/{user}")
            webhook.execute()
            time.sleep(5) # 5 second delay between messages

        save_announced_users("announced_users.txt", announced_users)
    else:
        print(f"Request failed with status code: {response.status_code}")
        if "error" in response.json():
            print(response.json()["error"])

if __name__ == "__main__":
    while True:
        check_for_new_users()
        time.sleep(600) # Check every 600 seconds

