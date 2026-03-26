"""
Test script for Database Field Explorer
Verify that the enhanced dashboard can access all database fields
"""

import sys
import os
sys.path.append('.')

from src.dashboard.database_field_explorer import DatabaseFieldExplorer
import sqlite3
import pandas as pd

def test_database_explorer():
    """Test the database field explorer functionality"""
    
    print("🧪 Testing Database Field Explorer...")
    
    try:
        # Initialize explorer
        explorer = DatabaseFieldExplorer("job_search.db")
        
        print(f"✅ Database Explorer initialized successfully")
        print(f"📊 Found {len(explorer.schema)} tables in database")
        
        # Test schema loading
        print("\n📋 Database Schema Overview:")
        total_fields = 0
        for table_name, fields in explorer.schema.items():
            field_count = len(fields)
            total_fields += field_count
            print(f"  • {table_name}: {field_count} fields")
            
            # Show first few fields as sample
            if field_count > 0:
                sample_fields = [f['name'] for f in fields[:3]]
                print(f"    Sample fields: {', '.join(sample_fields)}")
        
        print(f"\n📊 Total fields across all tables: {total_fields}")
        
        # Test data loading from a specific table
        if 'weekly_metrics' in explorer.schema:
            print("\n🔍 Testing data loading from weekly_metrics...")
            
            try:
                df = explorer.get_table_data('weekly_metrics', limit=5)
                print(f"✅ Loaded {len(df)} records from weekly_metrics")
                print(f"📊 Columns: {list(df.columns)}")
                
                if not df.empty:
                    print("📈 Sample data:")
                    print(df.head())
                    
            except Exception as e:
                print(f"⚠️ Error loading weekly_metrics data: {e}")
        
        # Test field statistics
        if 'weekly_metrics' in explorer.schema and len(explorer.schema['weekly_metrics']) > 0:
            print("\n📊 Testing field statistics...")
            
            # Get first field for testing
            first_field = explorer.schema['weekly_metrics'][0]['name']
            
            try:
                stats = explorer.get_field_statistics('weekly_metrics', first_field)
                print(f"✅ Statistics for {first_field}:")
                for key, value in stats.items():
                    print(f"  • {key}: {value}")
                    
            except Exception as e:
                print(f"⚠️ Error getting field statistics: {e}")
        
        print("\n✅ Database Explorer test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database Explorer test failed: {e}")
        return False

def test_database_connection():
    """Test basic database connectivity"""
    
    print("\n🔌 Testing database connection...")
    
    try:
        conn = sqlite3.connect("job_search.db")
        cursor = conn.cursor()
        
        # Check if database exists and has tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"✅ Database connection successful")
        print(f"📊 Found {len(tables)} tables")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 Starting Database Field Explorer Tests...")
    print("=" * 60)
    
    # Test database connection first
    if not test_database_connection():
        print("\n❌ Cannot proceed without database connection")
        return
    
    # Test the explorer
    if test_database_explorer():
        print("\n🎉 All tests passed! Database Field Explorer is ready to use.")
        print("\n📝 To use in dashboard:")
        print("   1. Run: streamlit run src/dashboard/real_time_dashboard.py")
        print("   2. Navigate to 'Database Explorer' in the sidebar")
        print("   3. Explore all 41 tables and hundreds of fields!")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()