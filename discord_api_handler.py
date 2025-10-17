"""
Discord API Handler Module
Handles all Discord API interactions including token validation,
guild retrieval, and guild leave operations.
"""

import json
import aiohttp
import csv
import os
import asyncio
import ssl
import certifi
import random
from dotenv import load_dotenv

from utils.logger import setup_logger

logger = setup_logger()

# Load environment variables
load_dotenv()

# --- Constants ---
DISCORD_API = "https://discord.com/api/v9"
GUILDS_ALL_OUTPUT = "output/guilds_all.csv"
GUILDS_LEAVE_FILE = "data/guilds_leave.txt"
# Output CSV files (with separate columns for Excel)
INVALID_TOKENS_CSV = "output/invalid_tokens.csv"
VALID_TOKENS_CSV = "output/valid_tokens.csv"

# --- Delay between Discord requests (e.g., between IPs) ---
DISCORD_REQUEST_DELAY = (
    int(os.getenv('DISCORD_REQUEST_DELAY_MIN', 5)),
    int(os.getenv('DISCORD_REQUEST_DELAY_MAX', 10))
)

# Temporary storage for invalid/valid tokens
invalid_tokens_buffer = []
valid_tokens_buffer = []

# Statistics counters
stats = {
    "total_accounts": 0,
    "proxy_checked": 0,
    "proxy_working": 0,
    "proxy_failed": 0,
    "proxy_empty": 0,
    "tokens_checked": 0,
    "tokens_valid": 0,
    "tokens_invalid": 0,
    "accounts_skipped_proxy": 0,
    "accounts_processed": 0,
    "guilds_collected": 0,
}

# TODO --- БЛОК ХРАНЕНИЯ РЕЗУЛЬТАТОВ ВЫХОДА ИЗ ГИЛЬДИЙ ---
# Global structure for tracking leave operations results across all profiles
leave_results = {}
# Format: {
#     "guild_name": {
#         "id": "1002684842196086876",
#         "success_profiles": [1, 2, 4, 6, ...],  # list of successful profile numbers
#         "failed_profiles": {                     # dict: profile_num -> error_reason
#             3: "401 Unauthorized - Invalid token",
#             17: "403 Forbidden - No permission"
#         }
#     }
# }


def format_proxy(proxy_string: str) -> str:
    """
    Format proxy string to URL format.

    Args:
        proxy_string: Proxy in format 'ip:port:user:password' or 'ip:port'

    Returns:
        Formatted proxy URL or empty string if invalid
    """
    if not proxy_string:
        return ""
    parts = proxy_string.strip().split(':')
    if len(parts) == 4:
        ip, port, user, password = parts
        return f"http://{user}:{password}@{ip}:{port}"
    elif len(parts) == 2:
        ip, port = parts
        return f"http://{ip}:{port}"
    return ""


async def validate_proxy(proxy: str, identifier: str) -> bool:
    """
    Validate if proxy is working by making a test request.
    CRITICAL: If proxy fails, account will be SKIPPED to avoid IP exposure!

    Uses multiple fallback services for reliability:
    1. httpbin.org
    2. api.ipify.org
    3. ifconfig.me
    4. icanhazip.com

    Args:
        proxy: Proxy string (ip:port:user:pass or ip:port)
        identifier: Profile identifier for logging

    Returns:
        True if proxy is working, False if failed (account will be skipped)
    """
    stats["proxy_checked"] += 1

    if not proxy:
        stats["proxy_empty"] += 1
        logger.warning(f"{identifier}: ⚠️ NO PROXY configured - using DIRECT connection (IP EXPOSED!)")
        logger.warning(f"{identifier}: 🚨 SECURITY RISK: Your real IP will be visible to Discord!")
        return True  # No proxy = direct connection (risky!)

    proxy_url = format_proxy(proxy)
    if not proxy_url:
        stats["proxy_failed"] += 1
        logger.error(f"{identifier}: ❌ Invalid proxy format: {proxy}")
        return False

    # Mask password in logs
    proxy_display = proxy_url
    if "@" in proxy_url:
        parts = proxy_url.split("@")
        if ":" in parts[0]:
            user_part = parts[0].split(":")[0] + ":****"
            proxy_display = user_part + "@" + parts[1]

    logger.info(f"{identifier}: 🔍 Testing proxy: {proxy_display}")

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # TODO --- БЛОК ЗАПАСНЫХ СЕРВИСОВ ДЛЯ ПРОВЕРКИ ПРОКСИ ---
    # List of test services (with fallback)
    test_services = [
        ("https://httpbin.org/ip", "json", "origin"),
        ("https://api.ipify.org?format=json", "json", "ip"),
        ("https://ifconfig.me/ip", "text", None),
        ("https://icanhazip.com", "text", None)
    ]

    for service_url, response_type, ip_key in test_services:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(service_url, proxy=proxy_url, ssl=ssl_context, timeout=10) as resp:
                    if resp.status == 200:
                        if response_type == "json":
                            data = await resp.json()
                            proxy_ip = data.get(ip_key, "Unknown")
                        else:
                            proxy_ip = (await resp.text()).strip()

                        stats["proxy_working"] += 1
                        logger.info(f"{identifier}: ✅ Proxy working! IP: {proxy_ip} (via {service_url})")
                        return True
                    else:
                        logger.warning(
                            f"{identifier}: ⚠️ Service {service_url} returned status {resp.status}, trying next...")
                        continue
        except asyncio.TimeoutError:
            logger.warning(f"{identifier}: ⚠️ Timeout for {service_url}, trying next service...")
            continue
        except aiohttp.ClientProxyConnectionError as e:
            logger.warning(f"{identifier}: ⚠️ Connection error for {service_url}: {str(e)}, trying next...")
            continue
        except Exception as e:
            logger.warning(f"{identifier}: ⚠️ Error with {service_url}: {e}, trying next...")
            continue

    # All services failed
    stats["proxy_failed"] += 1
    logger.error(f"{identifier}: ❌ Proxy failed on ALL test services: {proxy_display}")
    logger.error(f"{identifier}: 💡 Possible causes: Wrong credentials, proxy offline, or network issues")
    logger.error(f"{identifier}: 🚫 Account will be SKIPPED (security measure)")
    return False


async def validate_token_and_log_invalid(token: str, proxy: str, user_agent: str, identifier: str) -> bool:
    """
    Validate Discord token and log if invalid.

    Args:
        token: Discord token to validate
        proxy: Proxy string (optional)
        user_agent: User agent string
        identifier: Profile identifier for logging

    Returns:
        True if token is valid, False otherwise
    """
    headers = {
        "Authorization": token,
        "User-Agent": user_agent or "Mozilla/5.0"
    }
    proxy_url = format_proxy(proxy)
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    stats["tokens_checked"] += 1

    # Log proxy usage
    if proxy_url:
        # Mask proxy password in logs for security
        proxy_display = proxy_url
        if "@" in proxy_url:
            # Format: http://user:pass@ip:port -> http://user:****@ip:port
            parts = proxy_url.split("@")
            if ":" in parts[0]:
                user_part = parts[0].split(":")[0] + ":****"
                proxy_display = user_part + "@" + parts[1]
        logger.info(f"{identifier}: 🌐 Using proxy: {proxy_display}")
    else:
        logger.info(f"{identifier}: 🌐 Direct connection (no proxy)")

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{DISCORD_API}/users/@me", proxy=proxy_url, ssl=ssl_context, timeout=20) as resp:
                if resp.status == 200:
                    stats["tokens_valid"] += 1
                    logger.info(f"{identifier}: ✅ Token is VALID")
                    valid_tokens_buffer.append((int(identifier) if identifier.isdigit() else 0, token))
                    return True
                elif resp.status == 401:
                    logger.error(f"{identifier}: ❌ Token is INVALID (401 Unauthorized)")
                else:
                    logger.error(f"{identifier}: ⚠️ Token check error. Status: {resp.status}")
    except Exception as e:
        logger.error(f"{identifier}: ❌ Error checking token: {e}")

    # Save as tuple with numeric id for sorting
    stats["tokens_invalid"] += 1
    invalid_tokens_buffer.append((int(identifier) if identifier.isdigit() else 0, token))
    return False


def flush_invalid_tokens():
    """Sort and save all invalid tokens to CSV file"""
    if not invalid_tokens_buffer:
        return

    sorted_tokens = sorted(invalid_tokens_buffer)

    # Save to CSV with separate columns for easy Excel work
    try:
        abs_path_csv = os.path.abspath(INVALID_TOKENS_CSV)
        with open(INVALID_TOKENS_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["Account ID", "Token", "Status"])
            for identifier, token in sorted_tokens:
                # Добавляем апостроф перед токеном чтобы Excel сохранил его как текст
                writer.writerow([identifier, f"'{token}", "Invalid"])
        logger.warning(f"💾 Saved {len(invalid_tokens_buffer)} invalid tokens to {abs_path_csv}")
    except Exception as e:
        logger.error(f"Failed to save invalid tokens to CSV: {e}")


def flush_valid_tokens():
    """Sort and save all valid tokens to CSV file"""
    if not valid_tokens_buffer:
        return

    sorted_tokens = sorted(valid_tokens_buffer)

    # Save to CSV with separate columns for easy Excel work
    try:
        abs_path_csv = os.path.abspath(VALID_TOKENS_CSV)
        with open(VALID_TOKENS_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["Account ID", "Token", "Status"])
            for identifier, token in sorted_tokens:
                # Добавляем апостроф перед токеном чтобы Excel сохранил его как текст
                writer.writerow([identifier, f"'{token}", "Valid"])
        logger.info(f"💾 Saved {len(valid_tokens_buffer)} valid tokens to {abs_path_csv}")
    except Exception as e:
        logger.error(f"Failed to save valid tokens to CSV: {e}")


async def get_guilds(token: str, proxy: str = None, user_agent: str = None, identifier: str = "", retries: int = 3):
    """
    Get list of guilds for a Discord account.

    Args:
        token: Discord token
        proxy: Proxy string (optional)
        user_agent: User agent string
        identifier: Profile identifier for logging
        retries: Number of retry attempts

    Returns:
        List of guild dictionaries or empty list on failure
    """
    headers = {
        "Authorization": token,
        "User-Agent": user_agent or "Mozilla/5.0",
    }
    proxy_url = format_proxy(proxy)
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    for attempt in range(1, retries + 1):
        try:
            # Log proxy usage on first attempt
            if attempt == 1:
                if proxy_url:
                    proxy_display = proxy_url
                    if "@" in proxy_url:
                        parts = proxy_url.split("@")
                        if ":" in parts[0]:
                            user_part = parts[0].split(":")[0] + ":****"
                            proxy_display = user_part + "@" + parts[1]
                    logger.info(f"{identifier}: 🌐 Using proxy: {proxy_display}")
                else:
                    logger.info(f"{identifier}: 🌐 Direct connection (no proxy)")

            logger.info(f"{identifier}: Getting guilds... (attempt #{attempt})")
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(f"{DISCORD_API}/users/@me/guilds", proxy=proxy_url, ssl=ssl_context,
                                       timeout=20) as resp:
                    if resp.status == 200:
                        try:
                            guilds = await resp.json()
                            logger.info(f"{identifier}: ✅ Received {len(guilds)} guilds")
                            return guilds
                        except ValueError as e:
                            logger.error(f"{identifier}: JSON parsing error: {e}")
                            return []
                    elif resp.status == 401:
                        logger.error(f"{identifier}: ❌ Invalid token (401 Unauthorized)")
                        return []
                    elif resp.status == 429:
                        retry_after = float(resp.headers.get("Retry-After", 5))
                        logger.warning(
                            f"{identifier}: ⚠️ Rate limited (429). Waiting {retry_after} sec before retry #{attempt}")
                        await asyncio.sleep(retry_after)
                        continue
                    elif resp.status == 503:
                        logger.warning(f"{identifier}: ⚠️ Discord server unavailable (503). Retry #{attempt}")
                        await asyncio.sleep(random.uniform(5, 10))
                        continue
                    elif resp.status == 500:
                        logger.warning(f"{identifier}: ⚠️ Internal server error (500). Retry #{attempt}")
                        await asyncio.sleep(random.uniform(5, 10))
                        continue
                    else:
                        logger.error(f"{identifier}: ❌ Failed to get guilds. Status: {resp.status}")
                        return []

        except aiohttp.ClientConnectionError as e:
            logger.error(f"{identifier}: Network connection error: {e}. Attempt #{attempt}")
            if attempt == retries:
                return []
            await asyncio.sleep(random.uniform(3, 6))
        except asyncio.TimeoutError as e:
            logger.error(f"{identifier}: Request timeout: {e}. Attempt #{attempt}")
            if attempt == retries:
                return []
            await asyncio.sleep(random.uniform(3, 6))
        except Exception as e:
            logger.error(f"{identifier}: Unknown error getting guilds: {e}")
            return []

    logger.error(f"{identifier}: ❌ Failed to get guilds after {retries} attempts")
    return []


async def leave_guild(token: str, guild: dict, proxy: str = None, user_agent: str = None, identifier: str = "",
                      retries: int = 3):
    """
    Leave a specific guild.

    Args:
        token: Discord token
        guild: Guild dictionary with 'name' and 'id'
        proxy: Proxy string (optional)
        user_agent: User agent string
        identifier: Profile identifier for logging
        retries: Number of retry attempts

    Returns:
        Tuple (success: bool, error_reason: str or None)
    """
    guild_name = guild.get("name", "[no name]")
    guild_id = guild.get("id")

    headers = {
        "Authorization": token,
        "User-Agent": user_agent or "Mozilla/5.0",
    }
    proxy_url = format_proxy(proxy)
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Log proxy usage on first leave attempt
    if proxy_url:
        proxy_display = proxy_url
        if "@" in proxy_url:
            parts = proxy_url.split("@")
            if ":" in parts[0]:
                user_part = parts[0].split(":")[0] + ":****"
                proxy_display = user_part + "@" + parts[1]
        logger.info(f"{identifier}: 🌐 Using proxy: {proxy_display}")
    else:
        logger.info(f"{identifier}: 🌐 Direct connection (no proxy)")

    for attempt in range(1, retries + 1):
        await asyncio.sleep(random.uniform(*DISCORD_REQUEST_DELAY))
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.delete(f"{DISCORD_API}/users/@me/guilds/{guild_id}", proxy=proxy_url,
                                          ssl=ssl_context, timeout=20) as resp:
                    if resp.status == 204:
                        logger.info(f"✅ {identifier}: Left guild '{guild_name}' (ID: {guild_id})")
                        return True, None
                    elif resp.status == 401:
                        logger.error(f"{identifier}: ❌ Invalid token (401 Unauthorized)")
                        error_reason = "401 Unauthorized - Invalid token"
                        return False, error_reason
                    elif resp.status == 403:
                        logger.error(f"{identifier}: ❌ No permission to leave guild '{guild_name}' (403 Forbidden)")
                        error_reason = "403 Forbidden - No permission"
                        return False, error_reason
                    elif resp.status == 404:
                        logger.warning(f"{identifier}: ⚠️ Guild '{guild_name}' not found (404). Already left?")
                        return True, None
                    elif resp.status == 429:
                        retry_after = float(resp.headers.get("Retry-After", 5))
                        logger.warning(
                            f"{identifier}: ⚠️ Rate limited (429). Waiting {retry_after} sec before retry #{attempt}")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        logger.error(f"{identifier}: ❌ Failed to leave guild. Status: {resp.status}")
                        error_reason = f"HTTP {resp.status}"
                        if attempt == retries:
                            return False, error_reason
                        await asyncio.sleep(random.uniform(3, 6))

        except asyncio.TimeoutError as e:
            logger.error(f"{identifier}: Request timeout: {e}. Attempt #{attempt}")
            error_reason = f"Timeout: {e}"
            if attempt == retries:
                return False, error_reason
            await asyncio.sleep(random.uniform(3, 6))
        except aiohttp.ClientResponseError as e:
            logger.error(f"{identifier}: Server response error: {e}. Attempt #{attempt}")
            error_reason = f"Response error: {e}"
            if attempt == retries:
                return False, error_reason
            await asyncio.sleep(random.uniform(3, 6))
        except Exception as e:
            logger.error(f"{identifier}: Unknown error leaving guild: {e}")
            error_reason = f"Unknown error: {e}"
            return False, error_reason

    logger.error(f"{identifier}: ❌ Failed to leave guild '{guild_name}' after {retries} attempts")
    error_reason = f"Failed after {retries} attempts"
    return False, error_reason


async def handle_guilds(profile: dict, mode: str, leave_list_path: str = GUILDS_LEAVE_FILE):
    """
    Main function for handling guild operations.

    Args:
        profile: Profile dictionary with token, proxy, user_agent
        mode: Operation mode - 'collect' or 'leave'
        leave_list_path: Path to file with guilds to leave
    """
    identifier = profile["identifier"]
    token = profile.get("ds_tokens")
    proxy = profile.get("proxies")
    user_agent = profile.get("user_agent")

    if not token:
        logger.error(f"{identifier}: Discord token missing in profile")
        return

    stats["accounts_processed"] += 1

    # Validate proxy first - CRITICAL for security!
    proxy_valid = await validate_proxy(proxy, identifier)
    if not proxy_valid:
        stats["accounts_skipped_proxy"] += 1
        logger.error(f"{identifier}: ❌ SKIPPING account due to invalid proxy (security measure)")
        return

    # Re-validate token
    is_valid = await validate_token_and_log_invalid(token, proxy, user_agent, identifier)
    if not is_valid:
        logger.warning(f"{identifier}: ⚠️ Skipping profile due to invalid token")
        return

    # Create guilds_leave.txt only in collect mode and only if it doesn't exist
    if mode == "collect" and not os.path.exists(leave_list_path):
        with open(leave_list_path, "w", encoding="utf-8") as f:
            f.write("# Enter guild names, IDs or numbers to leave, one per line\n")
            f.write("# You can use guild names or IDs\n")
            f.write("# Example:\n")
            f.write("# Caldera\n")
            f.write("# 1002684842196086876\n")
        logger.info(f"✅ Created leave list file: {leave_list_path}")
        logger.info(f"💡 Please fill it with guild names/IDs before running MODE 3 (Leave guilds)")

    # TODO --- БЛОК ПОЛУЧЕНИЯ СПИСКА ГИЛЬДИЙ ---
    if mode == "collect":
        # In collect mode, always fetch guilds from API
        guilds = await get_guilds(token, proxy, user_agent, identifier)
        if not guilds:
            logger.warning(f"{identifier}: Guild list is empty or failed to load")
            return

        stats["guilds_collected"] += len(guilds)

        # Save individual profile guilds
        filename = f"output/guilds_{identifier}.csv"
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["#", "Server Name", "Server ID"])
            for i, g in enumerate(guilds, 1):
                # Добавляем апостроф перед ID чтобы Excel не конвертировал в научную нотацию
                writer.writerow([i, g["name"], f"'{g['id']}"])
        logger.info(f"{identifier}: Guild list saved to {os.path.abspath(filename)}")

        # Add to combined file using pure Python + CSV
        new_guilds = [{"Server Name": g["name"], "Server ID": g["id"]} for g in guilds]

        # Load existing guilds from combined file
        existing_guilds = {}
        if os.path.exists(GUILDS_ALL_OUTPUT):
            try:
                with open(GUILDS_ALL_OUTPUT, "r", newline="", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        if "Server ID" in row and row["Server ID"]:
                            # Remove apostrophe if present
                            server_id = str(row["Server ID"]).strip().lstrip("'")
                            server_name = str(row.get("Server Name", "")).strip()
                            existing_guilds[server_id] = server_name
            except Exception as e:
                logger.error(f"{identifier}: Error reading combined file: {e}")

        # Add new guilds (deduplicate by Server ID)
        for guild in new_guilds:
            server_id = str(guild["Server ID"]).strip()
            server_name = str(guild["Server Name"]).strip()
            if server_id:
                existing_guilds[server_id] = server_name

        # Sort by name and write back
        sorted_guilds = sorted(existing_guilds.items(), key=lambda x: x[1].lower())

        try:
            with open(GUILDS_ALL_OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["#", "Server Name", "Server ID"])
                for i, (server_id, server_name) in enumerate(sorted_guilds, 1):
                    # Добавляем апостроф перед ID чтобы Excel не конвертировал в научную нотацию
                    writer.writerow([i, server_name, f"'{server_id}"])
            logger.info(f"{identifier}: List added to {os.path.abspath(GUILDS_ALL_OUTPUT)}")
        except Exception as e:
            logger.error(f"{identifier}: Error writing combined file: {e}")

    elif mode == "leave":
        # TODO --- БЛОК РЕЖИМА ВЫХОДА ИЗ ГИЛЬДИЙ ---

        # TODO --- ШАГ 1: ЧТЕНИЕ СПИСКА НА ВЫХОД ---
        leave_list = []
        try:
            with open(leave_list_path, "r", encoding="utf-8") as f:
                leave_list = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except FileNotFoundError:
            logger.error(f"{identifier}: ❌ Leave list file not found: {leave_list_path}")
            logger.error(f"{identifier}: Please create the file or run MODE 2 (Collect guilds) first")
            return

        if not leave_list:
            logger.warning(f"{identifier}: ⚠️ Leave list is empty, nothing to do")
            return

        logger.info(f"{identifier}: 📋 Processing {len(leave_list)} entries from leave list")

        # TODO --- ШАГ 2: ЗАГРУЗКА БАЗЫ ДАННЫХ ГИЛЬДИЙ (CSV или API) ---
        guilds_database = {}  # {name: id, name2: id2, ...}

        if os.path.exists(GUILDS_ALL_OUTPUT):
            # Try to load from CSV first (faster, no API calls)
            logger.info(f"{identifier}: 📂 Loading guild database from {GUILDS_ALL_OUTPUT}")
            try:
                with open(GUILDS_ALL_OUTPUT, "r", newline="", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        guild_name = row.get("Server Name", "").strip()
                        guild_id = row.get("Server ID", "").strip().strip("'")  # Remove apostrophe if present
                        if guild_name and guild_id:
                            guilds_database[guild_name] = guild_id
                logger.info(f"{identifier}: ✅ Loaded {len(guilds_database)} guilds from CSV database")
            except Exception as e:
                logger.error(f"{identifier}: ❌ Failed to load CSV database: {e}")
                logger.warning(f"{identifier}: ⚠️ Falling back to API request...")
                guilds_database = {}

        # Fallback: if CSV doesn't exist or failed to load, fetch guilds from API
        if not guilds_database:
            logger.warning(f"{identifier}: ⚠️ Guild database (guilds_all.csv) not found or empty")
            logger.info(f"{identifier}: 🔄 Fetching guilds from Discord API...")

            guilds = await get_guilds(token, proxy, user_agent, identifier)
            if not guilds:
                logger.error(f"{identifier}: ❌ Failed to fetch guilds from API")
                return

            # Convert API response to database format
            for guild in guilds:
                guilds_database[guild["name"]] = guild["id"]

            logger.info(f"{identifier}: ✅ Loaded {len(guilds_database)} guilds from API")

        # TODO --- ШАГ 3: ПРЕОБРАЗОВАНИЕ В ID ---
        to_leave_guilds = []

        for item in leave_list:
            guild_name = None
            guild_id = None

            # Check if item is already an ID (long numeric string)
            if len(item) > 15 and item.isdigit():
                guild_id = item
                guild_name = "Unknown"
                logger.info(f"{identifier}: 🆔 Using direct ID: {guild_id}")
            else:
                # Try to find by name in database (exact match first)
                if item in guilds_database:
                    guild_id = guilds_database[item]
                    guild_name = item
                    logger.info(f"{identifier}: ✅ Found '{guild_name}' in database (ID: {guild_id})")
                else:
                    # Try case-insensitive search
                    found = False
                    for db_name, db_id in guilds_database.items():
                        if db_name.lower() == item.lower():
                            guild_id = db_id
                            guild_name = db_name
                            logger.info(f"{identifier}: ✅ Found '{guild_name}' (case-insensitive) in database (ID: {guild_id})")
                            found = True
                            break

                    if not found:
                        logger.warning(f"{identifier}: ⚠️ Guild '{item}' not found in database - skipping")

            if guild_id:
                to_leave_guilds.append({"name": guild_name, "id": guild_id})

        if not to_leave_guilds:
            logger.warning(f"{identifier}: ❌ No matching guilds found to leave")
            return

        logger.info(f"{identifier}: 🎯 Found {len(to_leave_guilds)} guilds to leave")

        # TODO --- ШАГ 4: ВЫХОД ИЗ ГИЛЬДИЙ С ОТСЛЕЖИВАНИЕМ РЕЗУЛЬТАТОВ ---
        logger.info(f"{identifier}: 🚀 Starting leave operations...")
        successful_leaves = 0
        failed_leaves = 0

        for idx, guild in enumerate(to_leave_guilds, 1):
            guild_name = guild["name"]
            guild_id = guild["id"]

            # Initialize guild in global results if not exists
            if guild_name not in leave_results:
                leave_results[guild_name] = {
                    "id": guild_id,
                    "success_profiles": [],
                    "failed_profiles": {}
                }

            logger.info(f"{identifier}: 🔄 Leaving '{guild_name}' ({idx}/{len(to_leave_guilds)})...")

            success, error_reason = await leave_guild(token, guild, proxy, user_agent, identifier)

            if success:
                successful_leaves += 1
                # Add to global success list
                profile_num = int(identifier) if identifier.isdigit() else 0
                leave_results[guild_name]["success_profiles"].append(profile_num)
                logger.info(f"{identifier}: ✅ Left '{guild_name}' ({idx}/{len(to_leave_guilds)})")
            else:
                failed_leaves += 1
                # Add to global failed list with reason
                profile_num = int(identifier) if identifier.isdigit() else 0
                leave_results[guild_name]["failed_profiles"][profile_num] = error_reason
                logger.error(f"{identifier}: ❌ Failed to leave '{guild_name}': {error_reason} ({idx}/{len(to_leave_guilds)})")

        # Summary for this profile
        logger.info(f"{identifier}: ===== LEAVE SUMMARY =====")
        logger.info(f"{identifier}: Total to leave: {len(to_leave_guilds)}")
        logger.info(f"{identifier}: Successful: {successful_leaves}")
        logger.info(f"{identifier}: Failed: {failed_leaves}")


def print_final_report():
    """Print detailed final statistics report"""
    logger.info("=" * 80)
    logger.info("📊 FINAL EXECUTION REPORT")
    logger.info("=" * 80)

    # Accounts summary
    logger.info(f"👥 ACCOUNTS:")
    logger.info(f"   • Total processed: {stats['accounts_processed']}")
    logger.info(f"   • Skipped (proxy failed): {stats['accounts_skipped_proxy']}")
    logger.info(f"   • Successfully processed: {stats['accounts_processed'] - stats['accounts_skipped_proxy']}")

    # Proxy summary
    logger.info(f"")
    logger.info(f"🌐 PROXY STATISTICS:")
    logger.info(f"   • Total checked: {stats['proxy_checked']}")
    logger.info(f"   • Working proxies: {stats['proxy_working']} ✅")
    logger.info(f"   • Failed proxies: {stats['proxy_failed']} ❌")
    logger.info(f"   • No proxy (direct): {stats['proxy_empty']} ⚠️")

    if stats['proxy_checked'] > 0:
        success_rate = (stats['proxy_working'] / stats['proxy_checked']) * 100
        logger.info(f"   • Success rate: {success_rate:.1f}%")

    # Token summary
    logger.info(f"")
    logger.info(f"🔑 TOKEN STATISTICS:")
    logger.info(f"   • Total checked: {stats['tokens_checked']}")
    logger.info(f"   • Valid tokens: {stats['tokens_valid']} ✅")
    logger.info(f"   • Invalid tokens: {stats['tokens_invalid']} ❌")

    if stats['tokens_checked'] > 0:
        valid_rate = (stats['tokens_valid'] / stats['tokens_checked']) * 100
        logger.info(f"   • Valid rate: {valid_rate:.1f}%")

    # Guilds summary (only show in collect mode, not in leave mode)
    if stats['guilds_collected'] > 0:
        logger.info(f"")
        logger.info(f"🏰 GUILDS COLLECTED:")
        logger.info(f"   • Total guilds: {stats['guilds_collected']}")
        if stats['tokens_valid'] > 0:
            avg_guilds = stats['guilds_collected'] / stats['tokens_valid']
            logger.info(f"   • Average per account: {avg_guilds:.1f}")

    # Leave operations summary (show if we performed any leave operations)
    if leave_results:
        print_leave_report()

    # Warnings
    if stats['proxy_failed'] > 0:
        logger.warning(f"")
        logger.warning(f"⚠️ WARNING: {stats['proxy_failed']} proxy failures detected!")
        logger.warning(f"   Check your proxy configuration and credentials")

    if stats['proxy_empty'] > 0:
        logger.warning(f"")
        logger.warning(f"🚨 SECURITY WARNING: {stats['proxy_empty']} accounts used DIRECT connection!")
        logger.warning(f"   Your real IP was EXPOSED to Discord!")
        logger.warning(f"   Add proxies to data/proxies.txt to avoid detection")

    if stats['tokens_invalid'] > 0:
        logger.warning(f"")
        logger.warning(f"⚠️ WARNING: {stats['tokens_invalid']} invalid tokens detected!")
        logger.warning(f"   Check output/invalid_tokens.csv for details")

    logger.info("=" * 80)
    logger.info("✅ Report generation completed")
    logger.info("=" * 80)


def print_leave_report():
    """
    Print detailed leave operations report.
    Groups results by guilds and shows only problematic cases.
    """
    if not leave_results:
        logger.info("No leave operations performed")
        return

    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 LEAVE OPERATIONS REPORT")
    logger.info("=" * 60)

    # Analyze results
    total_guilds = len(leave_results)
    fully_successful_guilds = []
    partially_failed_guilds = []
    fully_failed_guilds = []

    total_operations = 0
    total_successful = 0
    total_failed = 0

    for guild_name, results in leave_results.items():
        success_count = len(results["success_profiles"])
        failed_count = len(results["failed_profiles"])
        total_count = success_count + failed_count

        total_operations += total_count
        total_successful += success_count
        total_failed += failed_count

        if failed_count == 0 and success_count > 0:
            fully_successful_guilds.append(guild_name)
        elif success_count == 0 and failed_count > 0:
            fully_failed_guilds.append(guild_name)
        elif success_count > 0 and failed_count > 0:
            partially_failed_guilds.append((guild_name, failed_count, total_count))

    # Sort partially failed by failure count (worst first)
    partially_failed_guilds.sort(key=lambda x: x[1], reverse=True)

    # Summary
    logger.info("")
    logger.info("📊 SUMMARY:")
    logger.info(f"   • Guilds in leave list: {total_guilds}")
    logger.info(f"   • Total leave operations: {total_operations}")
    logger.info(f"   • Successful operations: {total_successful}")
    logger.info(f"   • Failed operations: {total_failed}")

    if total_failed == 0:
        logger.info("")
        logger.info(f"✅ Successfully left all {len(fully_successful_guilds)} guilds across all accounts!")
    else:
        logger.info("")
        logger.info(f"✅ Successfully left {len(fully_successful_guilds)} guilds (all accounts)")
        if len(partially_failed_guilds) > 0:
            logger.info(f"⚠️  Partially failed: {len(partially_failed_guilds)} guilds (some accounts)")
        if len(fully_failed_guilds) > 0:
            logger.info(f"❌ Fully failed: {len(fully_failed_guilds)} guilds (all accounts)")

    # Show problems if any
    if total_failed > 0:
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"❌ FAILED TO LEAVE ({len(partially_failed_guilds) + len(fully_failed_guilds)} guilds):")
        logger.info("=" * 60)

        # Combine all problems
        problems_to_show = partially_failed_guilds + [
            (g, len(leave_results[g]["failed_profiles"]), len(leave_results[g]["failed_profiles"])) for g in
            fully_failed_guilds]
        problems_to_show.sort(key=lambda x: x[1], reverse=True)

        if len(problems_to_show) <= 5:
            # Show all problems in detail
            for guild_name, failed_count, total_count in problems_to_show:
                _print_guild_failure_details(guild_name, leave_results[guild_name])
        else:
            # Show top 5 most problematic
            logger.info("")
            logger.info(f"Top 5 most problematic guilds:")
            logger.info("")

            for idx, (guild_name, failed_count, total_count) in enumerate(problems_to_show[:5], 1):
                guild_id = leave_results[guild_name]["id"]
                failure_rate = (failed_count / total_count) * 100

                # Get most common error
                errors = list(leave_results[guild_name]["failed_profiles"].values())
                most_common_error = max(set(errors), key=errors.count) if errors else "Unknown"

                logger.info(f"{idx}. \"{guild_name}\" (ID: {guild_id[:8]}...)")
                logger.info(f"   └─> Failed on {failed_count}/{total_count} accounts ({failure_rate:.0f}%)")
                logger.info(f"       Most common: {most_common_error}")
                logger.info("")

            logger.info(f"... and {len(problems_to_show) - 5} more problematic guilds")
            logger.info("")

    logger.info("=" * 60)


def _print_guild_failure_details(guild_name: str, results: dict):
    """Helper function to print detailed failure info for a single guild"""
    guild_id = results["id"]
    success_count = len(results["success_profiles"])
    failed_profiles = results["failed_profiles"]

    logger.info("")
    logger.info("┌" + "─" * 58 + "┐")
    logger.info(f"│ Guild: \"{guild_name}\"")
    logger.info(f"│ ID: {guild_id}")
    logger.info("├" + "─" * 58 + "┤")
    logger.info(f"│ Failed on {len(failed_profiles)} account(s):")

    for profile_num, error_reason in sorted(failed_profiles.items()):
        logger.info(f"│   • Profile {profile_num}: {error_reason}")

    logger.info(f"│")
    logger.info(f"│ Successfully left on {success_count} account(s)")
    logger.info("└" + "─" * 58 + "┘")
