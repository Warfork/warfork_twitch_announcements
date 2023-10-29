## warfork_twitch_announcements

This Python script periodically checks for new streamers on Twitch who are playing a specific game and announces them via a Discord webhook.

### Prerequisites

Before you start, make sure you have the following:

- **Twitch Developer Application**: You need to create a Twitch Developer Application and obtain a client_id and client_secret.
- **Discord Webhook URL**: Prepare a Discord webhook URL where the announcements will be sent.
- **Python 3**: Ensure you have Python 3 installed on your system.

#### Required Python Packages

You will need to install the following Python packages using pip:

- **aiohttp**: For making asynchronous HTTP requests.
- **aiosqlite**: For managing the SQLite database.
- **discord-webhook**: For sending announcements to Discord.

You can install these packages using the following command:

```bash
pip install aiohttp aiosqlite discord-webhook```

### Configuration

In order to use this script, you must correctly configure the `twitch_config.json` file with the following parameters:

- **discord_webhook_url**: Your Discord webhook URL where announcements will be sent.
- **discord_webhook_delay**: Delay in seconds between announcing new users (e.g., 5 seconds).
- **game_name**: The name of the game you want to track (e.g., "Warfork").
- **twitch_client_id**: Your Twitch Developer Application client ID.
- **twitch_client_secret**: Your Twitch Developer Application client secret.
- **twitch_game_id**: The Twitch Game ID for the game you want to track.
- **twitch_max_streams**: The maximum number of streams to retrieve from Twitch.
- **twitch_recheck_seconds**: Time in seconds between checks for new users.
- **twitch_token_renewal_days**: How often the Twitch OAuth token should be renewed.
- **twitch_streamer_cooldown_hours**: Cooldown period in hours before announcing the same streamer again.
