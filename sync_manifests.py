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


def add_neovide_shortcut(data):
    shortcut_commands = [
        "$ws = New-Object -ComObject WScript.Shell",
        "$desktop = [Environment]::GetFolderPath('Desktop')",
        '$desktopShortcut = $ws.CreateShortcut("$desktop\\Neovide.lnk")',
        '$desktopShortcut.TargetPath = "$dir\\neovide.exe"',
        '$desktopShortcut.WorkingDirectory = "$dir"',
        '$desktopShortcut.IconLocation = "$dir\\neovide.exe"',
        "$desktopShortcut.Save()",
    ]

    if "post_install" in data and isinstance(data["post_install"], list):
        data["post_install"].extend(shortcut_commands)
    else:
        data["post_install"] = shortcut_commands


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

                    if app == "xournalpp" and "post_install" not in data:
                        data["post_install"] = [
                            'New-Item -ItemType Directory -Path "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Xournal" -Force | Out-Null',
                            "$ws = New-Object -ComObject WScript.Shell",
                            '$startMenuShortcut = $ws.CreateShortcut("$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Xournal\\Xournal.lnk")',
                            '$startMenuShortcut.TargetPath = "$dir\\bin\\xournalpp.exe"',
                            '$startMenuShortcut.WorkingDirectory = "$dir"',
                            '$startMenuShortcut.IconLocation = "$dir\\bin\\xournalpp.exe"',
                            "$startMenuShortcut.Save()",
                            "$desktop = [Environment]::GetFolderPath('Desktop')",
                            '$desktopShortcut = $ws.CreateShortcut("$desktop\\Xournal.lnk")',
                            '$desktopShortcut.TargetPath = "$dir\\bin\\xournalpp.exe"',
                            '$desktopShortcut.WorkingDirectory = "$dir"',
                            '$desktopShortcut.IconLocation = "$dir\\bin\\xournalpp.exe"',
                            "$desktopShortcut.Save()",
                        ]

                    if app == "neovide":
                        add_neovide_shortcut(data)

                    if app == "autohotkey":
                        data = {
                            "version": data["version"],
                            "description": "Minimal AutoHotkey v2 (64-bit only) with only AutoHotkey64.exe and WindowSpy.ahk.",
                            "homepage": data["homepage"],
                            "license": data["license"],
                            "url": data["url"],
                            "hash": data["hash"],
                            "architecture": {
                                "64bit": {"bin": [["AutoHotkey64.exe", "AutoHotkey64"]]}
                            },
                            "post_install": [
                                'Copy-Item "$dir\\UX\\WindowSpy.ahk" "$dir" -Force',
                                "Get-ChildItem $dir -Recurse | Where-Object {",
                                '    $_.FullName -notlike "$dir\\AutoHotkey64.exe" -and',
                                '    $_.FullName -notlike "$dir\\WindowSpy.ahk"',
                                "} | Remove-Item -Force -Recurse",
                            ],
                            "checkver": data.get("checkver", {}),
                            "autoupdate": data.get("autoupdate", {}),
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
