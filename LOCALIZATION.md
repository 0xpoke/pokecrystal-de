# German Pokémon Crystal Localization Workflow

This guide explains how to extract German text from your German Pokémon Crystal ROM and integrate it into the PRET disassembly structure.

## Prerequisites

- Your German Pokémon Crystal ROM file (`.gbc`)
- The English PRET disassembly as your base (already in this repo)
- Python 3.6+
- The charmap already supports German characters (ä, ö, ü, Ä, Ö, Ü)

## Step 1: Build the Map File

First, generate the memory map from the English disassembly:

```bash
make
```

This creates:
- `pokecrystal.map` - Memory addresses of all symbols
- `pokecrystal.sym` - Symbol definitions for debuggers

## Step 2: Extract Text from German ROM

Use the extraction tool to decode text from your German ROM:

```bash
python3 tools/extract_rom_text.py <path-to-german-rom.gbc> extracted_german_text.txt
```

**Example:**
```bash
python3 tools/extract_rom_text.py ~/roms/pokemon_crystal_german.gbc extracted_german_text.txt
```

This will:
1. Parse `constants/charmap.asm` for character encoding
2. Read the German ROM
3. Use addresses from `pokecrystal.map` to find text strings
4. Decode bytes to characters using the charmap
5. Output all extracted text to `extracted_german_text.txt`

## Step 3: Create a Translation Mapping

The extraction tool gives you a file like:

```
## BillPhoneMornGreetingText
Address: 0x1a5c2
Text: Guten Morgen!

## BillPhoneDayGreetingText
Address: 0x1a5d5
Text: Guten Tag!
```

Create a translation spreadsheet or file mapping English → German for each text block.

## Step 4: Replace Text in ASM Files

For each text symbol in the disassembly:

**Original (English):**
```asm
BillPhoneMornGreetingText:
	text "Good morning!"
	para "This is the #-"
	line "MON STORAGE SYSTEM"
	done
```

**Translated (German):**
```asm
BillPhoneMornGreetingText:
	text "Guten Morgen!"
	para "Das ist das #-"
	line "MON-SPEICHERSYSTEM"
	done
```

### Important Notes:

- Keep the code structure identical
- Don't change symbol names
- Don't move or remove any `text`, `para`, `line`, `cont`, or `done` directives
- Watch for text length - German can be longer than English
  - If text overflows, break it into multiple lines with `line` or `cont`
- Special codes like `<PLAY_G>`, `<PLAYER>`, `#`, `@` stay the same

## Step 5: Test Assembly

After replacing text:

```bash
make clean
make
```

If there are errors:
1. Check the error message - usually indicates which file has the problem
2. Common issues:
   - Text too long for the allocated space
   - Typo in control codes (like `<PLAYER>`)
   - Missing `done` or `text_end` marker
3. Fix the text and retry

## Step 6: Compare ROMs

To verify your German text appears correctly:

1. Assemble the German version: `make` creates `pokecrystal.gbc`
2. Load it in an emulator (BGB, mGBA, etc.)
3. Check that German text displays properly
4. Watch for:
   - Text overflow in dialog boxes
   - Missing umlauts (ä, ö, ü)
   - Garbled control codes

## Character Encoding Reference

The charmap maps these important characters:

| Character | Byte | Use |
|-----------|------|-----|
| `ä` | `$c3` | German lowercase |
| `ö` | `$c4` | German lowercase |
| `ü` | `$c5` | German lowercase |
| `Ä` | `$c0` | German uppercase |
| `Ö` | `$c1` | German uppercase |
| `Ü` | `$c2` | German uppercase |
| `@` | `$50` | String terminator |
| `<PLAYER>` | `$52` | Player name |
| `<RIVAL>` | `$53` | Rival name |
| `#` | `$54` | POKé symbol |

**Note:** `ß` (German eszett) is **not currently mapped**. You have options:
1. Use "ss" instead temporarily
2. Find which byte the German ROM uses for `ß` and add it to charmap.asm
3. Leave as TODO for now, come back later

## File Organization

Key directories for text:

```
data/
├── phone/text/        # NPC phone dialogue
│   ├── bill.asm
│   ├── mom.asm
│   └── ...
├── text/              # General text strings
│   └── ...
└── ...

engine/
├── battle/            # Battle text
└── ...

maps/
└── <location>/text/   # Location-specific dialogue
```

## Workflow Summary

1. **Extract:** `python3 tools/extract_rom_text.py german.gbc output.txt`
2. **Map:** Create translation file (English → German)
3. **Replace:** Edit `.asm` files with German text
4. **Test:** `make` and verify in emulator
5. **Iterate:** Fix any issues and repeat

## Tips

- Start with one file (like `data/phone/text/bill.asm`)
- Test assembly after each change
- Use a hex editor to verify text at known ROM addresses
- Keep the English version handy for reference
- Commit your changes to git as you go

## Troubleshooting

**"charmap.asm not found"**
- Run the script from the repo root
- Ensure `constants/charmap.asm` exists

**"pokecrystal.map not found"**
- Run `make` first to generate the map file

**Assembly fails with "string too long"**
- Text probably exceeds allocated space
- Break into multiple lines using `line` or `cont`
- Example:
  ```asm
  text "Very long German"
  line "text split here."
  done
  ```

**German characters show as ???**
- Verify charmap.asm has the character
- Check that you're using the correct byte code
- Example: use `$c3` for `ä`, not `$e4`

**Text overlaps in dialog box**
- German words are often longer than English
- Shorten the translation or break into multiple lines
- Test in emulator to see visual result

## Resources

- PRET Pokémon Crystal: https://github.com/pret/pokecrystal
- Game Boy Assembly: https://gbdev.io/
- Pokémon Disassembly Wiki: https://github.com/pret/pokecrystal/wiki

