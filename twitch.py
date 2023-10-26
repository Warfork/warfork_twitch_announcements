import requests
import schedule
import time
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
twitch_oauth_token = ""
twitch_recheck_time = 600
twitch_token_renewal_days = 21

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

def get_app_access_token(client_id, client_secret):
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    response = requests.post(url, params=params)

    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"Failed to obtain access token. Status code: {response.status_code}")
        return None

def renew_access_token():
    global twitch_oauth_token
    twitch_oauth_token = get_app_access_token(twitch_client_id, twitch_client_secret)

def check_for_new_users():
    announced_users = load_announced_users("announced_users.txt")
    new_users = set()

    global twitch_oauth_token
    if not twitch_oauth_token:
        renew_access_token()
        if not twitch_oauth_token:
            print("Failed to obtain Twitch OAuth token. Cannot proceed.")
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
            webhook = DiscordWebhook(url=discord_webhook_url, content=f"{user} is now streaming {game_name} on Twitch! https://twitch.tv/{user}")
            webhook.execute()
            time.sleep(discord_webhook_delay)

        save_announced_users("announced_users.txt", announced_users)
    else:
        print(f"Request failed with status code: {response.status_code}")
        if "error" in response.json():
            print(response.json()["error"])

if __name__ == "__main__":

    schedule.every(twitch_token_renewal_days).days.do(renew_access_token)

    while True:

        check_for_new_users()
        schedule.run_pending()
        time.sleep(twitch_recheck_time)
