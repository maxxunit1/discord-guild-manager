# 🚀 Quick Start Guide

Get Discord Guild Manager running in 5 minutes!

## Step 1: Download

```bash
git clone https://github.com/maxxunit1/discord-guild-manager.git
cd discord-guild-manager
```

Or download ZIP from GitHub and extract.

## Step 2: Run

### Windows:
**Double-click `start_windows.bat`**

Or in terminal:
```batch
start_windows.bat
```

### Mac/Linux:
**Make executable and run:**
```bash
chmod +x start_mac_linux.sh
./start_mac_linux.sh
```

**That's it!** The script will:
- ✅ Check if Python is installed
- ✅ Create virtual environment (first run only)
- ✅ Install dependencies (first run only)
- ✅ Launch the application

## Step 3: First Time Setup

On first run, you'll see:
```
============================================
      🤖 DISCORD GUILD MANAGER
============================================
  1 - Validate tokens
  2 - Collect guilds (save to CSV)
  3 - Leave guilds (from list)
============================================

❌ MISSING REQUIRED FILES!
```

The script will create example files in the `data` folder.

## Step 4: Add Your Data

Edit files in the `data` folder:

1. **`account_indexes.txt`** - Account numbers (1, 2, 3...)
2. **`ds_tokens.txt`** - Your Discord tokens
3. **`user_agents.txt`** - Browser user agents
4. **`proxies.txt`** - Your proxies (optional)

## Step 5: Run Again

**Windows:** Double-click `start_windows.bat`

**Mac/Linux:** Run `./start_mac_linux.sh`

Now you'll see the menu! Select your action (1-3).

## 🎯 Common Tasks

### Check if tokens work:
1. Select option `1`
2. Check `output/valid_tokens.csv` and `output/invalid_tokens.csv`

### Get all your Discord servers:
1. Select option `2`
2. Check `output/guilds_all.csv`

### Leave specific servers:
1. First run option `2` to collect servers
2. Edit `data/guilds_leave.txt` - add server names
3. Select option `3`

## ⚡ Pro Tips

1. **Python 3.8+ required** - The launcher will tell you if not installed
2. **Test with 1 account first!**
3. **Use proxies to avoid rate limits**
4. **Keep delays at 5-10 seconds** (edit `.env` file)

## ❓ Need Help?

- Check [README.md](README.md) for detailed instructions
- Check [EXAMPLE_DATA.md](EXAMPLE_DATA.md) for data format examples
- Create an [issue on GitHub](https://github.com/maxxunit1/discord-guild-manager/issues)

---

**Remember:** The launcher handles everything automatically! Just double-click and go! 🚀