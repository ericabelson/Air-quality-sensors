# Windows SSH Key Setup Guide

This guide shows Windows users how to set up secure SSH key authentication for your Raspberry Pi.

**Why SSH keys?** They're more secure than passwords and allow you to connect without typing your password every time.

---

## Prerequisites

- Windows 10 or later (PowerShell with built-in SSH client)
- Already set up SSH access to your Raspberry Pi with password

---

## Step 1: Generate SSH Key Pair (On Windows)

1. Open PowerShell (search "PowerShell" in Start menu, right-click, Run as Administrator)

2. Generate a new SSH key:

```powershell
ssh-keygen -t ed25519 -C "raspberry-pi-air-quality"
```

3. When prompted "Enter file in which to save the key", press **Enter** to use the default location:
   ```
   C:\Users\YourUsername\.ssh\id_ed25519
   ```

4. When prompted for a passphrase:
   - **Option A (Recommended):** Enter a strong passphrase for extra security
   - **Option B:** Press Enter twice for no passphrase (less secure, but convenient)

**Expected output:**
```
Generating public/private ed25519 key pair.
Your identification has been saved in C:\Users\YourName\.ssh\id_ed25519
Your public key has been saved in C:\Users\YourName\.ssh\id_ed25519.pub
The key fingerprint is:
SHA256:aBc123XyZ456... raspberry-pi-air-quality
```

---

## Step 2: Copy Your Public Key to the Raspberry Pi

### Method A: Using ssh-copy-id (Easier, Windows 10 Build 1809+)

If your Windows version supports `ssh-copy-id`, use this method:

```powershell
# Replace with your Raspberry Pi's IP address and username
ssh-copy-id pi@192.168.1.100
```

Enter your Raspberry Pi password when prompted.

**Skip to Step 3 if this works!**

### Method B: Manual Copy (If ssh-copy-id doesn't work)

If `ssh-copy-id` command is not found, do it manually:

1. **Display your public key** in PowerShell:

```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub
```

2. **Copy the entire output** (it should look like):
   ```
   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAbCdEfGhIjKlMnOpQrStUvWxYz... raspberry-pi-air-quality
   ```

3. **SSH into your Raspberry Pi** with password:

```powershell
ssh pi@192.168.1.100
```

4. **On the Raspberry Pi**, create the .ssh directory (if it doesn't exist):

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
```

5. **Add your public key** to the authorized_keys file:

```bash
nano ~/.ssh/authorized_keys
```

6. **Paste** the public key you copied in Step 2 (right-click in PuTTY or Ctrl+Shift+V in Windows Terminal)

7. **Save and exit**: `Ctrl+X`, then `Y`, then `Enter`

8. **Set correct permissions**:

```bash
chmod 600 ~/.ssh/authorized_keys
```

9. **Exit** the SSH session:

```bash
exit
```

---

## Step 3: Test SSH Key Authentication

From PowerShell on Windows:

```powershell
ssh pi@192.168.1.100
```

**Success:** You should connect WITHOUT being asked for a password!

**If asked for passphrase:** That's normal if you set one in Step 1. Enter it.

**If still asked for password:** See [Troubleshooting](#troubleshooting) below.

---

## Step 4: Disable Password Authentication (Optional, Recommended)

**WARNING:** Only do this AFTER confirming SSH key login works!

1. SSH into your Raspberry Pi (should use key now):

```powershell
ssh pi@192.168.1.100
```

2. Edit SSH configuration:

```bash
sudo nano /etc/ssh/sshd_config
```

3. Find and modify these lines (use Ctrl+W to search):

```
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no
```

4. Save and exit: `Ctrl+X`, then `Y`, then `Enter`

5. Restart SSH service:

```bash
sudo systemctl restart ssh
```

6. **IMPORTANT:** Open a NEW PowerShell window and test SSH key login BEFORE closing your current session!

```powershell
ssh pi@192.168.1.100
```

If successful, your Raspberry Pi now only accepts SSH keys, not passwords.

---

## Troubleshooting

### Problem: Still asked for password after setting up key

**Cause:** Permissions may be incorrect on the Raspberry Pi.

**Fix:**

```bash
# On the Raspberry Pi
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Check ownership
ls -la ~/.ssh
# Should show: drwx------ pi pi
```

### Problem: "Permission denied (publickey)" after disabling passwords

**Cause:** SSH key not properly configured.

**Emergency fix:**

1. Connect a monitor and keyboard directly to the Raspberry Pi
2. Log in locally
3. Re-enable password authentication:

```bash
sudo nano /etc/ssh/sshd_config
# Change: PasswordAuthentication yes
sudo systemctl restart ssh
```

4. From Windows, reconfigure SSH keys following Step 2

### Problem: ssh-copy-id command not found on Windows

**Solution:** Use Method B (Manual Copy) in Step 2.

### Problem: "WARNING: UNPROTECTED PRIVATE KEY FILE!"

**Cause:** Windows file permissions too open.

**Fix:** Windows doesn't use Unix permissions, but you can try:

```powershell
# Remove inheritance and set proper permissions
icacls $env:USERPROFILE\.ssh\id_ed25519 /inheritance:r
icacls $env:USERPROFILE\.ssh\id_ed25519 /grant:r "$($env:USERNAME):(R)"
```

---

## Using SSH Keys with PuTTY (Alternative)

If you prefer PuTTY over PowerShell:

1. Download PuTTYgen from: https://www.putty.org/

2. Open PuTTYgen

3. Click "Generate" and move your mouse randomly

4. Click "Save private key" (save as `raspberry-pi.ppk`)

5. Copy the public key shown in the text box

6. Follow Step 2 Method B to add the public key to your Pi

7. In PuTTY:
   - Session → Enter `pi@192.168.1.100`
   - Connection → SSH → Auth → Browse → Select your `.ppk` file
   - Session → Save session with a name

---

## Next Steps

After setting up SSH keys:

1. Continue with the security hardening script:
   ```bash
   cd ~/Air-quality-sensors/scripts
   sudo bash security-hardening.sh
   ```
   Now when prompted about SSH keys, you can answer "yes" to continue.

2. See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) to continue sensor setup

3. See [SECURITY.md](SECURITY.md) for additional security hardening

---

## Quick Reference

### Connect from Windows PowerShell:
```powershell
ssh pi@192.168.1.100
```

### Copy files to Pi:
```powershell
scp myfile.txt pi@192.168.1.100:/home/demeter/
```

### Copy files from Pi:
```powershell
scp pi@192.168.1.100:/home/demeter/myfile.txt C:\Users\YourName\Desktop\
```

---

## Security Best Practices

- ✅ Always use SSH keys instead of passwords when possible
- ✅ Use a passphrase on your SSH key for extra security
- ✅ Never share your private key (`id_ed25519`)
- ✅ Only share the public key (`id_ed25519.pub`)
- ✅ Keep backups of your SSH keys in a secure location
- ✅ Disable password authentication after confirming key-based login works

---

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Check SSH connection verbosity:
   ```powershell
   ssh -v pi@192.168.1.100
   ```
3. On Raspberry Pi, check SSH logs:
   ```bash
   sudo journalctl -u ssh -n 50
   ```
4. Open an issue on GitHub with your error message
