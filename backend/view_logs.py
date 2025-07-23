#!/usr/bin/env python
"""
Utility script to view and tail log files
"""
import os
import sys
import argparse
from pathlib import Path
import subprocess

LOGS_DIR = Path(__file__).parent / 'logs'

def list_logs():
    """List all available log files"""
    if not LOGS_DIR.exists():
        print("❌ Logs directory not found")
        return
    
    log_files = list(LOGS_DIR.glob('*.log'))
    if not log_files:
        print("❌ No log files found")
        return
    
    print("📁 Available log files:")
    for i, log_file in enumerate(log_files, 1):
        size = log_file.stat().st_size / 1024  # KB
        print(f"  {i}. {log_file.name} ({size:.1f} KB)")
    
    return log_files

def view_log(log_file, lines=50, follow=False):
    """View or tail a log file"""
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        return
    
    if follow:
        # Use tail -f for following
        print(f"📜 Following {log_file.name} (Ctrl+C to stop)...")
        try:
            subprocess.run(['tail', '-f', str(log_file)])
        except KeyboardInterrupt:
            print("\n✅ Stopped tailing log")
    else:
        # Show last N lines
        print(f"📜 Last {lines} lines of {log_file.name}:")
        print("=" * 80)
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            for line in all_lines[-lines:]:
                print(line.rstrip())

def main():
    parser = argparse.ArgumentParser(description='View Finance Hub log files')
    parser.add_argument('log_name', nargs='?', help='Log file name (e.g., django, pluggy, banking)')
    parser.add_argument('-n', '--lines', type=int, default=50, help='Number of lines to show (default: 50)')
    parser.add_argument('-f', '--follow', action='store_true', help='Follow log file (like tail -f)')
    parser.add_argument('-l', '--list', action='store_true', help='List available log files')
    
    args = parser.parse_args()
    
    if args.list or not args.log_name:
        list_logs()
        return
    
    # Find log file
    log_file = None
    if args.log_name.endswith('.log'):
        log_file = LOGS_DIR / args.log_name
    else:
        log_file = LOGS_DIR / f"{args.log_name}.log"
    
    view_log(log_file, args.lines, args.follow)

if __name__ == "__main__":
    main()