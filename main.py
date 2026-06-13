import datetime
import os
import re
from typing import Literal
import json
from dotenv import load_dotenv

import discord
from discord import app_commands

# Load .env file
load_dotenv()

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

# --- Load data from JSON files ---

def load_json(filepath, default_data):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_data

guild_settings = load_json("data/guild_settings.json", {})
ngwords = load_json("data/ngwords.json", {})
penalties = load_json("data/penalties.json", {})
locales = load_json("locales/locales.json", {})
fallback_mutes = load_json("data/fallback_mutes.json", {})

def fallback_mutes_save():
    with open("data/fallback_mutes.json", "w", encoding="utf-8") as f:
        json.dump(fallback_mutes, f, indent=4, ensure_ascii=False)

def ngwords_save():
    with open("data/ngwords.json", "w", encoding="utf-8") as f:
        json.dump(ngwords, f, indent=4, ensure_ascii=False)

def penalties_save():
    with open("data/penalties.json", "w", encoding="utf-8") as f:
        json.dump(penalties, f, indent=4, ensure_ascii=False)

def guild_settings_save():
    with open("data/guild_settings.json", "w", encoding="utf-8") as f:
        json.dump(guild_settings, f, indent=4, ensure_ascii=False)

def _(phrase_key, locale="en"):
    return locales.get(locale, {}).get(phrase_key, phrase_key)


# --- Utility functions ---

def parse_duration(duration_str: str) -> datetime.timedelta | None:
    """Parse a duration string (e.g., "10s", "5m", "2h", "1d") and return a timedelta object."""
    match = re.match(r"^(\d+)([smhd])$", duration_str.lower().strip())
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "s":
        return datetime.timedelta(seconds=value)
    elif unit == "m":
        return datetime.timedelta(minutes=value)
    elif unit == "h":
        return datetime.timedelta(hours=value)
    elif unit == "d":
        return datetime.timedelta(days=value)
    return None

# --- Commands ---

@client.tree.command(name="ngwords_set", description="Set NG words for the server.")
@app_commands.describe(words="設定するNGワード")
async def ngwords_set(interaction: discord.Interaction, words: str):
    user_locale = interaction.locale.value.split("-")[0]

    if interaction.guild is None:
        return await interaction.response.send_message(_("ERR_NOT_IN_A_SERVER", user_locale), ephemeral=True)
    
    sid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    
    if uid in guild_settings.get(sid, {}).get("nogame", []):
        return await interaction.response.send_message(_("ERR_NO_PERMISSION", user_locale), ephemeral=True)

    max_limit = guild_settings.get(sid, {}).get("max_ngwords", 1)
    current_words = ngwords.get(sid, {}).get(uid, [])

    if len(current_words) >= max_limit:
        return await interaction.response.send_message(_("ERR_NGWORD_LIMIT_REACHED", user_locale).format(max_limit=max_limit), ephemeral=True)
    
    if words in current_words:
        return await interaction.response.send_message(_("ERR_ALREADY_SET_NGWORD", user_locale), ephemeral=True)

    if not (2 <= len(words) <= 10):
        return await interaction.response.send_message(_("ERR_INVALID_NGWORD_COUNT", user_locale), ephemeral=True)
        
    ngwords.setdefault(sid, {}).setdefault(uid, [])
    ngwords[sid][uid].append(words)
    ngwords_save()

    await interaction.response.send_message(_("NGWORD_SET_SUCCESS", user_locale), ephemeral=True)

@client.tree.command(name="ngwords_unset", description="Unset NG words for the server.")
@app_commands.describe(words="削除するNGワード")
async def ngwords_unset(interaction: discord.Interaction, words: str):
    user_locale = interaction.locale.value.split("-")[0]
    
    if interaction.guild is None:
        return await interaction.response.send_message(_("ERR_NOT_IN_A_SERVER", user_locale), ephemeral=True)
    
    sid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    
    if uid in guild_settings.get(sid, {}).get("nogame", []):
        return await interaction.response.send_message(_("ERR_NO_PERMISSION", user_locale), ephemeral=True)
    elif words not in ngwords.get(sid, {}).get(uid, []):
        return await interaction.response.send_message(_("ERR_NGWORD_NOT_FOUND", user_locale), ephemeral=True)
    
    ngwords[sid][uid].remove(words)
    if not ngwords[sid][uid]:
        del ngwords[sid][uid]
    ngwords_save()
    await interaction.response.send_message(_("NGWORD_UNSET_SUCCESS", user_locale), ephemeral=True)

@client.tree.command(name="ngwords_list", description="List NG words for the server.")
async def ngwords_list(interaction: discord.Interaction):
    user_locale = interaction.locale.value.split("-")[0]
    
    if interaction.guild is None:
        return await interaction.response.send_message(_("ERR_NOT_IN_A_SERVER", user_locale), ephemeral=True)
    
    sid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    
    if uid in guild_settings.get(sid, {}).get("nogame", []):
        return await interaction.response.send_message(_("ERR_NO_PERMISSION", user_locale), ephemeral=True)
    elif uid not in ngwords.get(sid, {}):
        return await interaction.response.send_message(_("ERR_NO_NGWORD_SET", user_locale), ephemeral=True)
    
    user_ngwords = ngwords[sid][uid]
    await interaction.response.send_message(_("NGWORD_LIST_SUCCESS", user_locale).format(words=", ".join(user_ngwords)), ephemeral=True)

@client.tree.command(name="game_exclude", description="Exclude a user from the game.")
async def game_exclude(interaction: discord.Interaction, user: discord.Member):
    user_locale = interaction.locale.value.split("-")[0]
    
    if interaction.guild is None:
        return await interaction.response.send_message(_("ERR_NOT_IN_A_SERVER", user_locale), ephemeral=True)
        
    server_id = str(interaction.guild.id)

    if not interaction.user.guild_permissions.administrator:
        if interaction.user.id != user.id and interaction.user.top_role.position <= user.top_role.position:
            return await interaction.response.send_message(_("ERR_CANNOT_EXCLUDE_USER", user_locale), ephemeral=True)
            
    guild_settings.setdefault(server_id, {}).setdefault("nogame", [])
    if str(user.id) not in guild_settings[server_id]["nogame"]:
        guild_settings[server_id]["nogame"].append(str(user.id))
        guild_settings_save()
        
    await interaction.response.send_message(_("GAME_EXCLUDE_SUCCESS", user_locale).format(user=user.mention), ephemeral=True)

@client.tree.command(name="game_penalty", description="Set a penalty for the server.")
async def game_penalty(interaction: discord.Interaction, penalty: Literal["mute", "kick", "ban"], mute_duration: str = "5m"):
    user_locale = interaction.locale.value.split("-")[0]
    
    if interaction.guild is None:
        return await interaction.response.send_message(_("ERR_NOT_IN_A_SERVER", user_locale), ephemeral=True)
        
    server_id = str(interaction.guild.id)

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(_("ERR_CANNOT_SET_PENALTY", user_locale), ephemeral=True)
        
    penalty_value = penalty
    if penalty == "mute":
        duration = parse_duration(mute_duration)
        if not duration:
            return await interaction.response.send_message(_("ERR_INVALID_DURATION", user_locale), ephemeral=True)
        penalty_value = f"mute-{mute_duration}"
        
    penalties[server_id] = penalty_value
    penalties_save()
    await interaction.response.send_message(_("GAME_PENALTY_SUCCESS", user_locale).format(penalty=penalty_value), ephemeral=True)

@client.tree.command(name="ngwords_max_setting", description="1ユーザーあたりのNGワード登録上限を設定します")
@app_commands.describe(limit="登録上限数 (1〜10)")
async def ngwords_max_setting(interaction: discord.Interaction, limit: int):
    user_locale = interaction.locale.value.split("-")[0]

    if interaction.guild is None:
        return await interaction.response.send_message(_("ERR_NOT_IN_A_SERVER", user_locale), ephemeral=True)

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(_("ERR_CANNOT_SET_PENALTY", user_locale), ephemeral=True)

    if not (1 <= limit <= 10):
        return await interaction.response.send_message(_("ERR_INVALID_LIMIT_RANGE", user_locale), ephemeral=True)

    server_id = str(interaction.guild.id)
    
    guild_settings.setdefault(server_id, {})["max_ngwords"] = limit
    guild_settings_save()

    await interaction.response.send_message(_("NGWORD_MAX_SET_SUCCESS", user_locale).format(limit=limit), ephemeral=True)

@client.tree.command(name="game_fallback_setting", description="権限不足時の代替タイムアウト(メッセージ削除)を有効にします")
@app_commands.describe(enable="有効にする場合はTrue")
async def game_fallback_setting(interaction: discord.Interaction, enable: bool):
    user_locale = interaction.locale.value.split("-")[0]
    
    if interaction.guild is None:
        return await interaction.response.send_message(_("ERR_NOT_IN_A_SERVER", user_locale), ephemeral=True)
        
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(_("ERR_CANNOT_SET_PENALTY", user_locale), ephemeral=True)

    server_id = str(interaction.guild.id)
    
    # guild_settingsに設定を保存
    guild_settings.setdefault(server_id, {})["fallback_delete"] = enable
    guild_settings_save()

    status_text = "有効" if enable else "無効"
    await interaction.response.send_message(_("GAME_FALLBACK_SET_SUCCESS", user_locale).format(status=status_text), ephemeral=True)

@client.tree.command(name="game_status", description="Check the game status of a user.")
async def game_status(interaction: discord.Interaction):
    user_locale = interaction.locale.value.split("-")[0]
    
    if interaction.guild is None:
        return await interaction.response.send_message(_("ERR_NOT_IN_A_SERVER", user_locale), ephemeral=True)
        
    server_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    if user_id in guild_settings.get(server_id, {}).get("nogame", []):
        return await interaction.response.send_message(_("GAME_STATUS_EXCLUDED", user_locale), ephemeral=True)
    
    server_penalty = penalties.get(server_id)
    if not server_penalty:
        return await interaction.response.send_message(_("GAME_STATUS_NO_PENALTY", user_locale), ephemeral=True)
    
    excluded_mentions = [f"<@{uid}>" for uid in guild_settings.get(server_id, {}).get("nogame", [])]
    excluded_str = ", ".join(excluded_mentions) if excluded_mentions else "None"
    
    # --- 代替措置のステータス取得を追加 ---
    fallback_enabled = guild_settings.get(server_id, {}).get("fallback_delete", False)
    fallback_str = "有効" if fallback_enabled else "無効"

    mute_until = fallback_mutes.get(server_id, {}).get(user_id)
    mute_status = "なし"
    if mute_until:
        if datetime.datetime.now().timestamp() < mute_until:
            mute_status = _("STATUS_FALLBACK_ACTIVE", user_locale).format(time=int(mute_until))
        else:
            del fallback_mutes[server_id][user_id]
            fallback_mutes_save()

    embed = discord.Embed(
        title="GAME STATUS",
        description=(
            f"**NGword count:** {len(ngwords.get(server_id, {}).get(user_id, []))}\n"
            f"**Server Penalty:** {server_penalty}\n"
            f"**Fallback Setting:** {fallback_str}\n"
            f"**Current Fallback:** {mute_status}\n"
            f"**Excluded Users:** {excluded_str}"
        ),
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

# --- Event handlers ---

@client.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        return
    
    server_id = str(message.guild.id)
    user_id = str(message.author.id)

    mute_until = fallback_mutes.get(server_id, {}).get(user_id)
    if mute_until:
        if datetime.datetime.now().timestamp() < mute_until:
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            return
        else:
            del fallback_mutes[server_id][user_id]
            if not fallback_mutes[server_id]:
                del fallback_mutes[server_id]
            fallback_mutes_save()

    if user_id in guild_settings.get(server_id, {}).get("nogame", []):
        return
    
    server_ng_dict = ngwords.get(server_id, {})
    detected_word = None
    target_user_id = None

    for setter_id, words in server_ng_dict.items():
        for word in words:
            if word in message.content:
                detected_word = word
                target_user_id = setter_id
                break
        if detected_word:
            break

    if detected_word:
        guild_locale = message.guild.preferred_locale.value.split("-")[0]

        embed = discord.Embed(
            title=_("NGWORD_DETECTED_TITLE", guild_locale),
            description=_("NGWORD_DETECTED_DESC", guild_locale).format(word=detected_word, user=target_user_id),
            color=discord.Color.red()
        )
        
        server_penalty = penalties.get(server_id)
        if server_penalty:
            duration = None
            try:
                if server_penalty.startswith("mute-"):
                    duration_str = server_penalty.split("-")[1]
                    duration = parse_duration(duration_str)
                    if duration:
                        until_time = discord.utils.utcnow() + duration
                        await message.author.timeout(until_time, reason="Used an NG word.")
                        embed.add_field(name=_("PENALTY_APPLIED_TITLE", guild_locale), value=_("PENALTY_APPLIED_TIMEOUT", guild_locale).format(duration=duration_str), inline=False)
                elif server_penalty == "kick":
                    await message.author.kick(reason="Used an NG word.")
                    embed.add_field(name=_("PENALTY_APPLIED_TITLE", guild_locale), value=_("PENALTY_APPLIED_KICK", guild_locale), inline=False)
                elif server_penalty == "ban":
                    await message.author.ban(reason="Used an NG word.")
                    embed.add_field(name=_("PENALTY_APPLIED_TITLE", guild_locale), value=_("PENALTY_APPLIED_BAN", guild_locale), inline=False)
            except discord.Forbidden:
                fallback_enabled = guild_settings.get(server_id, {}).get("fallback_delete", False)

                if fallback_enabled and duration:
                    end_time = (datetime.datetime.now() + duration).timestamp()
                    fallback_mutes.setdefault(server_id, {})[user_id] = end_time
                    fallback_mutes_save()
                    
                    embed.add_field(
                        name=_("PENALTY_FALLBACK_TITLE", guild_locale),
                        value=_("PENALTY_FALLBACK_DESC", guild_locale).format(time=int(end_time)),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=_("PENALTY_FAILED_TITLE", guild_locale),
                        value=_("PENALTY_FAILED_DESC", guild_locale),
                        inline=False
                    )
                print(f"Failed to apply penalty to {message.author.name} due to missing permissions.")

        await message.reply(embed=embed, mention_author=True)
        
        if target_user_id in ngwords.get(server_id, {}):
            ngwords[server_id][target_user_id].remove(detected_word)
            if not ngwords[server_id][target_user_id]:
                del ngwords[server_id][target_user_id]
            ngwords_save()

        return
    
client.run(os.getenv("DISCORD_BOT_TOKEN"))