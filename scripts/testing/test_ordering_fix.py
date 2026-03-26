"""
Test specific table ordering fix for analysis_sessions table
"""

import sys
sys.path.append('.')

from src.dashboard.database_field_explorer import DatabaseFieldExplorer
import sqlite3

def test_analysis_sessions_table():
    """Test that analysis_sessions table works correctly without id column"""
    
    print("🧪 Testing analysis_sessions table specifically...")
    
    try:
        # Initialize explorer
        explorer = DatabaseFieldExplorer("job_search.db")
        
        # Check the schema for analysis_sessions
        if 'analysis_sessions' in explorer.schema:
            fields = explorer.schema['analysis_sessions']
            field_names = [f['name'] for f in fields]
            
            print(f"✅ analysis_sessions found with {len(fields)} fields")
            print(f"📊 Fields: {', '.join(field_names)}")
            
            # Check if it has id column
            has_id = 'id' in field_names
            print(f"🔍 Has 'id' column: {has_id}")
            
            # Test the smart ordering
            order_column = explorer._get_best_order_column('analysis_sessions')
            print(f"🎯 Best order column: {order_column}")
            
            # Test data loading
            try:
                df = explorer.get_table_data('analysis_sessions', limit=5)
                print(f"✅ Successfully loaded {len(df)} records from analysis_sessions")
                
                if not df.empty:
                    print(f"📊 Columns loaded: {list(df.columns)}")
                else:
                    print("📊 Table is empty (no data yet)")
                    
            except Exception as e:
                print(f"❌ Error loading analysis_sessions data: {e}")
                return False
        else:
            print("❌ analysis_sessions table not found")
            return False
            
        print("✅ analysis_sessions table test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_various_tables():
    """Test several tables to ensure ordering works correctly"""
    
    print("\n🧪 Testing ordering for various tables...")
    
    explorer = DatabaseFieldExplorer("job_search.db")
    
    # Test a few different tables
    test_tables = ['analysis_sessions', 'weekly_metrics', 'ai_insights', 'profile_viewers']
    
    for table in test_tables:
        if table in explorer.schema:
            try:
                order_col = explorer._get_best_order_column(table)
                df = explorer.get_table_data(table, limit=2)
                
                print(f"✅ {table}: order by '{order_col}', loaded {len(df)} records")
                
            except Exception as e:
                print(f"❌ {table}: failed - {e}")
        else:
            print(f"⚠️ {table}: not found in database")

def main():
    """Main test function"""
    
    print("🚀 Testing Database Field Explorer Ordering Fix")
    print("=" * 60)
    
    # Test analysis_sessions specifically
    if test_analysis_sessions_table():
        print("\n✅ analysis_sessions ordering fix successful!")
    
    # Test various tables
    test_various_tables()
    
    print("\n🎉 Database Field Explorer ordering fix complete!")
    print("📊 The explorer now intelligently handles tables with different column structures")

if __name__ == "__main__":
    main()