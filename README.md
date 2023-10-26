## warfork_twitch_announcements

This Python script periodically checks for new streamers on Twitch who are playing a specific game and announces them via a Discord webhook.

## Prerequisites

Before you start, make sure you have the following:

- Twitch Developer Application with client_id and client_secret
- Discord Webhook URL
- Python 3

Required Python packages:

- aiohttp
- schedule
- aiosqlite
- discord-webhook

You can install the required packages with the following command:

- pip install aiohttp schedule aiosqlite discord-webhook

## Configuration 

Ensure these parameters are correctly set in the twitch_config.json file.

- discord_webhook_url: Your Discord webhook URL where announcements will be sent.
- discord_webhook_delay: Delay in seconds between announcing new users (e.g., 5 seconds).
- game_name: The name of the game you want to track (e.g., "Warfork").
- twitch_client_id: Your Twitch Developer Application client ID.
- twitch_client_secret: Your Twitch Developer Application client secret.
- twitch_game_id: The Twitch Game ID for the game you want to track.
- twitch_max_streams: The maximum number of streams to retrieve from Twitch.
- twitch_recheck_seconds: Time in seconds between checks for new users.
- twitch_token_renewal_days: How often the Twitch OAuth token should be renewed.
- twitch_streamer_cooldown_hours: Cooldown period in hours before announcing the same streamer again.