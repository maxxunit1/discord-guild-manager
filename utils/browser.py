"""
Utility module for loading data from files
"""

import os
import asyncio
from typing import List, Optional


async def load_data(filepath: str, start_line: int = 1, end_line: int = 9999) -> List[str]:
    """
    Load lines from a text file within specified range.

    Args:
        filepath: Path to the text file
        start_line: First line number to read (1-indexed)
        end_line: Last line number to read (inclusive)

    Returns:
        List of strings (lines) from the file, excluding comments and empty lines
    """
    if not os.path.exists(filepath):
        return []

    lines = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()

        # Process lines in the specified range
        for i in range(start_line - 1, min(end_line, len(all_lines))):
            line = all_lines[i].strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                lines.append(line)

    except Exception as e:
        print(f"Error loading data from {filepath}: {e}")
        return []

    return lines


def load_data_sync(filepath: str, start_line: int = 1, end_line: int = 9999) -> List[str]:
    """
    Synchronous version of load_data.

    Args:
        filepath: Path to the text file
        start_line: First line number to read (1-indexed)
        end_line: Last line number to read (inclusive)

    Returns:
        List of strings (lines) from the file, excluding comments and empty lines
    """
    if not os.path.exists(filepath):
        return []

    lines = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()

        # Process lines in the specified range
        for i in range(start_line - 1, min(end_line, len(all_lines))):
            line = all_lines[i].strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                lines.append(line)

    except Exception as e:
        print(f"Error loading data from {filepath}: {e}")
        return []

    return lines


def ensure_file_exists(filepath: str, default_content: str = "") -> bool:
    """
    Ensure a file exists, creating it with default content if necessary.

    Args:
        filepath: Path to the file
        default_content: Default content to write if file doesn't exist

    Returns:
        True if file exists or was created successfully, False otherwise
    """
    try:
        if not os.path.exists(filepath):
            # Create directory if it doesn't exist
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            # Create file with default content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(default_content)

        return True

    except Exception as e:
        print(f"Error ensuring file exists {filepath}: {e}")
        return False