import urllib.request
import os, zipfile, sys, json, shutil, time, glob
from urllib.error import HTTPError

LAUNCHER_VERSION = "1.0.0"
GITHUB_RELEASES_URL = "https://api.github.com/repos/emptyenemy/MagicQuestLauncher/releases/latest"

def check_for_updates(url, version_file):
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req) as response:
            remote_etag = response.headers.get('ETag', '').strip('"')
            remote_modified = response.headers.get('Last-Modified', '')
            remote_length = response.headers.get('Content-Length', '')
            
        remote_info = {
            'etag': remote_etag,
            'last_modified': remote_modified,
            'content_length': remote_length
        }
        
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                local_info = json.load(f)
                if local_info == remote_info:
                    return False, remote_info
        
        return True, remote_info
        
    except (HTTPError, Exception) as e:
        print(f"Error checking for updates: {e}")
        return True, {}

def save_version_info(version_file, info):
    with open(version_file, 'w') as f:
        json.dump(info, f)

def print_header():
    print("\n" + "="*60)
    print(f"           MAGIC QUEST LAUNCHER [{LAUNCHER_VERSION}]")
    print("="*60 + "\n")

def print_status(message, status_type="info"):
    prefixes = {"info": "[INFO]", "success": "[OK]", "warning": "[UPDATE]", "error": "[ERROR]"}
    prefix = prefixes.get(status_type, "[INFO]")
    print(f"  {prefix} {message}")

def check_launcher_updates():
    try:
        req = urllib.request.Request(GITHUB_RELEASES_URL)
        req.add_header('User-Agent', f'MagicQuestLauncher/{LAUNCHER_VERSION}')
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            latest_version = data['tag_name'].lstrip('v')
            
            if latest_version != LAUNCHER_VERSION:
                print_status(f"Launcher update available: {LAUNCHER_VERSION} -> {latest_version}", "warning")
                print_status(f"Download: {data['html_url']}", "info")
                return True
            else:
                print_status("Launcher is up to date!", "success")
            
        return False
        
    except Exception as e:
        print_status(f"Could not check for launcher updates: {e}", "error")
        return False

def download_with_progress(url, filepath):
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, (downloaded * 100) // total_size)
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            bar_length = 40
            filled_length = (percent * bar_length) // 100
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            print(f'\r  [{bar}] {percent}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)', end='', flush=True)
    
    print_status("Starting download...", "info")
    urllib.request.urlretrieve(url, filepath, progress_hook)
    print("\n")
    print_status("Download completed!", "success")

def clean_temp_files():
    current_dir = os.path.dirname(os.path.abspath(sys.executable if hasattr(sys, 'frozen') else __file__))
    
    temp_patterns = [
        'temp_*.zip',
        'temp_*.exe'
    ]
    
    for pattern in temp_patterns:
        for file_path in glob.glob(os.path.join(current_dir, pattern)):
            try:
                os.remove(file_path)
            except:
                pass

p = r"C:\Games\Magic Quest\default\game"
version_file = os.path.join(p, ".version")
game_url = "https://magic-quest.ru/magic_quest.zip"

print_header()

clean_temp_files()

print_status("Checking launcher updates...", "info")
launcher_update_available = check_launcher_updates()

print("\n" + "-"*60)
print_status("Checking game updates...", "info")
needs_update, version_info = check_for_updates(game_url, version_file)

if needs_update:
    print_status("Update available! Preparing download...", "warning")
    os.makedirs(p, exist_ok=True)
    zip_path = os.path.join(p, "magic_quest.zip")
    download_with_progress(game_url, zip_path)
    
    print_status("Cleaning old files...", "info")
    for item in os.listdir(p):
        item_path = os.path.join(p, item)
        if item == "magic_quest.zip":
            continue
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)
    
    print_status("Extracting game files...", "info")
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(p)
    
    os.remove(zip_path)
    
    save_version_info(version_file, version_info)
    print_status("Update completed successfully!", "success")
else:
    print_status("Game is up to date!", "success")

print("\n" + "-"*60)
print_status("Launching game...", "info")
exe_files = [f for f in os.listdir(p) if f.endswith('.exe')]
if exe_files:
    original_dir = os.getcwd()
    os.chdir(p)
    exe_path = os.path.join(p, exe_files[0])
    os.spawnv(os.P_NOWAIT, exe_path, [exe_files[0]])
    os.chdir(original_dir)
    print_status(f"Game launched: {exe_files[0]}", "success")
    print("\n  Have fun playing Magic Quest!")
    print("-"*60)
    
    if launcher_update_available:
        print("\n  Press Enter to close...")
        input()
    else:
        print("\n  Closing launcher in 3 seconds...")
        time.sleep(3)
else:
    print_status("Game executable not found!", "error")
    
    if launcher_update_available:
        print("\n  Press Enter to close...")
        input()
    else:
        print("\n  Press Enter to close...")
        input()
