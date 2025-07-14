#!/usr/bin/env python3
"""
Smart Media Icon System - Main Entry Point

This is the unified entry point that supports both CLI and tray application modes.
Users can choose which interface to use based on command line arguments.
"""

import sys
import argparse
from pathlib import Path

# Add src to path for development
src_path = Path(__file__).parent / 'src'
if src_path.exists():
    sys.path.insert(0, str(src_path))


def create_argument_parser():
    """Create the main argument parser"""
    parser = argparse.ArgumentParser(
        description="Smart Media Icon System - Professional media organization tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage Examples:
    python main.py --tray                          # Run as tray application
    python main.py --cli "C:\\Media"               # Run as CLI
    python main.py "D:\\Movies" --verbose          # CLI with verbose output
    python main.py --tray --config myconfig.json  # Tray with custom config
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--tray', 
        action='store_true',
        help='Run as Windows system tray application (default if no directory specified)'
    )
    mode_group.add_argument(
        '--cli', 
        action='store_true',
        help='Run as command line interface'
    )
    
    # Directory argument (for CLI mode)
    parser.add_argument(
        'directory',
        nargs='?',
        help='Media directory to process (CLI mode only, default: current directory)'
    )
    
    # Common arguments
    parser.add_argument(
        '--config', '-c',
        default='config.json',
        help='Configuration file path (default: config.json)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--minimized',
        action='store_true',
        help='Start tray application minimized (tray mode only)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Smart Media Icon System v1.0.0'
    )
    
    return parser


def determine_mode(args):
    """Determine which mode to run based on arguments"""
    if args.tray:
        return 'tray'
    elif args.cli:
        return 'cli'
    elif args.directory:
        # If directory is specified, default to CLI mode
        return 'cli'
    else:
        # If no directory specified, default to tray mode
        return 'tray'


def run_cli_mode(args):
    """Run the CLI application"""
    try:
        from smart_media_icon.cli import main as cli_main
        
        # Prepare CLI arguments
        cli_args = []
        
        if args.directory:
            cli_args.append(args.directory)
        elif not args.directory:
            cli_args.append('.')  # Current directory
        
        if args.config != 'config.json':
            cli_args.extend(['--config', args.config])
        
        if args.verbose:
            cli_args.append('--verbose')
        
        # Replace sys.argv temporarily for CLI
        original_argv = sys.argv[:]
        sys.argv = ['smart-media-icon'] + cli_args
        
        try:
            return cli_main()
        finally:
            sys.argv = original_argv
            
    except ImportError as e:
        print(f"❌ Error: Could not import CLI module: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ CLI Error: {e}")
        return 1


def run_tray_mode(args):
    """Run the tray application"""
    try:
        from smart_media_icon.tray.main import main as tray_main
        
        # Prepare tray arguments
        tray_args = ['smart_media_icon_tray']
        
        if args.config != 'config.json':
            tray_args.extend(['--config', args.config])
        
        if args.debug:
            tray_args.append('--debug')
        
        # Replace sys.argv temporarily for tray app
        original_argv = sys.argv[:]
        sys.argv = tray_args
        
        try:
            return tray_main()
        finally:
            sys.argv = original_argv
            
    except ImportError as e:
        print(f"❌ Error: Could not import tray module: {e}")
        print("💡 Make sure PyQt5 is installed: pip install PyQt5")
        return 1
    except Exception as e:
        print(f"❌ Tray Error: {e}")
        return 1


def setup_logging(args):
    """Setup logging based on arguments"""
    import logging
    
    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] %(name)s - %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def check_requirements():
    """Check if basic requirements are met"""
    try:
        import PyQt5
        import watchdog
        import requests
        import PIL
        return True
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("💡 Install dependencies with: pip install -r requirements.txt")
        return False


def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args)
    
    # Determine mode
    mode = determine_mode(args)
    
    print(f"🚀 Smart Media Icon System v1.0.0")
    print(f"🎯 Mode: {mode.upper()}")
    
    # Check requirements for tray mode
    if mode == 'tray' and not check_requirements():
        print("⚠️ Falling back to CLI mode due to missing dependencies")
        mode = 'cli'
    
    # Run appropriate mode
    try:
        if mode == 'tray':
            return run_tray_mode(args)
        else:
            return run_cli_mode(args)
            
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())