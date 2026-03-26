"""
First-Degree Connection Analysis for Job Search Intelligence
Analyze your current first-degree connections data
"""

import sys
sys.path.append('.')

import sqlite3
import pandas as pd
from collections import Counter

def analyze_first_degree_connections():
    """Analyze first-degree connections in the network_connections table"""
    
    print("🤝 First-Degree Connection Analysis")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect("job_search.db")
        
        # Get all first-degree connections data
        query = """
            SELECT 
                connection_name,
                connection_title, 
                connection_company,
                connection_location,
                relationship_type,
                mutual_connections,
                connection_strength,
                timestamp,
                created_at
            FROM network_connections
            ORDER BY created_at DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("❌ No first-degree connections found in database")
            return
        
        total_connections = len(df)
        print(f"📊 Total First-Degree Connections: {total_connections}")
        
        # Company analysis
        print(f"\n🏢 COMPANY DISTRIBUTION:")
        print("-" * 30)
        company_counts = df['connection_company'].value_counts()
        for company, count in company_counts.head(10).items():
            if pd.notna(company):
                percentage = (count / total_connections) * 100
                print(f"• {company:<25} {count:>2} ({percentage:.1f}%)")
        
        # Industry analysis - skip since column doesn't exist
        print(f"\n🏭 RELATIONSHIP TYPE DISTRIBUTION:")
        print("-" * 30)
        if 'relationship_type' in df.columns:
            relationship_counts = df['relationship_type'].value_counts()
            for rel_type, count in relationship_counts.items():
                if pd.notna(rel_type):
                    percentage = (count / total_connections) * 100
                    print(f"• {rel_type:<25} {count:>2} ({percentage:.1f}%)")
        else:
            print("Relationship type data not available")
        # Title/Seniority analysis
        print(f"\n👔 TITLE ANALYSIS:")
        print("-" * 30)
        
        # Identify leadership titles
        leadership_keywords = ['director', 'vp', 'vice president', 'ceo', 'cto', 'cfo', 
                              'head of', 'chief', 'president', 'founder']
        
        senior_titles = []
        regular_titles = []
        
        for title in df['connection_title']:
            if pd.notna(title):
                title_lower = title.lower()
                if any(keyword in title_lower for keyword in leadership_keywords):
                    senior_titles.append(title)
                else:
                    regular_titles.append(title)
        
        print(f"👑 Leadership/Senior Titles: {len(senior_titles)} ({len(senior_titles)/total_connections*100:.1f}%)")
        for title in senior_titles[:5]:
            print(f"   • {title}")
        
        print(f"\n🧑‍💼 Regular Titles: {len(regular_titles)} ({len(regular_titles)/total_connections*100:.1f}%)")
        for title in regular_titles[:5]:
            print(f"   • {title}")
        
        # Geographic analysis
        print(f"\n🌍 GEOGRAPHIC DISTRIBUTION:")
        print("-" * 30)
        if 'connection_location' in df.columns:
            location_counts = df['connection_location'].value_counts()
            for location, count in location_counts.head(5).items():
                if pd.notna(location):
                    percentage = (count / total_connections) * 100
                    print(f"• {location:<25} {count:>2} ({percentage:.1f}%)")
        else:
            print("Location data not available")
        # Connection strength analysis
        print(f"\n💪 CONNECTION STRENGTH ANALYSIS:")
        print("-" * 30)
        if 'connection_strength' in df.columns and df['connection_strength'].notna().any():
            avg_strength = df['connection_strength'].mean()
            max_strength = df['connection_strength'].max()
            min_strength = df['connection_strength'].min()
            
            print(f"Average Strength: {avg_strength:.2f}")
            print(f"Strongest Connection: {max_strength:.2f}")
            print(f"Weakest Connection: {min_strength:.2f}")
        else:
            print("Connection strength data not available")
        
        # Fortune 500 analysis
        print(f"\n🏆 FORTUNE 500 ANALYSIS:")
        print("-" * 30)
        
        # Get Fortune 500 companies from database
        try:
            conn = sqlite3.connect("job_search.db")
            f500_query = "SELECT company_name FROM fortune_500_companies"
            f500_df = pd.read_sql_query(f500_query, conn)
            f500_companies = set(f500_df['company_name'].str.lower())
            conn.close()
            
            f500_connections = 0
            f500_matches = []
            
            for company in df['connection_company']:
                if pd.notna(company):
                    if company.lower() in f500_companies:
                        f500_connections += 1
                        f500_matches.append(company)
            
            f500_percentage = (f500_connections / total_connections) * 100
            print(f"Fortune 500 Connections: {f500_connections} ({f500_percentage:.1f}%)")
            
            if f500_matches:
                print("F500 Companies in network:")
                for company in set(f500_matches):
                    print(f"   • {company}")
                    
        except Exception as e:
            print(f"Could not analyze Fortune 500 data: {e}")
        
        # Network growth potential
        print(f"\n📈 NETWORK GROWTH ANALYSIS:")
        print("-" * 30)
        max_connections = 30000  # LinkedIn limit
        current_percentage = (total_connections / max_connections) * 100
        remaining_capacity = max_connections - total_connections
        
        print(f"Current Network Size: {total_connections:,} / {max_connections:,}")
        print(f"Network Utilization: {current_percentage:.3f}%")
        print(f"Remaining Capacity: {remaining_capacity:,} connections")
        print(f"Growth Potential: {'🚀 Enormous' if current_percentage < 1 else '📊 Significant'}")
        
        # Sample connections detail
        print(f"\n🔍 SAMPLE CONNECTIONS:")
        print("-" * 30)
        sample_connections = df.head(5)
        for _, connection in sample_connections.iterrows():
            name = connection['connection_name'] if pd.notna(connection['connection_name']) else 'Unknown'
            title = connection['connection_title'] if pd.notna(connection['connection_title']) else 'Unknown Title'
            company = connection['connection_company'] if pd.notna(connection['connection_company']) else 'Unknown Company'
            print(f"• {name}")
            print(f"  {title} @ {company}")
        
        # Strategic recommendations
        print(f"\n💡 STRATEGIC RECOMMENDATIONS:")
        print("-" * 30)
        
        if total_connections < 50:
            print("🎯 Focus on Quality Growth:")
            print("   • Target 2-3 new connections per week")
            print("   • Prioritize industry leaders and decision makers")
            print("   • Expand Fortune 500 company representation")
        
        if len(senior_titles) / total_connections < 0.3:
            print("👑 Increase Senior-Level Connections:")
            print("   • Target Directors, VPs, and C-level executives")
            print("   • Focus on thought leaders in your industry")
        
        if len(set(df['connection_company'])) < total_connections * 0.8:
            print("🏢 Diversify Company Representation:")
            print("   • Avoid concentration in single companies")
            print("   • Target multiple contacts per strategic company")
        
        return df
        
    except Exception as e:
        print(f"❌ Error analyzing first-degree connections: {e}")
        return None

def show_connection_value_analysis(df):
    """Analyze the strategic value of current connections"""
    
    if df is None or df.empty:
        return
        
    print(f"\n💎 CONNECTION VALUE ANALYSIS:")
    print("-" * 30)
    
    # High-value indicators
    high_value_companies = ['airbnb', 'uber', 'google', 'microsoft', 'amazon', 'apple', 'meta']
    high_value_count = 0
    
    for company in df['connection_company']:
        if pd.notna(company):
            if any(hv_company in company.lower() for hv_company in high_value_companies):
                high_value_count += 1
    
    if high_value_count > 0:
        print(f"✅ High-Value Tech Companies: {high_value_count}")
        print("   • Strong foundation in technology sector")
        print("   • Access to innovation leaders")
    
    # Connection quality score
    total_connections = len(df)
    
    # Score factors
    scores = []
    
    # Company diversity (max 20 points)
    unique_companies = len(set(df['connection_company'].dropna()))
    company_diversity_score = min(20, (unique_companies / total_connections) * 20)
    scores.append(('Company Diversity', company_diversity_score))
    
    # Geographic diversity (max 15 points) 
    unique_locations = len(set(df['connection_location'].dropna())) if 'connection_location' in df.columns else 1
    geo_diversity_score = min(15, unique_locations * 3)
    scores.append(('Geographic Diversity', geo_diversity_score))    # High-value company presence (max 25 points)
    hv_score = min(25, high_value_count * 5)
    scores.append(('High-Value Companies', hv_score))
    
    # Network size foundation (max 20 points)
    size_score = min(20, total_connections * 2)
    scores.append(('Network Size', size_score))
    
    # Leadership connections (max 20 points)
    leadership_keywords = ['director', 'vp', 'ceo', 'cto', 'head of', 'chief']
    leadership_count = sum(1 for title in df['connection_title'] 
                          if pd.notna(title) and any(kw in title.lower() for kw in leadership_keywords))
    leadership_score = min(20, leadership_count * 4)
    scores.append(('Leadership Access', leadership_score))
    
    total_score = sum(score for _, score in scores)
    
    print(f"\n📊 NETWORK QUALITY SCORE: {total_score:.1f}/100")
    print("-" * 30)
    for category, score in scores:
        print(f"{category:<20} {score:>5.1f} pts")
    
    if total_score >= 80:
        rating = "🏆 Excellent"
    elif total_score >= 60:
        rating = "🥈 Very Good"
    elif total_score >= 40:
        rating = "🥉 Good"
    else:
        rating = "📈 Building"
    
    print(f"\nOverall Rating: {rating}")

def main():
    """Main analysis function"""
    
    print("🤝 LinkedIn First-Degree Connection Intelligence")
    print("=" * 60)
    
    df = analyze_first_degree_connections()
    
    if df is not None:
        show_connection_value_analysis(df)
        
        print(f"\n🎯 NEXT STEPS:")
        print("-" * 20)
        print("1. 📊 Use Database Explorer to view detailed connection data")
        print("2. 🎯 Set networking goals based on analysis insights")
        print("3. 📈 Track connection growth and quality metrics")
        print("4. 🤝 Focus on building genuine professional relationships")

if __name__ == "__main__":
    main()