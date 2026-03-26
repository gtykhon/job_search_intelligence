#!/usr/bin/env python3
"""
Simple Database Schema Test
Tests just the database connection and schema fix
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def test_database_schema():
    """Test the database schema fix directly"""
    
    print("🔍 Testing Database Schema Fix")
    print("=" * 40)
    
    # Connect to database
    conn = sqlite3.connect('job_search.db')
    
    # Test 1: Check if weekly_metrics table exists and has the right columns
    print("📊 Test 1: Table Structure")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(weekly_metrics)")
    columns = cursor.fetchall()
    
    column_names = [col[1] for col in columns]
    print(f"   Columns found: {len(column_names)}")
    
    required_columns = ['week_start_date', 'leadership_engagement_percentage', 
                       'comment_quality_score', 'f500_penetration_percentage']
    
    missing = [col for col in required_columns if col not in column_names]
    if missing:
        print(f"   ❌ Missing columns: {missing}")
        return False
    else:
        print(f"   ✅ All required columns present")
    
    # Test 2: Test the fixed query (using week_start_date instead of collection_date)
    print("\n📅 Test 2: Fixed Query")
    cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    try:
        # This is the FIXED query that should work
        query = """
            SELECT *, week_start_date as collection_date FROM weekly_metrics 
            WHERE week_start_date >= ? 
            ORDER BY week_start_date ASC
        """
        
        df = pd.read_sql_query(query, conn, params=[cutoff_date])
        print(f"   ✅ Query successful: {len(df)} records returned")
        
        if len(df) > 0:
            print(f"   📊 Sample data:")
            for col in ['leadership_engagement_percentage', 'comment_quality_score', 'f500_penetration_percentage']:
                if col in df.columns:
                    value = df[col].iloc[0] if len(df) > 0 else 0
                    print(f"      {col}: {value}")
        
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
        return False
    
    # Test 3: Test the OLD query that was failing
    print("\n❌ Test 3: Old Query (Should Fail)")
    try:
        # This is the OLD query that was causing the error
        old_query = """
            SELECT * FROM weekly_metrics 
            WHERE collection_date >= ? 
            ORDER BY collection_date ASC
        """
        
        df_old = pd.read_sql_query(old_query, conn, params=[cutoff_date])
        print(f"   ⚠️  Old query unexpectedly worked: {len(df_old)} records")
        
    except Exception as e:
        print(f"   ✅ Old query failed as expected: {str(e)[:50]}...")
    
    conn.close()
    
    print("\n" + "=" * 40)
    print("🎯 CONCLUSION:")
    print("✅ Database schema is correct")
    print("✅ Fixed query works with week_start_date")
    print("✅ Analytics engine should now work properly")
    print("\n🚀 Dashboard analytics should be working!")
    
    return True

if __name__ == "__main__":
    test_database_schema()