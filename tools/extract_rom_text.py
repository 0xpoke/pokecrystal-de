#!/usr/bin/env python3
"""
Extract text strings from a Pokémon Crystal ROM using charmap encoding.

Usage:
    python3 extract_rom_text.py <rom_file> <output_file>

This script:
1. Parses constants/charmap.asm to build the character encoding
2. Reads the ROM file as binary
3. Extracts text at known addresses (from .map file)
4. Outputs decoded text in a readable format
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
        address: Address to start reading from
        charmap: byte -> character mapping
        max_length: Maximum string length to prevent runaway reads
    
    Returns:
        str: Decoded text, or None if address is out of bounds
    """
    if address >= len(rom_bytes):
        return None
    
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
    
    return ''.join(text)


def parse_map_file(map_file):
    """
    Parse pokecrystal.map to find text symbol addresses.
    
    Returns:
        dict: Maps symbol name to address (int)
    """
    symbols = {}
    
    with open(map_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Try to parse: ADDRESS SYMBOLNAME
            parts = line.split()
            if len(parts) >= 2:
                try:
                    addr = int(parts[0], 16)
                    name = parts[1]
                    # Only store text-related symbols
                    if 'Text' in name or 'text' in name:
                        symbols[name] = addr
                except ValueError:
                    pass
    
    return symbols


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_rom_text.py <rom_file> [output_file]")
        print("\nExtract text strings from Pokémon Crystal ROM.")
        print("Uses constants/charmap.asm for character encoding.")
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
        print(f"Warning: {map_file} not found.")
        print("First, run: make")
        print("This will generate pokecrystal.map and pokecrystal.sym")
    
    # Load data
    print("[1/3] Loading charmap...")
    charmap = parse_charmap(charmap_file)
    print(f"      Loaded {len(charmap)} character mappings")
    
    print("[2/3] Loading ROM...")
    with open(rom_path, 'rb') as f:
        rom_bytes = f.read()
    print(f"      ROM size: {len(rom_bytes)} bytes ({len(rom_bytes) / 1024 / 1024:.2f} MB)")
    
    print("[3/3] Extracting text...")
    
    # If map file exists, use it to find known text locations
    extracted_text = {}
    if map_file.exists():
        symbols = parse_map_file(map_file)
        print(f"      Found {len(symbols)} text symbols")
        
        for symbol_name, address in sorted(symbols.items(), key=lambda x: x[1]):
            text = decode_rom_text(rom_bytes, address, charmap)
            if text:
                extracted_text[symbol_name] = {
                    'address': f'0x{address:06x}',
                    'text': text
                }
    
    # Write output
    print(f"\nWriting output to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Extracted Pokémon Crystal ROM Text\n\n")
        f.write(f"Total strings extracted: {len(extracted_text)}\n\n")
        
        for symbol_name in sorted(extracted_text.keys()):
            data = extracted_text[symbol_name]
            f.write(f"## {symbol_name}\n")
            f.write(f"Address: {data['address']}\n")
            f.write(f"Text: {data['text']}\n\n")
    
    print(f"✓ Extracted {len(extracted_text)} text strings")
    print(f"✓ Output written to: {output_path}")


if __name__ == '__main__':
    main()
