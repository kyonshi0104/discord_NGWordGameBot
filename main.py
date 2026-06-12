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
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

# --- Load data from JSON files ---
# ファイルが存在しない場合の初期化
def load_json(filepath, default_data):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_data

guild_settings = load_json("data/guild_settings.json", {})
ngwords = load_json("data/ngwords.json", {})
penalties = load_json("data/penalties.json", {})
locales = load_json("locales/locales.json", {})

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

async def guild_autocomplete(
    interaction: discord.Interaction, 
    current: str
) -> list[app_commands.Choice[str]]:
    """Botが参加しており、かつユーザーも所属しているサーバーの一覧を自動補完の候補として返す"""
    choices = []
    
    for guild in client.guilds:
        member = guild.get_member(interaction.user.id)
        if member is None:
            continue  # 所属していないサーバーは候補に出さない
            
        if current.lower() in guild.name.lower():
            choices.append(
                app_commands.Choice(name=guild.name, value=str(guild.id))
            )
            
    # Discordの仕様制限より:25
    return choices[:25]

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
@app_commands.describe(server_id="対象のサーバー（自動補完から選択）", words="設定するNGワード")
@app_commands.autocomplete(server_id=guild_autocomplete) # 自動補完を結びつける
async def ngwords_set(interaction: discord.Interaction, server_id: str, words: str):
    user_locale = interaction.locale.value.split("-")[0]
    
    if interaction.guild is not None:
        return await interaction.response.send_message(_("ERR_IN_A_SERVER", user_locale), ephemeral=True)
    server = client.get_guild(int(server_id))
    if not server or server.get_member(interaction.user.id) is None:
        return await interaction.response.send_message(_("ERR_NO_PERMISSION", user_locale), ephemeral=True)
        
    sid = server_id
    uid = str(interaction.user.id)
    
    if uid in guild_settings.get(sid, {}).get("nogame", []):
        return await interaction.response.send_message(_("ERR_NO_PERMISSION", user_locale), ephemeral=True)
    
    if uid in ngwords.get(sid, {}):
        return await interaction.response.send_message(_("ERR_ALREADY_SET_NGWORD", user_locale), ephemeral=True)
    elif not (2 <= len(words) <= 10):
        return await interaction.response.send_message(_("ERR_INVALID_NGWORD_COUNT", user_locale), ephemeral=True)
        
    ngwords.setdefault(sid, {}).setdefault(uid, [])
    ngwords[sid][uid].append(words)
    ngwords_save()
    await interaction.response.send_message(_("NGWORD_SET_SUCCESS", user_locale))

@client.tree.command(name="ngwords_unset", description="Unset NG words for the server.")
@app_commands.describe(server_id="対象のサーバー", words="削除するNGワード")
@app_commands.autocomplete(server_id=guild_autocomplete)
async def ngwords_unset(interaction: discord.Interaction, server_id: str, words: str):
    user_locale = interaction.locale.value.split("-")[0]
    if interaction.guild is not None:
        return await interaction.response.send_message(_("ERR_IN_A_SERVER", user_locale), ephemeral=True)
    
    sid = server_id
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
@app_commands.describe(server_id="対象のサーバー")
@app_commands.autocomplete(server_id=guild_autocomplete)
async def ngwords_list(interaction: discord.Interaction, server_id: str):
    user_locale = interaction.locale.value.split("-")[0]
    if interaction.guild is not None:
        return await interaction.response.send_message(_("ERR_IN_A_SERVER", user_locale), ephemeral=True)
    
    sid = server_id
    uid = str(interaction.user.id)
    
    if uid in guild_settings.get(sid, {}).get("nogame", []):
        return await interaction.response.send_message(_("ERR_NO_PERMISSION", user_locale), ephemeral=True)
    elif uid not in ngwords.get(sid, {}):
        return await interaction.response.send_message(_("ERR_NO_NGWORD_SET", user_locale), ephemeral=True)
    
    user_ngwords = ngwords[sid][uid]
    await interaction.response.send_message(_("NGWORD_LIST_SUCCESS", user_locale).format(words=", ".join(user_ngwords)), ephemeral=True)

@client.tree.command(name="game_exclude", description="Exclude a user from the game.")
async def game_exclude(interaction: discord.Interaction, user: discord.Member): # discord.Memberに変更
    user_locale = interaction.locale.value.split("-")[0]
    
    if interaction.guild is None:
        return await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        
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
        return await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        
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

@client.tree.command(name="game_status", description="Check the game status of a user.")
async def game_status(interaction: discord.Interaction):
    user_locale = interaction.locale.value.split("-")[0]
    
    if interaction.guild is None:
        return await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        
    server_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    if user_id in guild_settings.get(server_id, {}).get("nogame", []):
        return await interaction.response.send_message(_("GAME_STATUS_EXCLUDED", user_locale), ephemeral=True)
    
    server_penalty = penalties.get(server_id)
    if not server_penalty:
        return await interaction.response.send_message(_("GAME_STATUS_NO_PENALTY", user_locale), ephemeral=True)
    
    excluded_mentions = [f"<@{uid}>" for uid in guild_settings.get(server_id, {}).get("nogame", [])]
    excluded_str = ", ".join(excluded_mentions) if excluded_mentions else "None"
    
    embed = discord.Embed(
        title="GAME STATUS",
        description=f"**NGword count:** {len(ngwords.get(server_id, {}).get(user_id, []))}\n**Server Penalty:** {server_penalty}\n**Excluded Users:** {excluded_str}",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Event handlers ---

@client.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        return
    
    server_id = str(message.guild.id)
    user_id = str(message.author.id)

    if user_id in guild_settings.get(server_id, {}).get("nogame", []):
        return
    
    server_ng_dict = ngwords.get(server_id, {})

    detected_word = None
    target_user_id = None

    # メッセージ内の単語チェック
    for setter_id, words in server_ng_dict.items():
        for word in words:
            if word in message.content:
                detected_word = word
                target_user_id = setter_id
                break
        if detected_word:
            break

    if detected_word:
        embed = discord.Embed(
            title="NGWORD_DETECTED",
            description=f"NGワードが検出されました: **{detected_word}**\n設定者: <@{target_user_id}>",
            color=discord.Color.red()
        )
        await message.reply(embed=embed, mention_author=True)
        
        # --- ペナルティ処理 ---
        server_penalty = penalties.get(server_id)
        if server_penalty:
            try:
                if server_penalty.startswith("mute-"):
                    duration_str = server_penalty.split("-")[1]
                    duration = parse_duration(duration_str)
                    if duration:
                        until_time = discord.utils.utcnow() + duration
                        await message.author.timeout(until_time, reason="Used an NG word.")
                elif server_penalty == "kick":
                    await message.author.kick(reason="Used an NG word.")
                elif server_penalty == "ban":
                    await message.author.ban(reason="Used an NG word.")
            except discord.Forbidden:
                print(f"Failed to apply penalty to {message.author.name} due to missing permissions.")

        # --- NGワードの削除処理 ---
        if target_user_id in ngwords.get(server_id, {}):
            ngwords[server_id][target_user_id].remove(detected_word)

            if not ngwords[server_id][target_user_id]:
                del ngwords[server_id][target_user_id]
            ngwords_save()

        return
    
client.run(os.getenv("DISCORD_BOT_TOKEN"))