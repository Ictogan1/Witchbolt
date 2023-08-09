# Witchbolt - A command-line python based mod manager for Baldur's Gate 3

WIP. Only currently working feature is activating mods.

## Usage

```python mod.py modsettings.lsx modfiles...```

Replace `modsettings.lsx` with the path to your modsettings.lsx file(usually `.steam/steam/steamapps/compatdata/1086940/pfx/drive_c/users/steamuser/AppData/Local/Larian\ Studios/Baldur\'s\ Gate\ 3/PlayerProfiles/Public/modsettings.lsx`) and mods with the list of mod `.pak` files you want to have enabled(usually `.steam/steam/steamapps/compatdata/1086940/pfx/drive_c/users/steamuser/AppData/Local/Larian\ Studios/Baldur\'s\ Gate\ 3/Mods/*.pak).

## Credits

- Code for handling Larian file formats is loosely based on the excellent LSLib from Norbyte: https://github.com/Norbyte/lslib
- Took some minor inspiration from LaughingLeader's Baldurs Gate 3 Mod Manager: https://github.com/LaughingLeader/BG3ModManager
