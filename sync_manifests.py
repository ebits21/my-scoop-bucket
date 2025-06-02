import os
import requests
import json

# === Config ===
APPS = [
        "git",
        "7zip",
        "vscode", 
        "autohotkey", 
        "ripgrep", 
        "pandoc", 
        "neovide", 
        "neovim", 
        "FiraCode-NF",
        "xournalpp",
        "vcredist2022",
        "cryptomator",
        ]  # Add your desired apps
DEST_DIR = "bucket"

UPSTREAMS = {
    "main": "https://raw.githubusercontent.com/ScoopInstaller/Main/master/bucket/",
    "extras": "https://raw.githubusercontent.com/ScoopInstaller/Extras/master/bucket/",
    "nerd-fonts": "https://raw.githubusercontent.com/matthewjberger/scoop-nerd-fonts/master/bucket/",
}

os.makedirs(DEST_DIR, exist_ok=True)

def download_and_clean_manifest(app, dest_dir):
    for name, base_url in UPSTREAMS.items():
        url = f"{base_url}{app}.json"
        try:
            print(f"Trying {url}")
            response = requests.get(url)
            if response.status_code == 200:
                try:
                    data = json.loads(response.text)

                    # Remove 'shortcuts' key if present
                    if "shortcuts" in data:
                        print(f"Removing 'shortcuts' from {app}")
                        del data["shortcuts"]
                        
                    if app = "autohotkey":
                        data = {
    "version": original["version"],
    "description": "Minimal AutoHotkey v2 (64-bit only) with only AutoHotkey64.exe and WindowSpy.ahk.",
    "homepage": original["homepage"],
    "license": original["license"],
    "url": original["url"],
    "hash": original["hash"],
    "extract_dir": f"AutoHotkey_{original['version']}",
    "architecture": {
        "64bit": {
            "bin": [
                ["AutoHotkey64.exe", "AutoHotkey64"]
            ]
        }
    },
    "post_install": [
        "Copy-Item \"$dir\\UX\\WindowSpy.ahk\" \"$dir\" -Force",
        "Get-ChildItem $dir -Recurse | Where-Object {",
        "    $_.FullName -notlike \"$dir\\AutoHotkey64.exe\" -and",
        "    $_.FullName -notlike \"$dir\\WindowSpy.ahk\"",
        "} | Remove-Item -Force -Recurse"
    ],
    "checkver": original.get("checkver", {}),
    "autoupdate": original.get("autoupdate", {})
}

                    # Save the cleaned manifest
                    dest_path = os.path.join(dest_dir, f"{app}.json")
                    with open(dest_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)

                    print(f"✓ Downloaded and cleaned '{app}' from {name}")
                    return True
                except json.JSONDecodeError:
                    print(f"⚠ Failed to parse JSON for {app}")
                    return False
        except Exception as e:
            print(f"Error fetching {url}: {e}")
    print(f"✗ Failed to find '{app}' in any upstream.")
    return False

def main():
    updated = False
    for app in APPS:
        if download_and_clean_manifest(app, DEST_DIR):
            updated = True

    if updated:
        print("\nAll available manifests synced and cleaned.")
        # Optional Git commit:
        # os.system("git add bucket")
        # os.system("git commit -m 'Update manifests (shortcuts removed)'")
        # os.system("git push")
    else:
        print("No manifests updated.")

if __name__ == "__main__":
    main()
