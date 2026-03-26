"""
Database Table Population Analysis
Check which tables have data and which are empty
"""

import sys
sys.path.append('.')

import sqlite3
import pandas as pd
from src.dashboard.database_field_explorer import DatabaseFieldExplorer

def analyze_table_population():
    """Analyze which tables have data and which are empty"""
    
    print("Analyzing Table Population in Job Search Intelligence Database")
    print("=" * 70)
    
    try:
        # Initialize explorer and database connection
        explorer = DatabaseFieldExplorer("job_search.db")
        conn = sqlite3.connect("job_search.db")
        cursor = conn.cursor()
        
        tables_with_data = []
        empty_tables = []
        table_stats = []
        
        print(f"📊 Checking {len(explorer.schema)} tables...\n")
        
        for table_name in explorer.schema.keys():
            try:
                # Count records in each table
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                record_count = cursor.fetchone()[0]
                
                # Get field count
                field_count = len(explorer.schema[table_name])
                
                table_info = {
                    'table': table_name,
                    'records': record_count,
                    'fields': field_count,
                    'status': 'Has Data' if record_count > 0 else 'Empty'
                }
                
                table_stats.append(table_info)
                
                if record_count > 0:
                    tables_with_data.append((table_name, record_count, field_count))
                    status_icon = "✅"
                    status_text = f"{record_count} records"
                else:
                    empty_tables.append((table_name, field_count))
                    status_icon = "❌"
                    status_text = "Empty"
                
                print(f"{status_icon} {table_name:<30} {status_text:<15} ({field_count} fields)")
                
            except Exception as e:
                print(f"⚠️ {table_name:<30} Error: {e}")
        
        conn.close()
        
        # Summary statistics
        print("\n" + "=" * 70)
        print("📈 SUMMARY STATISTICS")
        print("=" * 70)
        
        total_tables = len(explorer.schema)
        tables_with_data_count = len(tables_with_data)
        empty_tables_count = len(empty_tables)
        
        print(f"📊 Total Tables: {total_tables}")
        print(f"✅ Tables with Data: {tables_with_data_count}")
        print(f"❌ Empty Tables: {empty_tables_count}")
        print(f"📈 Population Rate: {(tables_with_data_count/total_tables)*100:.1f}%")
        
        # Show tables with data
        if tables_with_data:
            print(f"\n✅ TABLES WITH DATA ({len(tables_with_data)} tables):")
            print("-" * 50)
            total_records = 0
            for table, records, fields in sorted(tables_with_data, key=lambda x: x[1], reverse=True):
                total_records += records
                print(f"• {table:<30} {records:>6} records ({fields} fields)")
            print(f"\n📊 Total Records Across All Tables: {total_records:,}")
        
        # Show empty tables
        if empty_tables:
            print(f"\n❌ EMPTY TABLES ({len(empty_tables)} tables):")
            print("-" * 50)
            for table, fields in sorted(empty_tables):
                print(f"• {table:<30} (0 records, {fields} fields)")
        
        # Identify core vs auxiliary tables
        print(f"\n🎯 TABLE CATEGORIZATION:")
        print("-" * 50)
        
        core_tables_with_data = []
        core_tables_empty = []
        
        # Define core tables that should have data for basic functionality
        core_table_patterns = [
            'weekly_metrics', 'profile_metrics', 'network_connections', 
            'post_performance', 'analysis_sessions', 'comprehensive_profile_metrics'
        ]
        
        for table, records, fields in tables_with_data:
            if any(pattern in table for pattern in core_table_patterns):
                core_tables_with_data.append(table)
        
        for table, fields in empty_tables:
            if any(pattern in table for pattern in core_table_patterns):
                core_tables_empty.append(table)
        
        if core_tables_with_data:
            print("✅ Core Tables with Data:")
            for table in core_tables_with_data:
                print(f"   • {table}")
        
        if core_tables_empty:
            print("⚠️ Core Tables that are Empty:")
            for table in core_tables_empty:
                print(f"   • {table}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        print("-" * 50)
        
        if empty_tables_count > tables_with_data_count:
            print("📊 Most tables are empty - this is normal for a new system")
            print("🚀 Focus on populating core tables first:")
            print("   • weekly_metrics (main performance data)")
            print("   • network_connections (LinkedIn connections)")
            print("   • post_performance (content analysis)")
        
        if 'weekly_metrics' in [t[0] for t in tables_with_data]:
            print("✅ weekly_metrics has data - core functionality available")
        else:
            print("⚠️ weekly_metrics is empty - run data collection to populate")
        
        return table_stats
        
    except Exception as e:
        print(f"❌ Error analyzing table population: {e}")
        return []

def show_sample_data_from_populated_tables():
    """Show sample data from tables that have data"""
    
    print(f"\n🔍 SAMPLE DATA FROM POPULATED TABLES:")
    print("=" * 70)
    
    try:
        explorer = DatabaseFieldExplorer("job_search.db")
        conn = sqlite3.connect("job_search.db")
        
        # Check a few key tables for sample data
        key_tables = ['weekly_metrics', 'analysis_sessions', 'network_connections', 'post_performance']
        
        for table in key_tables:
            if table in explorer.schema:
                try:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        print(f"\n📊 {table.upper()} ({count} records):")
                        print("-" * 40)
                        
                        # Get sample data
                        df = explorer.get_table_data(table, limit=3)
                        if not df.empty:
                            # Show first few columns and rows
                            display_cols = list(df.columns)[:5]  # First 5 columns
                            print(f"Columns: {', '.join(display_cols)}")
                            print(df[display_cols].head(2).to_string(index=False))
                        else:
                            print("No data retrieved")
                    else:
                        print(f"\n❌ {table.upper()}: Empty")
                        
                except Exception as e:
                    print(f"⚠️ Error checking {table}: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing sample data: {e}")

def main():
    """Main analysis function"""
    
    table_stats = analyze_table_population()
    
    if table_stats:
        show_sample_data_from_populated_tables()
        
        print(f"\n🎯 NEXT STEPS:")
        print("-" * 30)
        print("1. 📊 Use Database Explorer to examine populated tables")
        print("2. 🚀 Run data collection to populate empty tables")
        print("3. 📈 Focus analysis on tables with actual data")
        print("4. 🔍 Export data from populated tables for deeper analysis")

if __name__ == "__main__":
    main()