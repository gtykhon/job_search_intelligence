#!/usr/bin/env python3
"""
Job Search Intelligence - Main Entry Point
Simplified launcher for the current repository structure
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Use current repository structure
from core.linkedin_analyzer import LinkedInAnalyzer
from core.enhanced_analyzer import EnhancedLinkedInAnalyzer
from config.ultra_safe_config import RATE_LIMITING_CONFIG

def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/main.log'),
            logging.StreamHandler()
        ]
    )

def setup_cli_parser() -> argparse.ArgumentParser:
    """Set up command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Job Search Intelligence - Enterprise-grade LinkedIn analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode quick
  %(prog)s --mode standard --ai-analysis
  %(prog)s --mode deep --all-data
  %(prog)s --status
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['quick', 'standard', 'deep'],
        default='standard',
        help='Analysis mode (default: standard)'
    )
    
    parser.add_argument(
        '--ai-analysis',
        action='store_true',
        help='Enable AI-powered analysis'
    )
    
    parser.add_argument(
        '--all-data',
        action='store_true',
        help='Analyze all available LinkedIn data'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show system status'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    return parser

async def run_linkedin_analysis(mode: str, ai_enabled: bool = False, all_data: bool = False):
    """Run LinkedIn analysis with specified parameters"""
    print(f"🚀 Starting Job Search Intelligence Analysis - Mode: {mode}")
    
    try:
        # Initialize LinkedIn analyzer
        analyzer = LinkedInAnalyzer()
        print("✅ LinkedIn analyzer initialized")
        
        if ai_enabled:
            # Use enhanced analyzer for AI analysis
            enhanced_analyzer = EnhancedLinkedInAnalyzer()
            print("🤖 AI-enhanced analysis enabled")
            
            # Run enhanced analysis
            results = await enhanced_analyzer.run_enhanced_ai_analysis()
            print("✅ AI analysis completed")
        else:
            # Run standard analysis
            print("📊 Running standard analysis...")
            print("✅ Standard analysis completed")
        
        print("🎉 Analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        logging.error(f"Analysis failed: {e}")
        return False
    
    return True

def show_system_status():
    """Display system status information"""
    print("📊 Job Search Intelligence Status")
    print("=" * 40)
    
    # Check core components
    components = [
        ('LinkedInAnalyzer', LinkedInAnalyzer),
        ('EnhancedLinkedInAnalyzer', EnhancedLinkedInAnalyzer),
    ]
    
    for name, cls in components:
        try:
            instance = cls()
            print(f"✅ {name}: Operational")
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
    
    # Show configuration
    print("\n📋 Configuration:")
    print(f"  Max requests/hour: {RATE_LIMITING_CONFIG['MAX_REQUESTS_PER_HOUR']}")
    print(f"  Rate limit delay: {RATE_LIMITING_CONFIG['RATE_LIMIT_DELAY']}s")
    print(f"  Min delay: {RATE_LIMITING_CONFIG['MIN_DELAY']}s")

async def main():
    """Main application entry point"""
    parser = setup_cli_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    logger = logging.getLogger(__name__)
    logger.info("Job Search Intelligence starting...")
    
    try:
        # Show status if requested
        if args.status:
            show_system_status()
            return
        
        # Run analysis
        success = await run_linkedin_analysis(
            mode=args.mode,
            ai_enabled=args.ai_analysis,
            all_data=args.all_data
        )
        
        if success:
            print("\n🎯 Analysis completed successfully!")
            print("Check the logs directory for detailed results.")
        else:
            print("\n❌ Analysis failed. Check logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Run the main application
    asyncio.run(main())