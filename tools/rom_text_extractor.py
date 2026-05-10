#!/usr/bin/env python3
"""
ROM Text Extractor for Pokémon Crystal Localization
Extracts text from a ROM using the charmap.asm encoding
"""

import re
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional


class CharmapParser:
    """Parse charmap.asm and build byte-to-character mapping"""
    
    def __init__(self, charmap_path: str):
        self.byte_to_char: Dict[int, str] = {}
        self.char_to_byte: Dict[str, int] = {}
        self.parse(charmap_path)
    
    def parse(self, charmap_path: str):
        """Parse charmap.asm file"""
        with open(charmap_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Match: charmap "char", $xx
        pattern = r'charmap\s+"([^"]+)"\s*,\s*\$([0-9a-fA-F]{2})'
        
        for match in re.finditer(pattern, content):
            char = match.group(1)
            byte_val = int(match.group(2), 16)
            
            # Handle escape sequences
            char = char.replace('\\n', '\n').replace('\\t', '\t')
            
            self.byte_to_char[byte_val] = char
            self.char_to_byte[char] = byte_val
    
    def decode(self, rom_bytes: bytes, address: int, max_length: Optional[int] = None) -> Tuple[str, int]:
        """
        Decode text starting at address until terminator (0x50 = '@')
        Returns: (text, bytes_read)
        """
        text = []
        i = 0
        max_len = max_length or (len(rom_bytes) - address)
        
        while i < max_len and address + i < len(rom_bytes):
            byte = rom_bytes[address + i]
            
            if byte == 0x50:  # '@' terminator
                i += 1
                break
            
            if byte in self.byte_to_char:
                text.append(self.byte_to_char[byte])
            else:
                # Unknown byte - use placeholder
                text.append(f'[0x{byte:02x}]')
            
            i += 1
        
        return ''.join(text), i
    
    def encode(self, text: str) -> bytes:
        """Encode text string to ROM bytes"""
        encoded = []
        
        i = 0
        while i < len(text):
            # Try multi-character sequences first (like "<CONT>")
            found = False
            for length in range(min(10, len(text) - i), 0, -1):
                substr = text[i:i+length]
                if substr in self.char_to_byte:
                    encoded.append(self.char_to_byte[substr])
                    i += length
                    found = True
                    break
            
            if not found:
                # Try single character
                if text[i] in self.char_to_byte:
                    encoded.append(self.char_to_byte[text[i]])
                    i += 1
                else:
                    raise ValueError(f"Character '{text[i]}' at position {i} not in charmap")
        
        # Add terminator
        encoded.append(0x50)  # '@'
        return bytes(encoded)


class ROMTextExtractor:
    """Extract text from ROM using .map file"""
    
    def __init__(self, rom_path: str, charmap_path: str):
        self.rom_path = rom_path
        self.charmap = CharmapParser(charmap_path)
        
        with open(rom_path, 'rb') as f:
            self.rom = f.read()
    
    def extract_at_address(self, address: int, label: Optional[str] = None) -> str:
        """Extract text at specific address"""
        text, _ = self.charmap.decode(self.rom, address)
        return text
    
    def find_text_by_pattern(self, pattern: str, max_results: int = 10) -> list:
        """Find all occurrences of a text pattern in ROM"""
        results = []
        
        try:
            encoded = self.charmap.encode(pattern)
        except ValueError as e:
            print(f"Error encoding pattern: {e}")
            return results
        
        # Search for pattern in ROM
        search_bytes = bytes(encoded[:-1])  # Without terminator for searching
        
        address = 0
        count = 0
        while count < max_results:
            pos = self.rom.find(search_bytes, address)
            if pos == -1:
                break
            
            text, _ = self.charmap.decode(self.rom, pos)
            results.append((pos, text))
            
            address = pos + 1
            count += 1
        
        return results
    
    def extract_range(self, start: int, end: int) -> list:
        """Extract all text strings in a ROM range"""
        results = []
        address = start
        
        while address < end and address < len(self.rom):
            # Look for string starts (usually preceded by null or specific patterns)
            text, length = self.charmap.decode(self.rom, address)
            
            if text and length > 1:  # Found a non-empty string
                results.append((address, text))
                address += length
            else:
                address += 1
        
        return results


def main():
    """Example usage"""
    if len(sys.argv) < 2:
        print("Usage: python rom_text_extractor.py <rom_path> [charmap_path]")
        print("\nExample:")
        print("  python rom_text_extractor.py german_crystal.gbc constants/charmap.asm")
        sys.exit(1)
    
    rom_path = sys.argv[1]
    charmap_path = sys.argv[2] if len(sys.argv) > 2 else "constants/charmap.asm"
    
    if not Path(rom_path).exists():
        print(f"Error: ROM not found: {rom_path}")
        sys.exit(1)
    
    if not Path(charmap_path).exists():
        print(f"Error: Charmap not found: {charmap_path}")
        sys.exit(1)
    
    print(f"Loading ROM: {rom_path}")
    print(f"Using charmap: {charmap_path}")
    
    extractor = ROMTextExtractor(rom_path, charmap_path)
    
    # Example: Extract text at address 0x12345 (replace with real address from .map)
    print("\n--- Text Extraction Tool ---")
    print("Available methods:")
    print("1. extract_at_address(address) - Extract text at specific address")
    print("2. find_text_by_pattern(text) - Find text occurrences in ROM")
    print("3. extract_range(start, end) - Extract all text in address range")
    print("\nExample usage in Python:")
    print("  extractor.extract_at_address(0x12345)")
    print("  extractor.find_text_by_pattern('Good morning')")


if __name__ == "__main__":
    main()
