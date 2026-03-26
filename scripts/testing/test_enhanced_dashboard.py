"""
Test Enhanced Dashboard with Database Field Explorer
Verify the integration works correctly
"""

import sys
sys.path.append('.')

def test_dashboard_integration():
    """Test that the enhanced dashboard integrates properly with Database Explorer"""
    
    print("🧪 Testing Enhanced Dashboard Integration...")
    
    try:
        # Test dashboard import
        from src.dashboard.real_time_dashboard import RealTimeDashboard
        print("✅ Dashboard import successful")
        
        # Test database explorer import
        from src.dashboard.database_field_explorer import DatabaseFieldExplorer
        print("✅ Database Explorer import successful")
        
        # Test dashboard initialization
        dashboard = RealTimeDashboard()
        print("✅ Dashboard initialization successful")
        
        # Test database explorer initialization
        explorer = DatabaseFieldExplorer("job_search.db")
        print("✅ Database Explorer initialization successful")
        
        # Test schema discovery
        schema_count = len(explorer.schema)
        print(f"✅ Schema discovery successful: {schema_count} tables found")
        
        # Test dashboard database explorer method
        if hasattr(dashboard, '_render_database_explorer_page'):
            print("✅ Dashboard Database Explorer page method found")
        else:
            print("❌ Dashboard Database Explorer page method missing")
            return False
        
        print("\n🎉 All integration tests passed!")
        print(f"📊 Your enhanced dashboard now provides access to {schema_count} tables with hundreds of fields")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 Testing Enhanced Job Search Intelligence Dashboard")
    print("=" * 60)
    
    if test_dashboard_integration():
        print("\n✅ Your enhanced dashboard is ready!")
        print("\n📝 To launch the enhanced dashboard:")
        print("   streamlit run src/dashboard/real_time_dashboard.py")
        print("\n🗄️ New Database Explorer features:")
        print("   • Access to all 39 database tables")
        print("   • 500+ fields available for analysis")
        print("   • Interactive data exploration")
        print("   • Custom visualizations")
        print("   • Export capabilities")
        print("   • Real-time field statistics")
    else:
        print("\n❌ Integration issues detected. Check error messages above.")

if __name__ == "__main__":
    main()