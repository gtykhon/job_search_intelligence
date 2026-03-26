#!/usr/bin/env python3
"""
Test script for the analytics engine fix
"""

from src.analytics.advanced_analytics_engine import AdvancedAnalyticsEngine

def test_analytics():
    engine = AdvancedAnalyticsEngine('job_search.db')
    print('Testing all three metrics you requested...')
    
    metrics = ['leadership_engagement_percentage', 'comment_quality_score', 'f500_penetration_percentage']
    
    for metric in metrics:
        try:
            trend = engine.analyze_trends(metric, 7)
            print(f'✅ {metric}: {trend.trend_direction} trend, current: {trend.current_value}')
        except Exception as e:
            print(f'❌ {metric}: {e}')
    
    print('\nTesting benchmark analysis...')
    for metric in metrics:
        try:
            benchmark = engine.benchmark_performance(metric)
            print(f'✅ {metric}: Grade {benchmark.performance_grade}, Percentile: {benchmark.percentile_rank}')
        except Exception as e:
            print(f'❌ {metric}: {e}')

if __name__ == "__main__":
    test_analytics()