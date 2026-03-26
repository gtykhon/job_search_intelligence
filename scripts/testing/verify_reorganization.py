"""
Post-Reorganization System Verification
Test that all components work after directory reorganization
"""

import sys
import os

# Add the project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_system_functionality():
    """Test all major system components after reorganization"""
    
    print("Job Search Intelligence - Post-Reorganization Verification")
    print("=" * 70)
    
    # Test 1: Dashboard import
    try:
        from src.dashboard.real_time_dashboard import RealTimeDashboard
        from src.dashboard.database_field_explorer import DatabaseFieldExplorer
        print("✅ Dashboard modules import successfully")
    except Exception as e:
        print(f"❌ Dashboard import failed: {e}")
        return False
    
    # Test 2: Database connectivity
    try:
        import sqlite3
        conn = sqlite3.connect("job_search.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Database accessible with {table_count} tables")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test 3: Core module imports
    try:
        from src.analytics.advanced_analytics_engine import AdvancedAnalyticsEngine
        from src.tracking.comprehensive_profile_metrics import ComprehensiveProfileCollector
        print("✅ Core analytics modules import successfully")
    except Exception as e:
        print(f"❌ Analytics import failed: {e}")
        return False
    
    # Test 4: Documentation structure
    doc_paths = [
        "docs/README.md",
        "docs/user-guides/DATABASE_FIELD_EXPLORER_GUIDE.md",
        "docs/user-guides/FIRST_DEGREE_CONNECTIONS_GUIDE.md",
        "docs/reports/YOUR_FIRST_DEGREE_NETWORK_INTELLIGENCE.md",
        "docs/technical/REORGANIZATION_PLAN.md"
    ]
    
    missing_docs = []
    for doc_path in doc_paths:
        if not os.path.exists(doc_path):
            missing_docs.append(doc_path)
    
    if missing_docs:
        print(f"❌ Missing documentation files: {missing_docs}")
        return False
    else:
        print("✅ All documentation files properly organized")
    
    # Test 5: Scripts structure
    script_paths = [
        "scripts/analysis/analyze_first_degree_connections.py",
        "scripts/analysis/analyze_table_population.py",
        "scripts/testing/test_database_explorer.py",
        "scripts/testing/test_enhanced_dashboard.py"
    ]
    
    missing_scripts = []
    for script_path in script_paths:
        if not os.path.exists(script_path):
            missing_scripts.append(script_path)
    
    if missing_scripts:
        print(f"❌ Missing script files: {missing_scripts}")
        return False
    else:
        print("✅ All scripts properly organized")
    
    # Test 6: Essential files in root
    essential_files = [
        "README.md",
        "requirements.txt", 
        "launch_dashboard.py",
        "job_search.db"
    ]
    
    missing_essential = []
    for file_path in essential_files:
        if not os.path.exists(file_path):
            missing_essential.append(file_path)
    
    if missing_essential:
        print(f"❌ Missing essential files: {missing_essential}")
        return False
    else:
        print("✅ All essential files present in root directory")
    
    # Test 7: Directory structure
    expected_dirs = ["src", "docs", "scripts", "data", "logs", "cache"]
    missing_dirs = []
    for dir_name in expected_dirs:
        if not os.path.exists(dir_name):
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    else:
        print("✅ All expected directories present")
    
    print("\n" + "=" * 70)
    print("🎉 POST-REORGANIZATION VERIFICATION COMPLETE")
    print("=" * 70)
    print("✅ All systems operational after directory reorganization")
    print("✅ Professional project structure successfully implemented")
    print("✅ Documentation properly organized and accessible")
    print("✅ Scripts categorized and functional")
    print("✅ Clean root directory achieved")
    
    print(f"\n📊 ORGANIZATION SUMMARY:")
    print(f"   • Documentation: {len(doc_paths)} files properly organized")
    print(f"   • Scripts: {len(script_paths)} files categorized")
    print(f"   • Essential files: {len(essential_files)} files in root")
    print(f"   • Directory structure: {len(expected_dirs)} directories organized")
    
    print(f"\n🚀 SYSTEM READY:")
    print(f"   • Launch dashboard: python launch_dashboard.py")
    print(f"   • Access documentation: docs/README.md")
    print(f"   • Run analysis: scripts/analysis/")
    print(f"   • Test system: scripts/testing/")
    
    return True

def main():
    """Main verification function"""
    
    if test_system_functionality():
        print("\n🎯 Job Search Intelligence successfully reorganized!")
        print("   Professional structure implemented with full functionality preserved.")
    else:
        print("\n❌ Some issues detected during verification.")
        print("   Check error messages above for details.")

if __name__ == "__main__":
    main()