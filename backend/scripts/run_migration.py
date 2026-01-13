#!/usr/bin/env python3
"""
Quick migration runner for Railway deployment.
Run with: python run_migration.py
"""
import subprocess
import sys
import os

def main():
    print("🚀 Starting entity_type migration...")
    print("="*60)
    
    # Ensure we're in the backend directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    os.chdir(backend_dir)
    
    # Run the migration script
    result = subprocess.run(
        [sys.executable, "scripts/migrate_entity_type.py"],
        cwd=backend_dir
    )
    
    if result.returncode == 0:
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart the backend service")
        print("2. Test that foreign entities show tooltip instead of 404")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
