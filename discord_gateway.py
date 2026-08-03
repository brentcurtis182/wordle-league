#!/usr/bin/env python3
"""Discord Gateway listener — lets players post scores by simply pasting them.

Why this exists as its own always-on service:

Twilio and Slack PUSH incoming messages to us over HTTP webhooks, so the web
app can receive them. Discord does not — ordinary channel messages are only
delivered over a persistent Gateway WebSocket. Without this process, the only
way to submit a Discord score is a slash command, which kills the reflex that
makes Wordle sharing work (copy, paste, done). This closes that gap so Discord
behaves exactly like SMS.

Requires the MESSAGE CONTENT privileged intent, enabled on the bot in the
Discord developer portal. Without it Discord delivers empty `content` for every
message and nothing will ever parse — silently. The startup check below fails
loudly instead.

Scores are parsed and processed by handle_discord_message(), the same path the
slash command uses, which in turn calls the shared process_wordle_score() — so
Discord scores go through identical logic to SMS and Slack.

Run as a long-lived Railway service (NOT a cron):
    python discord_gateway.py
"""
import os
import sys
import asyncio
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

try:
    import discord
except ImportError:
    logging.error("discord.py is not installed — add discord.py to requirements.txt")
    raise


def _build_payload(message):
    """Shape a discord.py Message like the raw Gateway dict handle_discord_message expects."""
    return {
        "content": message.content or "",
        "author": {
            "id": str(message.author.id),
            "username": message.author.name,
            "global_name": getattr(message.author, "global_name", None),
            "bot": bool(message.author.bot),
        },
        "channel_id": str(message.channel.id),
        "guild_id": str(message.guild.id) if message.guild else None,
    }


class ScoreListener(discord.Client):
    async def on_ready(self):
        guilds = ", ".join(f"{g.name} ({g.id})" for g in self.guilds) or "none"
        logging.info(f"Discord gateway connected as {self.user} | guilds: {guilds}")
        if not self.intents.message_content:
            logging.error("MESSAGE CONTENT intent is OFF — message text will be empty and no "
                          "score can ever be parsed. Enable it in the Discord developer portal.")

    async def on_message(self, message):
        # Never react to ourselves or other bots.
        if message.author.bot or message.author.id == (self.user.id if self.user else None):
            return
        if not message.content:
            return

        payload = _build_payload(message)

        def _process():
            # Imported lazily so a DB/import problem can't stop the gateway booting.
            from league_data_adapter import get_db_connection
            from discord_integration import handle_discord_message
            conn = get_db_connection()
            try:
                return handle_discord_message(payload, conn)
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

        try:
            # handle_discord_message is synchronous (psycopg2); keep the event
            # loop free so one slow query can't stall the gateway heartbeat.
            result = await asyncio.to_thread(_process)
        except Exception as e:
            logging.error(f"Discord score handling failed: {e}")
            return

        status = (result or {}).get("status")
        if status == "processed":
            logging.info(f"Processed Discord score from {message.author} in #{message.channel}")
            try:
                await message.add_reaction("✅")
            except Exception:
                pass  # reaction is a nicety, never worth failing the score over
        elif status == "error" and (result or {}).get("reason") == "league_not_found":
            logging.warning(f"No league mapped to guild {payload['guild_id']} channel {payload['channel_id']}")


def main():
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit("DISCORD_BOT_TOKEN not set")

    intents = discord.Intents.default()
    intents.message_content = True  # privileged — must also be enabled in the dev portal

    client = ScoreListener(intents=intents)
    # discord.py reconnects and resumes on its own; let it own the retry loop.
    client.run(token, reconnect=True)


if __name__ == "__main__":
    main()
