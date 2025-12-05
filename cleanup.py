"""
🧹 Automated Project Cleanup Script

This script safely removes unnecessary files before deployment:
- Python cache directories (__pycache__)
- Log files (*.log)
- Temporary output files
- Old test/debug files
- Old pickle persistence files

Run this before pushing to GitHub!
"""

import os
import shutil
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent

# Files and directories to delete
TO_DELETE = [
    # Cache directories
    "__pycache__",
    "core/__pycache__",
    "api/__pycache__",
    
    # Log files
    "api.log",
    
    # Temporary output files
    "output.txt",
    "output_2.txt",
    
    # Old test/debug files
    "registry_state.pkl",
    "test_pickle.pkl",
    "test_pickle.py",
]

# Directories to clear (but keep the directory itself)
TO_CLEAR = [
    "data/registry",  # Clear old demo data
]


def delete_file_or_dir(path: Path):
    """Safely delete a file or directory."""
    if not path.exists():
        print(f"⏭️  Skip (not found): {path}")
        return
    
    try:
        if path.is_dir():
            shutil.rmtree(path)
            print(f"🗑️  Deleted directory: {path}")
        else:
            path.unlink()
            print(f"🗑️  Deleted file: {path}")
    except Exception as e:
        print(f"❌ Error deleting {path}: {e}")


def clear_directory(path: Path):
    """Clear all contents of a directory but keep the directory."""
    if not path.exists():
        print(f"⏭️  Skip (not found): {path}")
        return
    
    try:
        for item in path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        print(f"🧹 Cleared directory: {path}")
    except Exception as e:
        print(f"❌ Error clearing {path}: {e}")


def main():
    """Run the cleanup process."""
    print("=" * 60)
    print("🧹 BIAS DRIFT GUARDIAN - PROJECT CLEANUP")
    print("=" * 60)
    print()
    
    # Confirm with user
    print("This will delete:")
    for item in TO_DELETE:
        print(f"  - {item}")
    print()
    print("And clear:")
    for item in TO_CLEAR:
        print(f"  - {item}/*")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Cleanup cancelled.")
        return
    
    print()
    print("Starting cleanup...")
    print("-" * 60)
    
    # Delete files and directories
    for item in TO_DELETE:
        path = PROJECT_ROOT / item
        delete_file_or_dir(path)
    
    # Clear directories
    for item in TO_CLEAR:
        path = PROJECT_ROOT / item
        clear_directory(path)
    
    print("-" * 60)
    print()
    print("✅ Cleanup complete!")
    print()
    print("Next steps:")
    print("1. Verify everything works:")
    print("   python -c \"from core.drift_detector import DriftDetector\"")
    print()
    print("2. Check git status:")
    print("   git status")
    print()
    print("3. Ready for deployment!")
    print()


if __name__ == "__main__":
    main()
