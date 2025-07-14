#!/usr/bin/env python3
"""
Command Line Interface for Smart Media Icon System
"""

import sys
import argparse
import logging
from pathlib import Path

from .core.icon_setter import SmartIconSetter
from .utils.config import Config

def setup_logging(verbose=False):
    """Configure logging with professional formatting."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(name)s - %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=[console_handler],
        force=True
    )
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Smart Media Icon System - Professional media organization tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    smart-media-icon "C:\\Media"                    # Process media directory
    smart-media-icon "D:\\Movies" --verbose         # Verbose output
    smi "E:\\TV" --config myconfig.json             # Custom config (short command)
        """
    )
    
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Media directory to process (default: current directory)'
    )
    
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
        '--version',
        action='version',
        version='Smart Media Icon System v1.0.0'
    )
    
    return parser.parse_args()

def validate_directory(directory_path):
    """Validate the target directory."""
    path = Path(directory_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory_path}")
    
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory_path}")
    
    return path.resolve()

def main():
    """Main CLI entry point."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Setup logging
        setup_logging(verbose=args.verbose)
        logger = logging.getLogger('smart_media_icon.cli')
        
        logger.info("🎬 Smart Media Icon System v1.0.0")
        logger.info("=" * 50)
        
        # Validate directory
        try:
            media_directory = validate_directory(args.directory)
            logger.info(f"📁 Target directory: {media_directory}")
        except (FileNotFoundError, NotADirectoryError) as e:
            logger.error(f"❌ {e}")
            return 1
        
        # Load configuration
        try:
            config = Config(args.config)
            logger.info(f"⚙️  Configuration loaded from: {args.config}")
        except Exception as e:
            logger.error(f"❌ Configuration error: {e}")
            return 1
        
        # Initialize Smart Icon Setter
        try:
            icon_setter = SmartIconSetter(config)
            logger.info("🔧 Smart Icon Setter initialized")
        except Exception as e:
            logger.error(f"❌ Initialization error: {e}")
            return 1
        
        # Process media collection
        logger.info("🚀 Processing media collection...")
        try:
            success_count = icon_setter.process_media_collection(str(media_directory))
            
            if success_count > 0:
                logger.info(f"✅ Processing complete: {success_count} items processed successfully")
                return 0
            else:
                logger.warning("⚠️  No items were processed successfully")
                return 1
                
        except KeyboardInterrupt:
            logger.info("⏹️  Processing interrupted by user")
            return 1
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
            return 1
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
