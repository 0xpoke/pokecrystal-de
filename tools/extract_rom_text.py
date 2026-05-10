#!/usr/bin/env python3
"""
Extract text strings from a Pokémon Crystal ROM using charmap encoding.

Usage:
    python3 extract_rom_text.py <rom_file> [output_file]

This script:
1. Parses constants/charmap.asm to build the character encoding
2. Parses pokecrystal.map to find text symbol addresses
3. Reads the ROM file as binary
4. Extracts and decodes text at those addresses
5. Outputs decoded text in a readable format
"""

import sys
import re
from pathlib import Path


def parse_charmap(charmap_file):
    """
    Parse constants/charmap.asm and build a byte-to-character mapping.
    
    Returns:
        dict: Maps byte value (int) to character (str)
    """
    charmap = {}
    
    with open(charmap_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith(';'):
                continue
            
            # Match: charmap "char", $XX
            match = re.match(r'charmap\s+"([^"]+)",\s+\$([0-9a-fA-F]+)', line)
            if match:
                char = match.group(1)
                byte_val = int(match.group(2), 16)
                charmap[byte_val] = char
    
    return charmap


def decode_rom_text(rom_bytes, address, charmap, max_length=256):
    """
    Decode a null-terminated string from ROM at the given address.
    
    Args:
        rom_bytes: ROM data as bytes
        address: Address to start reading from (absolute ROM address)
        charmap: byte -> character mapping
        max_length: Maximum string length to prevent runaway reads
    
    Returns:
        tuple: (decoded_text, length_in_bytes) or (None, 0) if invalid address
    """
    if address >= len(rom_bytes):
        return None, 0
    
    text = []
    pos = 0
    
    while pos < max_length:
        byte = rom_bytes[address + pos]
        
        # 0x50 is the string terminator (@)
        if byte == 0x50:
            break
        
        # Check if byte is in charmap
        if byte in charmap:
            text.append(charmap[byte])
        else:
            # Unknown byte - represent as hex code
            text.append(f'[0x{byte:02x}]')
        
        pos += 1
    
    return ''.join(text), pos + 1  # +1 for the terminator


def bank_address_to_rom_offset(bank, address):
    """
    Convert Game Boy bank:address to absolute ROM offset.
    
    Bank 0: $0000-$3FFF (addresses 0x0000-0x3FFF)
    Banks 1+: each is 0x4000 bytes starting at ROM offset 0x4000
    
    Args:
        bank: Bank number (0-127)
        address: Address within bank ($0000-$3FFF)
    
    Returns:
        int: Absolute ROM offset
    """
    if bank == 0:
        return address
    else:
        return 0x4000 + (bank - 1) * 0x4000 + address


def parse_map_file(map_file):
    """
    Parse pokecrystal.map to find text symbol addresses.
    
    Format:
    ROM0 bank #0:
        SECTION: $0000-$0003 ($0004 bytes) ["sectionname"]
                 $0000 = SymbolName
    
    ROMX bank #1:
        SECTION: $4000-$5FFF ($2000 bytes) ["sectionname"]
                 $4000 = TextSymbol
    
    Returns:
        dict: Maps symbol name to ROM offset (int)
    """
    symbols = {}
    current_bank = 0
    current_section_start = 0
    
    with open(map_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Parse bank header: "ROM0 bank #0:" or "ROMX bank #1:"
            bank_match = re.match(r'^(ROM0|ROMX)\s+bank\s+#(\d+):', line)
            if bank_match:
                current_bank = int(bank_match.group(2))
                continue
            
            # Parse symbol: "         $XXXX = SymbolName"
            symbol_match = re.match(r'\s+\$([0-9a-fA-F]+)\s*=\s*(\S+)', line)
            if symbol_match:
                address = int(symbol_match.group(1), 16)
                symbol_name = symbol_match.group(2)
                
                # Only store text-related symbols
                if 'Text' in symbol_name or 'text' in symbol_name:
                    # Convert bank:address to ROM offset
                    rom_offset = bank_address_to_rom_offset(current_bank, address)
                    symbols[symbol_name] = rom_offset
    
    return symbols


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_rom_text.py <rom_file> [output_file]")
        print("\nExtract text strings from Pokémon Crystal ROM.")
        print("Uses constants/charmap.asm for character encoding.")
        print("Uses pokecrystal.map for text symbol addresses.")
        sys.exit(1)
    
    rom_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('extracted_text.txt')
    
    # Find charmap and map files relative to script location
    script_dir = Path(__file__).parent.parent
    charmap_file = script_dir / 'constants' / 'charmap.asm'
    map_file = script_dir / 'pokecrystal.map'
    
    # Validate files exist
    if not rom_path.exists():
        print(f"Error: ROM file not found: {rom_path}")
        sys.exit(1)
    
    if not charmap_file.exists():
        print(f"Error: charmap.asm not found: {charmap_file}")
        print("Run this script from the pokecrystal-de repository root.")
        sys.exit(1)
    
    if not map_file.exists():
        print(f"Error: {map_file} not found.")
        print("First, run: make")
        print("This will generate pokecrystal.map and pokecrystal.sym")
        sys.exit(1)
    
    # Load data
    print("[1/4] Loading charmap...")
    charmap = parse_charmap(charmap_file)
    print(f"      Loaded {len(charmap)} character mappings")
    
    print("[2/4] Loading map file...")
    symbols = parse_map_file(map_file)
    print(f"      Found {len(symbols)} text symbols")
    
    if len(symbols) == 0:
        print("\n⚠ Warning: No text symbols found in map file!")
        print("Check that pokecrystal.map exists and has the correct format.")
        sys.exit(1)
    
    print("[3/4] Loading ROM...")
    with open(rom_path, 'rb') as f:
        rom_bytes = f.read()
    print(f"      ROM size: {len(rom_bytes)} bytes ({len(rom_bytes) / 1024 / 1024:.2f} MB)")
    
    print("[4/4] Extracting text...")
    
    extracted_text = {}
    extracted_count = 0
    
    for symbol_name in sorted(symbols.keys()):
        rom_offset = symbols[symbol_name]
        
        # Extract text
        text, length = decode_rom_text(rom_bytes, rom_offset, charmap)
        
        if text and len(text) > 0:
            extracted_text[symbol_name] = {
                'offset': f'0x{rom_offset:06x}',
                'length': length,
                'text': text
            }
            extracted_count += 1
    
    # Write output
    print(f"\nWriting output to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Extracted Pokémon Crystal German ROM Text\n\n")
        f.write(f"Total strings extracted: {extracted_count}/{len(symbols)}\n\n")
        f.write("=" * 80 + "\n\n")
        
        for symbol_name in sorted(extracted_text.keys()):
            data = extracted_text[symbol_name]
            f.write(f"## {symbol_name}\n")
            f.write(f"ROM Offset: {data['offset']}\n")
            f.write(f"Length:     {data['length']} bytes\n")
            f.write(f"Text:       {data['text']}\n")
            f.write("\n")
    
    print(f"✓ Extracted {extracted_count}/{len(symbols)} text strings")
    print(f"✓ Output written to: {output_path}")
    
    if extracted_count < len(symbols):
        print(f"\n⚠ Note: Only extracted {extracted_count} out of {len(symbols)} symbols")
        print("Some text strings may be empty or corrupted in the ROM.")


if __name__ == '__main__':
    main()
