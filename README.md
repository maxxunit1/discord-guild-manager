# Discord Guild Manager

**Full guide with images** - https://x.com/2maxdmn4/status/1980479928174092427
**How to find your Discord account token** - https://x.com/2maxdmn4/status/1980483000736559133

- ⚡ **One-click launcher** - No Python knowledge required
- 🧹 **Clean up cluttered accounts** - Leave 100+ servers in minutes
- ✅ **Token validation** - Check which accounts are still active
- 📊 **CSV export** - All your servers in one spreadsheet
- 🔒 **Proxy support** - Stay safe with proxy rotation
- 🚀 **Production-ready** - Error handling, logging, retry logic

Perfect for:
- Managing 2-3 Discord accounts (main + alts)
- Spring cleaning dead/spam servers
- Token validation after long breaks
- Organizing servers across accounts
- Bot developers testing environments

## 📧 Installation

### Quick Start (Recommended)

**Windows Users:**
1. Download the project (clone or ZIP)
2. Double-click `start_windows.bat`
3. Done! ✅

**Mac/Linux Users:**
1. Download the project
2. Make executable: `chmod +x start_mac_linux.sh`
3. Run: `./start_mac_linux.sh`
4. Done! ✅

The launcher will automatically:
- ✅ Check Python (show download link if missing)
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Run the application

### Manual Installation (Advanced)

If you prefer manual setup:

1. **Download the project:**
   ```bash
   git clone https://github.com/maxxunit1/discord-guild-manager.git
   cd discord-guild-manager
   ```

2. **Install Python 3.8+** (if not installed)
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, CHECK "Add Python to PATH"

3. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

4. **Activate virtual environment:**
   - Windows: `venv\Scripts\activate.bat`
   - Mac/Linux: `source venv/bin/activate`

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Run:**
   ```bash
   python main.py
   ```

## 🎮 Usage

### First Run

**Windows:** Double-click `start_windows.bat`

**Mac/Linux:** Run `./start_mac_linux.sh`

You'll see a menu:
```
============================================
      🤖 DISCORD GUILD MANAGER
============================================
  1 - Validate tokens
  2 - Collect guilds (save to CSV)
  3 - Leave guilds (from list)
============================================
Select action (1-3):
```

If this is your first run, the script will create example data files in the `data` folder. Fill them with your data and run again.

### Data Files Setup

The script needs 4 data files in the `data` folder:

1. **`account_indexes.txt`** - Account identifiers (1, 2, 3...)
2. **`ds_tokens.txt`** - Discord tokens (one per line)
3. **`user_agents.txt`** - Browser user agents (one per line)
4. **`proxies.txt`** - Proxies in format `ip:port:user:pass` (optional)

**Important:** Line numbers must match across all files!
- Line 1 token = Account 1
- Line 1 proxy = Proxy for Account 1
- etc.

See [EXAMPLE_DATA.md](EXAMPLE_DATA.md) for detailed format examples.

### Running the Script

**Windows:** Double-click `start_windows.bat`

**Mac/Linux:** Run `./start_mac_linux.sh`

The launcher handles everything:
- ✅ First run: Installs dependencies (~30 seconds)
- ✅ Subsequent runs: Instant start (~1 second)
- ✅ If requirements.txt changed: Auto-reinstalls

### Option 1: Validate Tokens
- Checks if your Discord tokens are still valid
- Results: `output/valid_tokens.csv` and `output/invalid_tokens.csv`

### Option 2: Collect Guilds
- Gets list of all guilds for each account
- Results: `output/guilds_all.csv` (combined) + `output/guilds_{id}.csv` (individual)

### Option 3: Leave Guilds
1. First run option 2 to collect guilds
2. Edit `data/guilds_leave.txt` - add guild names or IDs
3. Run option 3

4. Results: Detailed report in console


