# Roku Updater Configuration Guide

This guide covers all configuration requirements for the Roku Welcome Screen Updater, including both Roku device authentication and Airbnb data access.

## Overview

The Roku updater requires authentication credentials:
1. **Roku Session Token** - To update your Roku device welcome screen (expires periodically)
2. **Airbnb API Key** - To access your listing's reservation data (unique per listing, stable)
3. **Airbnb Authentication Cookie** - For session authentication (expires periodically)

The session-based tokens expire regularly and need to be refreshed when authentication fails.

---

## 🖥️ Roku Configuration

### When to Update Roku Token

The `ks.session` token expires periodically. Update it if you see:
- Authentication errors (non-200 status codes)
- "Failed with status 401" or "Failed with status 403"
- Tokens typically expire after hours to days

### How to Get New Roku Session Token

1. **Open your browser** and log into https://my.roku.com
2. **Navigate to your device**: Go to your Roku device settings page
3. **Open Developer Tools**: Press F12 or right-click → Inspect
4. **Go to Network tab** in developer tools
5. **Make any change** to your device settings (toggle something)
6. **Find the API request** in the network tab
7. **Copy the ks.session value** from the request cookies

### Update the Roku Token

Edit `update_roku_welcome.py` around line 25:
```python
ROKU_SESSION_TOKEN = 'YOUR_NEW_SESSION_TOKEN_HERE'
```

**Example:**
```python
# NEW (updated)
ROKU_SESSION_TOKEN = 'G%3FtpNvOLV%2GLy%3C0m6QSJmHs...'
```

**Note**: Only the `ks.session` token is required - all other cookies have been removed for simplicity.

---

## 🏠 Airbnb Configuration

### When to Update Airbnb Credentials

You'll see this error when Airbnb session has expired:
```
❌ Failed to download reservations: HTTP 401
⚠️ Airbnb download failed, falling back to local file...
```

### How to Get Fresh Airbnb Credentials

1. **Log into Airbnb** in your browser
2. **Navigate to your reservations page**
3. **Open browser developer tools** (F12 or right-click → Inspect)
4. **Go to Network tab** and refresh the page
5. **Find the API request** that loads reservations data (look for `download_reservations`)
6. **Right-click on the request** → Copy as cURL
7. **Extract the API key and cookies** from the cURL command
   - Look for `key=` in the URL parameters for the API key
   - Look for `_aat=` in the cookies for the authentication token

### Update the Airbnb Configuration

1. Open `update_roku_welcome.py` in your editor
2. Find the configuration section at the top (around lines 31-32)
3. Update the configuration variables with your new values
4. Save the file

**Update these configuration variables:**
```python
# Airbnb API credentials (unique per listing - should not change often)
AIRBNB_API_KEY = 'YOUR_API_KEY_HERE'
AIRBNB_AAT_COOKIE = 'YOUR_AAT_COOKIE_HERE'
```

**Note**: The API key is unique per Airbnb listing and should remain stable, while the AAT cookie expires periodically and needs regular updates.

---

## ⚙️ Configuration Options

### Disable Airbnb API (Use Local CSV Only)

If you prefer not to deal with cookies:
1. Set `use_airbnb_api=False` in the main function
2. Manually download and replace `reservations.csv` when needed
3. The script will work exactly as before

### Backup Strategy

- **The script automatically falls back** to your local `reservations.csv` file if download fails
- **Your local file will still work** as a backup even when cookies expire
- The automated download is a convenience feature - your existing workflow continues to work!

---

## 🔧 Troubleshooting

### Common Issues

**Roku Updates Failing:**
- Check if `ROKU_SESSION_TOKEN` needs refreshing
- Verify device ID is correct
- Ensure you're logged into the correct Roku account

**Airbnb Downloads Failing:**
- Update cookies following the Airbnb section above
- Check if you can access reservations in your browser
- Verify the reservations page loads properly

**Script Not Running:**
- Check cron job: `crontab -l`
- Verify log file: `tail roku_update.log`
- Test manually: `./run.sh`

### Log Monitoring

Check execution logs:
```bash
tail -20 roku_update.log              # Recent activity
grep "$(date +%Y-%m-%d)" roku_update.log  # Today's runs
ls -la roku_update.log                # Last modified time
```

### File Locations

- **Main script**: `update_roku_welcome.py`
- **Runner script**: `run.sh`
- **Log file**: `roku_update.log`
- **Backup CSV**: `reservations.csv`

---

## 📝 Quick Reference

| Issue | Solution | Location |
|-------|----------|----------|
| Roku auth error | Update `ROKU_SESSION_TOKEN` | Line ~25 in Python script |
| Airbnb 401 error | Update `AIRBNB_API_KEY` and `AIRBNB_AAT_COOKIE` | Lines ~31-32 in Python script |
| No cron execution | Check `crontab -l` and `roku_update.log` | Terminal |
| Want local-only | Set `use_airbnb_api=False` | Line ~441 in Python script |

**Remember**: Both authentication tokens expire regularly, so periodic updates are normal maintenance!
