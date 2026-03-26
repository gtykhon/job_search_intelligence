#!/usr/bin/env python3
"""
Enhanced Job Search Intelligence CLI

This script provides easy access to the enhanced LinkedIn analyzer that combines
real data collection with advanced network analytics from the old analyzer code.

Usage:
    python scripts/enhanced_linkedin_cli.py [--force-refresh] [--debug]

Features:
- Real LinkedIn data collection (356 connections verified)
- Advanced company and role extraction
- Connection strength scoring
- Location and industry clustering
- Comprehensive CSV and JSON exports
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add src to path
sys.path.append('src')
from intelligence.enhanced_linkedin_analyzer import EnhancedLinkedInAnalyzer

def print_banner():
    """Print the CLI banner"""
    print("\\n" + "="*60)
    print("🚀 ENHANCED LINKEDIN INTELLIGENCE ANALYZER")
    print("="*60)
    print("Real Data Collection + Advanced Analytics")
    print("Combining LinkedIn profile data with network insights")
    print("="*60)

async def run_enhanced_analysis(force_refresh: bool = False, debug: bool = False):
    """Run the enhanced LinkedIn analysis"""
    
    try:
        print("\\n🔧 Initializing Enhanced Analyzer...")
        analyzer = EnhancedLinkedInAnalyzer(debug=debug, force_refresh=force_refresh)
        
        # Display cache information
        cache_info = analyzer.get_cache_info()
        print(f"\\n📊 Cache Status: {cache_info.get('status', 'unknown')}")
        
        if cache_info.get('age_hours') is not None:
            print(f"🕒 Cache Age: {cache_info['age_hours']:.1f} hours")
            print(f"💾 Data Fresh: {analyzer.is_data_fresh()}")
        
        if force_refresh:
            print("🔄 Force refresh enabled - collecting fresh data")
        
        print("\\n🚀 Starting Enhanced Network Analysis...")
        print("This combines real LinkedIn data with advanced analytics")
        print("Please wait while we analyze your network...")
        
        # Run the enhanced analysis
        results = await analyzer.analyze_enhanced_network()
        
        # Display comprehensive results
        print("\\n" + "="*50)
        print("📈 ENHANCED ANALYSIS RESULTS")
        print("="*50)
        
        real_data = results.get('real_data', {})
        combined = results.get('combined_metrics', {})
        analytics = results.get('enhanced_analytics', {})
        
        # Real LinkedIn Data Section
        print("\\n🔗 REAL LINKEDIN DATA:")
        print("-" * 25)
        print(f"  Total Connections: {real_data.get('total_connections', 'N/A')}")
        print(f"  Leadership Engagement: {real_data.get('leadership_engagement', 'N/A')}")
        print(f"  F500 Penetration: {real_data.get('f500_penetration', 'N/A')}")
        print(f"  Profile Name: {real_data.get('profile_name', 'N/A')}")
        print(f"  Data Source: {real_data.get('data_source', 'N/A')}")
        
        # Enhanced Analytics Section
        print("\\n📊 ENHANCED ANALYTICS:")
        print("-" * 25)
        print(f"  Unique Companies: {combined.get('unique_companies', 'N/A')}")
        print(f"  Unique Locations: {combined.get('unique_locations', 'N/A')}")
        print(f"  Unique Roles: {combined.get('unique_roles', 'N/A')}")
        print(f"  Avg Connection Strength: {combined.get('average_connection_strength', 0):.2f}/3.0")
        
        # Top Companies
        if analytics.get('top_companies'):
            print("\\n🏢 TOP COMPANIES:")
            print("-" * 15)
            for i, (company, count) in enumerate(analytics['top_companies'][:5], 1):
                print(f"  {i}. {company}: {count} connections")
        
        # Top Locations
        if analytics.get('top_locations'):
            print("\\n📍 TOP LOCATIONS:")
            print("-" * 15)
            for i, (location, count) in enumerate(analytics['top_locations'][:5], 1):
                print(f"  {i}. {location}: {count} connections")
        
        # Top Roles
        if analytics.get('top_roles'):
            print("\\n💼 TOP ROLES:")
            print("-" * 12)
            for i, (role, count) in enumerate(analytics['top_roles'][:5], 1):
                print(f"  {i}. {role}: {count} connections")
        
        # Connection Strength Analysis
        metrics = analytics.get('metrics', {})
        if metrics.get('average_connection_strength'):
            strength = metrics['average_connection_strength']
            strength_level = "Strong" if strength > 2.5 else "Good" if strength > 2.0 else "Average"
            print(f"\\n💪 CONNECTION STRENGTH: {strength:.2f}/3.0 ({strength_level})")
        
        # Export Information
        print("\\n" + "="*50)
        print("📁 EXPORTED FILES:")
        print("="*50)
        
        # Find the latest output directory
        output_dirs = list(Path('output').glob('enhanced_analysis_*'))
        if output_dirs:
            latest_dir = max(output_dirs, key=lambda x: x.stat().st_mtime)
            print(f"\\n📂 Results Directory: {latest_dir}")
            
            exported_files = list(latest_dir.glob('*.csv')) + list(latest_dir.glob('*.json'))
            for file in exported_files:
                print(f"  📄 {file.name}")
        
        print("\\n" + "="*50)
        print("✅ ENHANCED ANALYSIS COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("\\n🎯 Key Benefits:")
        print("  • Real LinkedIn data (not mock/fake)")
        print("  • Advanced company/role extraction")
        print("  • Connection strength scoring")
        print("  • Comprehensive CSV exports")
        print("  • Network pattern analysis")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ Error: {str(e)}")
        if debug:
            import traceback
            traceback.print_exc()
        return False

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Enhanced Job Search Intelligence Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/enhanced_linkedin_cli.py                    # Run with cached data
  python scripts/enhanced_linkedin_cli.py --force-refresh   # Force fresh data collection
  python scripts/enhanced_linkedin_cli.py --debug           # Enable debug logging
        """
    )
    
    parser.add_argument(
        '--force-refresh', 
        action='store_true',
        help='Force refresh of cached LinkedIn data'
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Run the analysis
    success = asyncio.run(run_enhanced_analysis(
        force_refresh=args.force_refresh,
        debug=args.debug
    ))
    
    if success:
        print("\\n🎉 Thank you for using Enhanced Job Search Intelligence!")
        print("💡 Tip: Results are saved as CSV files for further analysis")
    else:
        print("\\n💔 Analysis failed. Please check the error messages above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())