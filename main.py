"""
Discord Guild Manager - Simple version for public use
All data files should be placed in the 'data' folder
"""

import os
import sys
import asyncio
import random
from dotenv import load_dotenv
from utils.logger import setup_logger
from utils.browser import load_data
from discord_api_handler import (
    handle_guilds,
    validate_token_and_log_invalid,
    flush_invalid_tokens,
    flush_valid_tokens,
    print_final_report,
    stats
)

# Load environment variables
load_dotenv()

# --- Logging setup ---
logger = setup_logger()

# --- Prevent system sleep (macOS only) ---
if sys.platform == "darwin":  # macOS
    from utils.caffeinate_on import enable_caffeinate
    enable_caffeinate()
    logger.info("✅ Caffeinate enabled to prevent macOS sleep")
else:
    logger.info("ℹ️ Caffeinate skipped (not required for Windows)")

# --- Configuration from .env ---
START_LINE = int(os.getenv('START_LINE', 1))
END_LINE = int(os.getenv('END_LINE', 9999))
RANDOM_START = os.getenv('RANDOM_START', 'False').lower() == 'true'
THREAD_COUNT = int(os.getenv('THREAD_COUNT', 3))
ACCOUNT_DELAY = (
    int(os.getenv('ACCOUNT_DELAY_MIN', 1)),
    int(os.getenv('ACCOUNT_DELAY_MAX', 5))
)

# Parse profile filters
allow_profiles = os.getenv('ALLOW_PROFILE_NUMBERS', '').strip()
ALLOW_PROFILE_NUMBERS = []
if allow_profiles:
    for x in allow_profiles.split(','):
        x = x.strip()
        # Skip empty strings and comments
        if x and not x.startswith('#'):
            try:
                ALLOW_PROFILE_NUMBERS.append(int(x))
            except ValueError:
                logger.warning(f"Invalid profile number in ALLOW_PROFILE_NUMBERS: {x}")

skip_profiles = os.getenv('SKIP_PROFILE_NUMBERS', '').strip()
SKIP_PROFILE_NUMBERS = []
if skip_profiles:
    for x in skip_profiles.split(','):
        x = x.strip()
        # Skip empty strings and comments
        if x and not x.startswith('#'):
            try:
                SKIP_PROFILE_NUMBERS.append(int(x))
            except ValueError:
                logger.warning(f"Invalid profile number in SKIP_PROFILE_NUMBERS: {x}")

# --- File paths (all in data folder) ---
DATA_DIR = "data"
OUTPUT_DIR = "output"

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATA_FILE_PATHS = {
    "account_indexes": os.path.join(DATA_DIR, "account_indexes.txt"),
    "ds_tokens": os.path.join(DATA_DIR, "ds_tokens.txt"),
    "user_agents": os.path.join(DATA_DIR, "user_agents.txt"),
    "proxies": os.path.join(DATA_DIR, "proxies.txt"),
    "leave_list": os.path.join(DATA_DIR, "guilds_leave.txt"),
}

REQUIRED_DATA_FILES = ["account_indexes", "ds_tokens", "user_agents", "proxies"]

# --- Global variables ---
RUN_VALIDATE_TOKENS = False
RUN_SERVER_HANDLER = False
MODE = "collect"

profiles = {}
profile_semaphore = asyncio.Semaphore(THREAD_COUNT)

logger.info(f"Configuration loaded:")
logger.info(f"  - Processing lines: {START_LINE} to {END_LINE}")
logger.info(f"  - Thread count: {THREAD_COUNT}")
logger.info(f"  - Random start: {RANDOM_START}")
logger.info(f"  - Account delay: {ACCOUNT_DELAY[0]}-{ACCOUNT_DELAY[1]} seconds")


# --- Process guilds for single profile ---
async def run_profile(profile):
    """Process guild operations for a single profile"""
    async with profile_semaphore:
        identifier = profile["identifier"]
        logger.info(f"Profile {identifier}: Starting guild processing")
        try:
            await handle_guilds(profile, mode=MODE, leave_list_path=DATA_FILE_PATHS["leave_list"])
        except Exception as e:
            logger.error(f"Profile {identifier}: Error during execution: {e}")


# --- Validate token ---
async def run_validate_token(profile):
    """Validate Discord token for a single profile"""
    async with profile_semaphore:
        identifier = profile["identifier"]
        logger.info(f"Profile {identifier}: Starting token validation")
        try:
            # Import validation function
            from discord_api_handler import validate_proxy

            # Increment processed counter
            stats["accounts_processed"] += 1

            # Validate proxy first
            proxy_valid = await validate_proxy(profile["proxies"], identifier)
            if not proxy_valid:
                logger.error(f"Profile {identifier}: ❌ Proxy validation failed, skipping token check")
                return

            # Validate token
            await validate_token_and_log_invalid(
                token=profile["ds_tokens"],
                proxy=profile["proxies"],
                user_agent=profile["user_agent"],
                identifier=identifier
            )
        except Exception as e:
            logger.error(f"Profile {identifier}: Token validation error: {e}")


# --- Check if all required files exist ---
def check_required_files():
    """Check if all required data files exist and create examples if missing"""
    missing_files = []

    for key in REQUIRED_DATA_FILES:
        filepath = DATA_FILE_PATHS[key]
        if not os.path.exists(filepath):
            missing_files.append(filepath)

    if missing_files:
        logger.error("=" * 60)
        logger.error("❌ MISSING REQUIRED FILES!")
        logger.error("The following files are missing:")
        for file in missing_files:
            logger.error(f"  - {file}")
        logger.error("=" * 60)

        # Create example files
        logger.info("Creating example files...")

        # Create account_indexes.txt
        if DATA_FILE_PATHS["account_indexes"] in missing_files:
            with open(DATA_FILE_PATHS["account_indexes"], "w") as f:
                f.write("# Account identifiers - one per line\n")
                f.write("# Example:\n")
                f.write("# 1\n")
                f.write("# 2\n")
                f.write("# 3\n")

        # Create ds_tokens.txt
        if DATA_FILE_PATHS["ds_tokens"] in missing_files:
            with open(DATA_FILE_PATHS["ds_tokens"], "w") as f:
                f.write("# Discord tokens - one per line\n")
                f.write("# Example:\n")
                f.write("# MTA1NTU2Nzg5...\n")

        # Create user_agents.txt
        if DATA_FILE_PATHS["user_agents"] in missing_files:
            with open(DATA_FILE_PATHS["user_agents"], "w") as f:
                f.write("# User agents - one per line\n")
                f.write("# Example:\n")
                f.write("# Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\n")

        # Create proxies.txt
        if DATA_FILE_PATHS["proxies"] in missing_files:
            with open(DATA_FILE_PATHS["proxies"], "w") as f:
                f.write("# Proxies - one per line\n")
                f.write("# Format: ip:port:username:password\n")
                f.write("# Example:\n")
                f.write("# 192.168.1.1:8080:user:pass\n")

        logger.info("Example files created. Please fill them with your data and run again.")
        return False

    return True


# --- Main function ---
async def main():
    global RUN_VALIDATE_TOKENS, RUN_SERVER_HANDLER, MODE

    # Check if all required files exist
    if not check_required_files():
        return

    # --- Interactive menu ---
    print("\n" + "=" * 60)
    print("         🤖 DISCORD GUILD MANAGER")
    print("=" * 60)
    print("  1 - Validate tokens")
    print("  2 - Collect guilds (save to CSV)")
    print("  3 - Leave guilds (from list)")
    print("=" * 60)

    choice = input("Select action (1-3): ").strip()

    if choice == "1":
        RUN_VALIDATE_TOKENS = True
        RUN_SERVER_HANDLER = False
        logger.info("✅ Mode selected: TOKEN VALIDATION")
    elif choice == "2":
        RUN_VALIDATE_TOKENS = False
        RUN_SERVER_HANDLER = True
        MODE = "collect"
        logger.info("✅ Mode selected: COLLECT GUILDS")
    elif choice == "3":
        RUN_VALIDATE_TOKENS = False
        RUN_SERVER_HANDLER = True
        MODE = "leave"
        logger.info("✅ Mode selected: LEAVE GUILDS")
    else:
        logger.error("❌ Invalid choice! Exiting.")
        return

    print("=" * 60 + "\n")

    # Load data into dictionaries
    data = {}
    for key in REQUIRED_DATA_FILES:
        # Load data from file
        lines = await load_data(DATA_FILE_PATHS[key], START_LINE, END_LINE)
        if not lines:
            logger.error(f"Required file {key} is empty or not found: {DATA_FILE_PATHS[key]}")
            return
        # Convert list to dictionary: key - line number (starting from START_LINE), value - line from file
        data[key] = {str(i + START_LINE): line for i, line in enumerate(lines)}
        logger.info(f"Loaded {len(data[key])} lines from {key} ({DATA_FILE_PATHS[key]}).")

    # Get profile identifiers from account_indexes
    profile_identifiers = list(data["account_indexes"].keys())

    # Apply filters
    if ALLOW_PROFILE_NUMBERS:
        profile_identifiers = [pid for pid in profile_identifiers if int(pid) in ALLOW_PROFILE_NUMBERS]
    if SKIP_PROFILE_NUMBERS:
        profile_identifiers = [pid for pid in profile_identifiers if int(pid) not in SKIP_PROFILE_NUMBERS]

    # Shuffle if needed
    if RANDOM_START:
        random.shuffle(profile_identifiers)

    # Build profiles dictionary
    for pid in profile_identifiers:
        profiles[pid] = {
            "identifier": pid,
            "ds_tokens": data["ds_tokens"].get(pid, ""),
            "user_agent": data["user_agents"].get(pid, ""),
            "proxies": data["proxies"].get(pid, ""),
        }

    if not profiles:
        logger.error("No suitable profiles to run.")
        return

    logger.info(f"Ready to process {len(profiles)} profiles")

    tasks = []

    # --- Token validation ---
    if RUN_VALIDATE_TOKENS:
        logger.info("Starting token validation...")
        for idx, pid in enumerate(profiles):
            task = asyncio.create_task(run_validate_token(profiles[pid]))
            tasks.append(task)
            if idx < len(profiles) - 1:
                delay = random.randint(*ACCOUNT_DELAY)
                logger.info(f"Waiting {delay} seconds before next account...")
                await asyncio.sleep(delay)

    # --- Guild processing ---
    if RUN_SERVER_HANDLER:
        if MODE == "leave" and not os.path.exists(DATA_FILE_PATHS["leave_list"]):
            with open(DATA_FILE_PATHS["leave_list"], "w", encoding="utf-8") as f:
                f.write("# Enter guild names, IDs or numbers to leave, one per line\n")
                f.write("# Example:\n")
                f.write("# My Server\n")
                f.write("# 123456789012345678\n")
            logger.info(f"Created leave list file: {DATA_FILE_PATHS['leave_list']}")
            logger.info("Please add guilds to leave and run again!")
            return

        logger.info(f"Starting guild {MODE} mode...")
        for idx, pid in enumerate(profiles):
            task = asyncio.create_task(run_profile(profiles[pid]))
            tasks.append(task)
            if idx < len(profiles) - 1:
                delay = random.randint(*ACCOUNT_DELAY)
                logger.info(f"Waiting {delay} seconds before next account...")
                await asyncio.sleep(delay)

    # Wait for all tasks to complete
    await asyncio.gather(*tasks)

    # Save results
    if RUN_VALIDATE_TOKENS:
        flush_invalid_tokens()
        flush_valid_tokens()

    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ ALL OPERATIONS COMPLETED!")
    logger.info("=" * 60)

    # Print detailed final report
    print_final_report()

    logger.info("")
    logger.info("📁 Check the 'output' folder for results")
    logger.info("📝 Check the 'logs' folder for detailed logs")


if __name__ == "__main__":
    asyncio.run(main())
