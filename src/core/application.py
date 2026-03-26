"""
Enhanced Job Search Intelligence Application
Main application class with enterprise-grade patterns
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..config import get_config, AppConfig, AnalysisMode
from ..resources import get_resource_manager
from ..utils.logging_config import create_emoji_logger
from ..utils.error_handling import error_context, AppError
from ..core.job_search_intelligence import LinkedInIntelligenceEngine
from ..core.analysis_engine import AnalysisEngine
from ..integrations.notifications import NotificationManager
from ..integrations.monitoring import MonitoringSystem

@dataclass
class ApplicationState:
    """Application state tracking"""
    started_at: datetime
    current_operation: str = "idle"
    operations_count: int = 0
    errors_count: int = 0
    last_error: Optional[str] = None
    status: str = "initializing"

class Application:
    """
    Main Job Search Intelligence Application
    
    Features:
    - Enterprise resource management
    - Comprehensive monitoring
    - Multi-channel notifications
    - Advanced error handling
    - Performance optimization
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize the application with configuration"""
        self.config = config or get_config()
        self.logger = create_emoji_logger(__name__)
        
        # Application state
        self.state = ApplicationState(started_at=datetime.now())
        
        # Core components
        self.resource_manager = None
        self.intelligence_engine = None
        self.analysis_engine = None
        self.notification_manager = None
        self.monitoring_system = None
        
        # Performance tracking
        self.performance_metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'average_operation_time': 0.0
        }
        
        self.logger.info("🚀 Job Search Intelligence Application initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize all application components
        
        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("🔧 Initializing application components...")
            
            # Initialize resource manager
            async with error_context("resource_manager_init"):
                self.resource_manager = get_resource_manager(self.config)
                success = await self.resource_manager.initialize()
                if not success:
                    raise AppError("Resource manager initialization failed")
                self.logger.info("✅ Resource manager initialized")
            
            # Initialize intelligence engine
            async with error_context("intelligence_engine_init"):
                self.intelligence_engine = LinkedInIntelligenceEngine(
                    config=self.config,
                    resource_manager=self.resource_manager
                )
                await self.intelligence_engine.initialize()
                self.logger.info("✅ Intelligence engine initialized")
            
            # Initialize analysis engine
            async with error_context("analysis_engine_init"):
                self.analysis_engine = AnalysisEngine(
                    config=self.config,
                    resource_manager=self.resource_manager
                )
                await self.analysis_engine.initialize()
                self.logger.info("✅ Analysis engine initialized")
            
            # Initialize notification manager
            if self.config.notifications.enabled:
                async with error_context("notification_manager_init"):
                    self.notification_manager = NotificationManager(
                        config=self.config
                    )
                    await self.notification_manager.initialize()
                    self.logger.info("✅ Notification manager initialized")
            
            # Initialize monitoring system
            if self.config.monitoring.enabled:
                async with error_context("monitoring_system_init"):
                    self.monitoring_system = MonitoringSystem(
                        config=self.config,
                        resource_manager=self.resource_manager
                    )
                    await self.monitoring_system.initialize()
                    await self.monitoring_system.start()
                    self.logger.info("✅ Monitoring system initialized")
            
            self.state.status = "ready"
            self.logger.info("🎉 Application initialization completed successfully!")
            
            # Send startup notification
            if self.notification_manager:
                await self.notification_manager.send_notification(
                    "Job Search Intelligence Startup",
                    "Application started successfully",
                    priority="normal"
                )
            
            return True
            
        except Exception as e:
            self.state.status = "failed"
            self.state.last_error = str(e)
            self.logger.error(f"❌ Application initialization failed: {e}")
            return False
    
    async def run(self) -> Dict[str, Any]:
        """
        Run the main application workflow
        
        Returns:
            Analysis results dictionary
        """
        if self.state.status != "ready":
            raise AppError("Application not properly initialized")
        
        try:
            self.logger.info("🔍 Starting Job Search Intelligence Analysis...")
            self.state.current_operation = "intelligence_analysis"
            self.state.status = "running"
            
            start_time = time.time()
            
            # Run intelligence analysis based on configuration
            if self.config.analysis.mode == AnalysisMode.QUICK:
                results = await self._run_quick_analysis()
            elif self.config.analysis.mode == AnalysisMode.STANDARD:
                results = await self._run_standard_analysis()
            elif self.config.analysis.mode == AnalysisMode.DEEP:
                results = await self._run_deep_analysis()
            elif self.config.analysis.mode == AnalysisMode.INTELLIGENCE:
                results = await self._run_intelligence_analysis()
            else:
                results = await self._run_standard_analysis()
            
            # Calculate performance metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(True, execution_time)
            
            # Add execution metadata
            results['execution_metadata'] = {
                'mode': self.config.analysis.mode.value,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            self.state.status = "completed"
            self.logger.info(f"✅ Analysis completed in {execution_time:.2f}s")
            
            # Send completion notification
            if self.notification_manager:
                await self.notification_manager.send_notification(
                    f"📊 LinkedIn analysis completed successfully in {execution_time:.2f}s",
                    priority="normal",
                    channel="all"
                )
            
            return results
            
        except Exception as e:
            self.state.status = "error"
            self.state.last_error = str(e)
            self.state.errors_count += 1
            
            execution_time = time.time() - start_time if 'start_time' in locals() else 0
            self._update_performance_metrics(False, execution_time)
            
            self.logger.error(f"❌ Analysis failed: {e}")
            
            # Send error notification
            if self.notification_manager:
                await self.notification_manager.send_notification(
                    f"🚨 LinkedIn analysis failed: {str(e)[:100]}...",
                    priority="high",
                    channel="all"
                )
            
            raise AppError(f"Analysis execution failed: {e}")
    
    async def _run_quick_analysis(self) -> Dict[str, Any]:
        """Run quick analysis - basic profile and connections"""
        async with error_context("quick_analysis"):
            self.logger.info("⚡ Running quick analysis...")
            
            # Get basic profile information
            profile_data = await self.intelligence_engine.get_user_profile()
            
            # Get connection count
            connection_count = await self.intelligence_engine.get_connection_count()
            
            return {
                'analysis_type': 'quick',
                'profile': profile_data,
                'network_size': connection_count,
                'insights': ['Quick analysis provides basic profile overview']
            }
    
    async def _run_standard_analysis(self) -> Dict[str, Any]:
        """Run standard analysis - full network analysis"""
        async with error_context("standard_analysis"):
            self.logger.info("📊 Running standard analysis...")
            
            # Get comprehensive network data
            network_data = await self.intelligence_engine.analyze_network()
            
            # Perform analysis
            analysis_results = await self.analysis_engine.analyze_network_patterns(network_data)
            
            return {
                'analysis_type': 'standard',
                'network_data': network_data,
                'analysis_results': analysis_results,
                'insights': analysis_results.get('insights', [])
            }
    
    async def _run_deep_analysis(self) -> Dict[str, Any]:
        """Run deep analysis - includes AI insights"""
        async with error_context("deep_analysis"):
            self.logger.info("🧠 Running deep analysis with AI insights...")
            
            # Get comprehensive data
            network_data = await self.intelligence_engine.analyze_network()
            analysis_results = await self.analysis_engine.analyze_network_patterns(network_data)
            
            # Generate AI insights if enabled
            ai_insights = []
            if self.config.ai.enabled:
                ai_insights = await self.analysis_engine.generate_ai_insights(
                    network_data, analysis_results
                )
            
            return {
                'analysis_type': 'deep',
                'network_data': network_data,
                'analysis_results': analysis_results,
                'ai_insights': ai_insights,
                'insights': analysis_results.get('insights', []) + ai_insights
            }
    
    async def _run_intelligence_analysis(self) -> Dict[str, Any]:
        """Run full intelligence analysis - comprehensive insights"""
        async with error_context("intelligence_analysis"):
            self.logger.info("🎯 Running full intelligence analysis...")
            
            # Get all available data
            network_data = await self.intelligence_engine.analyze_network()
            analysis_results = await self.analysis_engine.analyze_network_patterns(network_data)
            
            # Generate AI insights and recommendations
            ai_insights = []
            recommendations = []
            
            if self.config.ai.enabled:
                ai_insights = await self.analysis_engine.generate_ai_insights(
                    network_data, analysis_results
                )
                recommendations = await self.analysis_engine.generate_recommendations(
                    network_data, analysis_results, ai_insights
                )
            
            # Perform advanced analysis
            competitive_analysis = await self.analysis_engine.analyze_competitive_landscape(
                network_data
            )
            
            opportunity_analysis = await self.analysis_engine.identify_opportunities(
                network_data, analysis_results
            )
            
            return {
                'analysis_type': 'intelligence',
                'network_data': network_data,
                'analysis_results': analysis_results,
                'ai_insights': ai_insights,
                'recommendations': recommendations,
                'competitive_analysis': competitive_analysis,
                'opportunity_analysis': opportunity_analysis,
                'insights': (
                    analysis_results.get('insights', []) + 
                    ai_insights + 
                    recommendations
                )
            }
    
    def _update_performance_metrics(self, success: bool, execution_time: float):
        """Update performance tracking metrics"""
        self.performance_metrics['total_operations'] += 1
        self.state.operations_count += 1
        
        if success:
            self.performance_metrics['successful_operations'] += 1
        else:
            self.performance_metrics['failed_operations'] += 1
        
        # Update average execution time
        total_ops = self.performance_metrics['total_operations']
        current_avg = self.performance_metrics['average_operation_time']
        self.performance_metrics['average_operation_time'] = (
            (current_avg * (total_ops - 1) + execution_time) / total_ops
        )
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive application health status"""
        health_status = {
            'status': self.state.status,
            'uptime': (datetime.now() - self.state.started_at).total_seconds(),
            'current_operation': self.state.current_operation,
            'operations_count': self.state.operations_count,
            'errors_count': self.state.errors_count,
            'performance_metrics': self.performance_metrics,
            'components': {}
        }
        
        # Check component health
        if self.resource_manager:
            health_status['components']['resource_manager'] = 'healthy'
        
        if self.intelligence_engine:
            health_status['components']['intelligence_engine'] = 'healthy'
        
        if self.analysis_engine:
            health_status['components']['analysis_engine'] = 'healthy'
        
        if self.notification_manager:
            health_status['components']['notification_manager'] = 'healthy'
        
        if self.monitoring_system:
            health_status['components']['monitoring_system'] = 'healthy'
        
        return health_status
    
    async def cleanup(self):
        """Cleanup all application resources"""
        try:
            self.logger.info("🧹 Starting application cleanup...")
            
            # Cleanup monitoring system
            if self.monitoring_system:
                await self.monitoring_system.stop()
                self.logger.info("✅ Monitoring system stopped")
            
            # Cleanup notification manager
            if self.notification_manager:
                await self.notification_manager.cleanup()
                self.logger.info("✅ Notification manager cleaned up")
            
            # Cleanup engines
            if self.analysis_engine:
                await self.analysis_engine.cleanup()
                self.logger.info("✅ Analysis engine cleaned up")
            
            if self.intelligence_engine:
                await self.intelligence_engine.cleanup()
                self.logger.info("✅ Intelligence engine cleaned up")
            
            # Cleanup resource manager (last)
            if self.resource_manager:
                await self.resource_manager.cleanup()
                self.logger.info("✅ Resource manager cleaned up")
            
            self.state.status = "shutdown"
            self.logger.info("✅ Application cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup error: {e}")
    
    def __repr__(self) -> str:
        """String representation of the application"""
        return (
            f"LinkedInIntelligenceApp(status={self.state.status}, "
            f"mode={self.config.analysis.mode.value}, "
            f"operations={self.state.operations_count})"
        )
