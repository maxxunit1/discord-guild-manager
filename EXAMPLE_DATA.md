# Example Data Formats

This file shows the correct format for all data files used by Discord Guild Manager.

## 📁 File Structure

All files should be placed in the `data` folder:
```
data/
├── account_indexes.txt
├── ds_tokens.txt
├── user_agents.txt
├── proxies.txt
└── guilds_leave.txt
```

## 📄 account_indexes.txt

Simple numeric identifiers for your accounts:
```
1
2
3
4
5
```

**Important:** These numbers are just identifiers. Line 1 corresponds to line 1 in all other files.

## 📄 ds_tokens.txt

Discord tokens, one per line:
```
MTA1NTU2Nzg5MDEyMzQ1Njc4OQ.GnP_ej.1234567890abcdefghijklmnopqrstuvwxyz
OTg3NjU0MzIxMDk4NzY1NDMyMQ.G12345.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKL
MTExMTExMTExMTExMTExMTExMQ.Gabc12.9876543210zyxwvutsrqponmlkjihgfedcba
```

**Note:** These are example tokens and won't work. Get real tokens from Discord.

## 📄 user_agents.txt

Browser user agent strings, one per line:
```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

**Tip:** You can use the same user agent for all accounts if needed.

## 📄 proxies.txt

Proxy credentials in format `ip:port:username:password`:
```
192.168.1.100:8080:user1:password123
10.0.0.50:3128:proxyuser:proxypass456
proxy.example.com:1080:myuser:mypassword
```

**Formats supported:**
- With auth: `ip:port:username:password`
- Without auth: `ip:port`
- Leave empty line if no proxy for that account

## 📄 guilds_leave.txt

List of guilds to leave (used with option 3):
```
# This is a comment - it will be ignored
My Test Server
Another Server Name
123456789012345678
987654321098765432
Gaming Community
```

**You can use:**
- Guild names (partial match works)
- Guild IDs (18-digit numbers)
- Line numbers from collected guilds

## 💡 Tips

1. **Line alignment is critical!** 
   - Line 1 in tokens = Account 1
   - Line 1 in proxies = Proxy for Account 1
   - Line 1 in user_agents = User agent for Account 1

2. **Comments** - Lines starting with `#` are ignored

3. **Empty lines** - Will be skipped automatically

4. **Case sensitivity** - Guild names are case-insensitive for matching

## 🔍 Example with 3 accounts:

**account_indexes.txt:**
```
101
102
103
```

**ds_tokens.txt:**
```
MTA1NTU2Nzg5MDEyMzQ1Njc4OQ.GnP_ej.token_for_account_101
OTg3NjU0MzIxMDk4NzY1NDMyMQ.G12345.token_for_account_102
MTExMTExMTExMTExMTExMTExMQ.Gabc12.token_for_account_103
```

**user_agents.txt:**
```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0
Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0
```

**proxies.txt:**
```
192.168.1.100:8080:user1:pass1
192.168.1.101:8080:user2:pass2
192.168.1.102:8080:user3:pass3
```