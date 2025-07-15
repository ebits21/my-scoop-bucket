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
    "winfsp-np",
    "ultravnc",
    "go",
    "rustdesk",
]  # Add your desired apps
DEST_DIR = "bucket"

UPSTREAMS = {
    "main": "https://raw.githubusercontent.com/ScoopInstaller/Main/master/bucket/",
    "extras": "https://raw.githubusercontent.com/ScoopInstaller/Extras/master/bucket/",
    "nerd-fonts": "https://raw.githubusercontent.com/matthewjberger/scoop-nerd-fonts/master/bucket/",
    "nonportable": "https://raw.githubusercontent.com/ScoopInstaller/Nonportable/master/bucket/",
}

os.makedirs(DEST_DIR, exist_ok=True)


def remove_item(data, item, app="manifest"):
    if item in data:
        print(f'Removing "{item}" from {app}.')
        del data[item]
    else:
        print(f'Could not remove "{item}" from {app}, not found.')


def update_post_install(data, script):
    if "post_install" in data and isinstance(data["post_install"], list):
        data["post_install"].extend(script)
    else:
        data["post_install"] = script


def update_uninstaller(data, script):
    # Check if "uninstaller" key exists and is a dictionary with a "script" key
    if (
        "uninstaller" in data
        and isinstance(data["uninstaller"], dict)
        and "script" in data["uninstaller"]
    ):
        # Append the new script to the existing script list
        data["uninstaller"]["script"].extend(script)
    else:
        # Create a new entry with the uninstall script
        data["uninstaller"] = {"script": script}


def add_desktop_shortcut(data, link_name, exe_path):
    link_name = link_name.capitalize()
    shortcut_commands = [
        "$ws = New-Object -ComObject WScript.Shell",
        "$desktop = [Environment]::GetFolderPath('Desktop')",
        f'$desktopShortcut = $ws.CreateShortcut("$desktop\\{link_name}.lnk")',
        f'$desktopShortcut.TargetPath = "$dir\\{exe_path}"',
        '$desktopShortcut.WorkingDirectory = "$dir"',
        f'$desktopShortcut.IconLocation = "$dir\\{exe_path}"',
        "$desktopShortcut.Save()",
    ]

    update_post_install(data, shortcut_commands)
    uninstall_desktop_shortcut(data, link_name)


def uninstall_desktop_shortcut(data, link_name):
    uninstall_script = [
        '$desktop = [Environment]::GetFolderPath("Desktop")',
        f'Remove-Item "$desktop\\{link_name}.lnk" -ErrorAction SilentlyContinue',
    ]

    update_uninstaller(data, uninstall_script)


def add_startmenu_shortcut(data, link_name, exe_path):
    link_name = link_name.capitalize()
    shortcut_commands = [
        f'New-Item -ItemType Directory -Path "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\{link_name}" -Force | Out-Null',
        "$ws = New-Object -ComObject WScript.Shell",
        f'$startMenuShortcut = $ws.CreateShortcut("$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\{link_name}\\{link_name}.lnk")',
        f'$startMenuShortcut.TargetPath = "$dir\\{exe_path}"',
        '$startMenuShortcut.WorkingDirectory = "$dir"',
        f'$startMenuShortcut.IconLocation = "$dir\\{exe_path}"',
        "$startMenuShortcut.Save()",
    ]

    update_post_install(data, shortcut_commands)
    uninstall_startmenu_shortcut(data, link_name)


def uninstall_startmenu_shortcut(data, link_name):
    uninstall_script = [
        f'Remove-Item "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\{link_name}\\{link_name}.lnk" -ErrorAction SilentlyContinue',
        f'Remove-Item "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\{link_name}" -ErrorAction SilentlyContinue -Recurse',
    ]

    update_uninstaller(data, uninstall_script)


def add_file_association(data, file_ext, prog_id, exe_path):
    association_script = [
        f"$ext = '{file_ext}'",
        f"$progID = '{prog_id}'",
        f'$exePath = "$dir\\{exe_path}"',
        "",
        "# 1. Associate .xopp with ProgID",
        'New-Item -Path "HKCU:\\Software\\Classes\\$ext" -Force | Out-Null',
        "Set-ItemProperty -Path \"HKCU:\\Software\\Classes\\$ext\" -Name '(default)' -Value $progID",
        "",
        "# 2. Define open command for ProgID",
        'New-Item -Path "HKCU:\\Software\\Classes\\$progID\\shell\\open\\command" -Force | Out-Null',
        'Set-ItemProperty -Path "HKCU:\\Software\\Classes\\$progID\\shell\\open\\command" -Name \'(default)\' -Value "`"$exePath`" `"%1`""',
        "",
        "# 3. Set icon for ProgID",
        'New-Item -Path "HKCU:\\Software\\Classes\\$progID\\DefaultIcon" -Force | Out-Null',
        'Set-ItemProperty -Path "HKCU:\\Software\\Classes\\$progID\\DefaultIcon" -Name \'(default)\' -Value "`"$exePath`",0"',
    ]

    update_post_install(data, association_script)
    uninstall_file_association(data, file_ext, prog_id)


def uninstall_file_association(data, file_ext, prog_id):
    uninstall_script = [
        f"$ext = '{file_ext}'",
        f"$progID = '{prog_id}'",
        "",
        "# Remove file extension association",
        'Remove-Item -Path "HKCU:\\Software\\Classes\\$ext" -Recurse -Force -ErrorAction SilentlyContinue',
        "",
        "# Remove ProgID definition",
        'Remove-Item -Path "HKCU:\\Software\\Classes\\$progID" -Recurse -Force -ErrorAction SilentlyContinue',
        "",
        "# Remove UserChoice if set (may override your settings)",
        'Remove-Item -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts\\$ext" -Recurse -Force -ErrorAction SilentlyContinue',
    ]

    update_uninstaller(data, uninstall_script)


# def setup_xournal(data):
#     uninstall_script = [
#         '$desktop = [Environment]::GetFolderPath("Desktop")',
#         'Remove-Item "$desktop\\Xournal.lnk" -ErrorAction SilentlyContinue',
#         'Remove-Item "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Xournal\\Xournal.lnk" -ErrorAction SilentlyContinue',
#         'Remove-Item "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Xournal" -ErrorAction SilentlyContinue -Recurse',
#         "$ext = '.xopp'",
#         "$progID = 'xournalpp.xoppfile'",
#         "",
#         "# Remove file extension association",
#         'Remove-Item -Path "HKCU:\\Software\\Classes\\$ext" -Recurse -Force -ErrorAction SilentlyContinue',
#         "",
#         "# Remove ProgID definition",
#         'Remove-Item -Path "HKCU:\\Software\\Classes\\$progID" -Recurse -Force -ErrorAction SilentlyContinue',
#         "",
#         "# Remove UserChoice if set (may override your settings)",
#         'Remove-Item -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts\\$ext" -Recurse -Force -ErrorAction SilentlyContinue',
#     ]

#     if "post_install" not in data:
#         data["post_install"] = [
#             'New-Item -ItemType Directory -Path "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Xournal" -Force | Out-Null',
#             "$ws = New-Object -ComObject WScript.Shell",
#             '$startMenuShortcut = $ws.CreateShortcut("$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Xournal\\Xournal.lnk")',
#             '$startMenuShortcut.TargetPath = "$dir\\bin\\xournalpp.exe"',
#             '$startMenuShortcut.WorkingDirectory = "$dir"',
#             '$startMenuShortcut.IconLocation = "$dir\\bin\\xournalpp.exe"',
#             "$startMenuShortcut.Save()",
#             "$desktop = [Environment]::GetFolderPath('Desktop')",
#             '$desktopShortcut = $ws.CreateShortcut("$desktop\\Xournal.lnk")',
#             '$desktopShortcut.TargetPath = "$dir\\bin\\xournalpp.exe"',
#             '$desktopShortcut.WorkingDirectory = "$dir"',
#             '$desktopShortcut.IconLocation = "$dir\\bin\\xournalpp.exe"',
#             "$desktopShortcut.Save()",
#             "$ext = '.xopp'",
#             "$progID = 'xournalpp.xoppfile'",
#             '$exePath = "$dir\\bin\\xournalpp.exe"',
#             "",
#             "# 1. Associate .xopp with ProgID",
#             'New-Item -Path "HKCU:\\Software\\Classes\\$ext" -Force | Out-Null',
#             "Set-ItemProperty -Path \"HKCU:\\Software\\Classes\\$ext\" -Name '(default)' -Value $progID",
#             "",
#             "# 2. Define open command for ProgID",
#             'New-Item -Path "HKCU:\\Software\\Classes\\$progID\\shell\\open\\command" -Force | Out-Null',
#             'Set-ItemProperty -Path "HKCU:\\Software\\Classes\\$progID\\shell\\open\\command" -Name \'(default)\' -Value "`"$exePath`" `"%1`""',
#             "",
#             "# 3. Set icon for ProgID",
#             'New-Item -Path "HKCU:\\Software\\Classes\\$progID\\DefaultIcon" -Force | Out-Null',
#             'Set-ItemProperty -Path "HKCU:\\Software\\Classes\\$progID\\DefaultIcon" -Name \'(default)\' -Value "`"$exePath`",0"',
#         ]

#     data["uninstaller"] = {"script": uninstall_script}


def setup_autohotkey(data):
    data = {
        "version": data["version"],
        "description": "Minimal AutoHotkey v2 (64-bit only) with only AutoHotkey64.exe and WindowSpy.ahk.",
        "homepage": data["homepage"],
        "license": data["license"],
        "url": data["url"],
        "hash": data["hash"],
        "architecture": {"64bit": {"bin": [["AutoHotkey64.exe", "AutoHotkey64"]]}},
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
    return data


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
                    remove_item(data, "shortcuts", app)

                    if app == "xournalpp":
                        add_desktop_shortcut(data, "xournal", "bin\\xournalpp.exe")
                        add_startmenu_shortcut(data, "xournal", "bin\\xournalpp.exe")
                        add_file_association(
                            data, ".xopp", "xournalpp.xoppfile", "bin\\xournalpp.exe"
                        )

                    if app == "neovide":
                        remove_item(data, "notes", app)
                        remove_item(data, "post_install", app)
                        remove_item(data, "pre_uninstall", app)
                        add_desktop_shortcut(data, "neovide", "neovide.exe")

                    if app == "autohotkey":
                        data = setup_autohotkey(data)

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
