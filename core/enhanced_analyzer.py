"""
Integration script to enhance LinkedIn analyzer with organized output management
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.output_manager import OutputManager
import json
from datetime import datetime
import asyncio

class EnhancedLinkedInAnalyzer:
    """
    Enhanced version of LinkedIn analyzer with organized output management
    """
    
    def __init__(self):
        self.output_manager = OutputManager()
        
    async def run_enhanced_ai_analysis(self, profile_id: str = "default"):
        """Run AI analysis with enhanced output management"""
        
        print("🚀 Starting Enhanced LinkedIn AI Analysis...")
        
        # Start analysis session
        session_id = self.output_manager.start_session("ai_insights", profile_id)
        print(f"📋 Session ID: {session_id}")
        
        try:
            # Import and run existing AI insights test
            from test_ai_insights import test_claude_insights
            
            print("🤖 Running Claude AI Analysis...")
            start_time = datetime.now()
            
            # Run the analysis
            result = await test_claude_insights()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result and "analysis" in result:
                # Save results using enhanced output manager
                file_path = self.output_manager.save_analysis_results(
                    analysis_type="ai_insights",
                    data={
                        "claude_analysis": result["analysis"],
                        "performance": {
                            "duration_seconds": duration,
                            "timestamp": end_time.isoformat(),
                            "model_used": result.get("model", "claude-3-5-sonnet-20241022")
                        },
                        "metadata": {
                            "confidence_score": result.get("confidence_score", 0.9),
                            "recommendations_count": len(result["analysis"].get("recommendations", [])),
                            "insights_count": len(result["analysis"].get("insights", []))
                        }
                    },
                    profile_id=profile_id,
                    save_to_db=True
                )
                
                print(f"✅ Analysis completed in {duration:.2f}s")
                print(f"📁 Results saved to: {file_path}")
                
                # Generate daily report
                report_path = self.output_manager.generate_daily_report()
                print(f"📊 Daily report: {report_path}")
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "file_path": file_path,
                    "duration": duration,
                    "analysis": result["analysis"]
                }
            else:
                print("❌ AI analysis failed")
                return {"success": False, "error": "Analysis failed"}
                
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_network_analysis(self, profile_id: str = "default"):
        """Run network analysis with enhanced output"""
        
        session_id = self.output_manager.start_session("network_analysis", profile_id)
        print(f"🌐 Starting Network Analysis - Session: {session_id}")
        
        try:
            # Simulate network analysis (replace with actual network analysis code)
            network_data = {
                "total_connections": 500,
                "industry_breakdown": {
                    "Technology": 45,
                    "Finance": 25,
                    "Healthcare": 15,
                    "Education": 10,
                    "Other": 5
                },
                "geographic_distribution": {
                    "United States": 60,
                    "United Kingdom": 15,
                    "Canada": 10,
                    "Germany": 8,
                    "Other": 7
                },
                "connection_strength": {
                    "strong": 25,
                    "medium": 45,
                    "weak": 30
                },
                "growth_metrics": {
                    "monthly_growth_rate": 2.5,
                    "quality_score": 8.3,
                    "engagement_rate": 15.7
                }
            }
            
            # Save with enhanced manager
            file_path = self.output_manager.save_analysis_results(
                analysis_type="network_analysis",
                data=network_data,
                profile_id=profile_id,
                save_to_db=True
            )
            
            # Export as CSV
            csv_path = self.output_manager.save_export(
                data=network_data["industry_breakdown"],
                filename="industry_breakdown",
                format_type="csv"
            )
            
            print(f"✅ Network analysis completed")
            print(f"📁 JSON results: {file_path}")
            print(f"📊 CSV export: {csv_path}")
            
            return {
                "success": True,
                "session_id": session_id,
                "file_path": file_path,
                "csv_path": csv_path,
                "data": network_data
            }
            
        except Exception as e:
            print(f"❌ Network analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_analysis_history(self, days: int = 7):
        """Get recent analysis history"""
        history = self.output_manager.get_analysis_history(days=days)
        
        print(f"\n📈 Analysis History (Last {days} days):")
        print(f"{'Type':<15} {'Profile':<10} {'Date':<20} {'Status':<10}")
        print("-" * 60)
        
        for record in history:
            print(f"{record['analysis_type']:<15} {record['profile_id']:<10} {record['timestamp'][:19]:<20} {record['status']:<10}")
        
        return history
    
    def cleanup_old_files(self, days_to_keep: int = 30):
        """Clean up old files"""
        moved_count = self.output_manager.cleanup_old_files(days_to_keep)
        print(f"🧹 Moved {moved_count} old files to archive")
        return moved_count

async def main():
    """Main execution function"""
    
    analyzer = EnhancedLinkedInAnalyzer()
    
    print("🔧 Job Search Intelligence - Enhanced Output Management")
    print("=" * 60)
    
    # Menu
    while True:
        print("\n📋 Available Actions:")
        print("1. Run AI Analysis (Claude)")
        print("2. Run Network Analysis")
        print("3. View Analysis History")
        print("4. Generate Daily Report")
        print("5. Cleanup Old Files")
        print("6. Exit")
        
        choice = input("\n🎯 Select action (1-6): ").strip()
        
        if choice == "1":
            profile_id = input("Enter profile ID (default: 'default'): ").strip() or "default"
            result = await analyzer.run_enhanced_ai_analysis(profile_id)
            if result["success"]:
                print(f"\n🎉 AI Analysis Summary:")
                print(f"Duration: {result['duration']:.2f}s")
                print(f"File: {result['file_path']}")
        
        elif choice == "2":
            profile_id = input("Enter profile ID (default: 'default'): ").strip() or "default"
            result = await analyzer.run_network_analysis(profile_id)
            if result["success"]:
                print(f"\n🎉 Network Analysis Summary:")
                print(f"Total Connections: {result['data']['total_connections']}")
                print(f"Files: {result['file_path']}")
        
        elif choice == "3":
            days = input("Days of history (default: 7): ").strip()
            days = int(days) if days.isdigit() else 7
            analyzer.get_analysis_history(days)
        
        elif choice == "4":
            report_path = analyzer.output_manager.generate_daily_report()
            print(f"📊 Daily report generated: {report_path}")
        
        elif choice == "5":
            days = input("Keep files newer than X days (default: 30): ").strip()
            days = int(days) if days.isdigit() else 30
            analyzer.cleanup_old_files(days)
        
        elif choice == "6":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-6.")

if __name__ == "__main__":
    asyncio.run(main())
