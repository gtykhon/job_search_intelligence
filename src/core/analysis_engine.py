"""
Analysis Engine with AI Integration
Advanced analysis capabilities with Cloud and Local LLM integration
"""

import asyncio
import json
import logging
import requests
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta

# Cloud AI imports with fallbacks
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AsyncAnthropic = None

# Local LLM imports with fallbacks
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

# Note: Removed llama-cpp-python and ollama libraries for direct HTTP calls

from ..config import AppConfig
from ..resources import ResourceManager
from ..utils.error_handling import error_context, ProcessingError, ExternalServiceError

logger = logging.getLogger(__name__)

class AnalysisEngine:
    """
    Advanced Analysis Engine with AI Integration
    Provides intelligent insights using Claude and OpenAI
    """
    
    def __init__(self, config: AppConfig, resource_manager: ResourceManager):
        self.config = config
        self.resource_manager = resource_manager
        
        # AI clients
        self._claude_client = None
        self._openai_client = None
        self._http_session = None  # For direct HTTP calls to local LLMs
        
        # Analysis cache
        self._analysis_cache = {}
        self._cache_expiry = timedelta(hours=2)
        
        # Analysis patterns
        self._pattern_templates = {
            'network_growth': {
                'description': 'Analyze network growth patterns and trajectory',
                'ai_prompt_template': 'Analyze the LinkedIn network growth pattern: {data}. Provide insights on growth trends, quality indicators, and recommendations.'
            },
            'industry_influence': {
                'description': 'Assess influence and positioning within industry',
                'ai_prompt_template': 'Analyze industry influence based on LinkedIn network data: {data}. Evaluate thought leadership potential and industry positioning.'
            },
            'connection_quality': {
                'description': 'Evaluate the quality and strategic value of connections',
                'ai_prompt_template': 'Evaluate connection quality from this LinkedIn network: {data}. Assess strategic value, engagement potential, and relationship strength.'
            },
            'competitive_analysis': {
                'description': 'Analyze competitive landscape and positioning',
                'ai_prompt_template': 'Perform competitive analysis based on LinkedIn data: {data}. Identify competitive advantages, gaps, and strategic opportunities.'
            },
            'opportunity_identification': {
                'description': 'Identify growth and networking opportunities',
                'ai_prompt_template': 'Identify networking and growth opportunities from LinkedIn data: {data}. Suggest specific actions and strategic connections.'
            }
        }
    
    async def initialize(self):
        """Initialize the Analysis Engine and AI clients"""
        async with error_context("analysis_engine_initialization"):
            try:
                # Initialize AI client based on provider
                if self.config.ai.enabled:
                    if self.config.ai.provider == "claude" and ANTHROPIC_AVAILABLE and self.config.ai.api_key:
                        self._claude_client = AsyncAnthropic(
                            api_key=self.config.ai.api_key
                        )
                        logger.info("🤖 Claude client initialized")
                        
                    elif self.config.ai.provider == "openai" and OPENAI_AVAILABLE and self.config.ai.api_key:
                        self._openai_client = openai.AsyncOpenAI(
                            api_key=self.config.ai.api_key
                        )
                        logger.info("🤖 OpenAI client initialized")
                        
                    elif self.config.ai.provider in ["ollama", "lmstudio", "textgen", "localai", "custom"]:
                        # Test HTTP endpoint for local LLM services
                        try:
                            host = self._get_llm_host()
                            test_endpoint = f"{host}/v1/models" if self.config.ai.provider == "lmstudio" else f"{host}/api/tags" if self.config.ai.provider == "ollama" else f"{host}/v1/models"
                            
                            response = requests.get(test_endpoint, timeout=5)
                            if response.status_code == 200:
                                self._http_session = True  # Mark as available
                                logger.info("🤖 %s HTTP endpoint initialized at %s", 
                                          self.config.ai.provider.capitalize(), host)
                            else:
                                logger.warning("⚠️ %s service not responding at %s", 
                                             self.config.ai.provider.capitalize(), host)
                        except Exception as e:
                            logger.warning("⚠️ Failed to connect to %s: %s", self.config.ai.provider, e)
                    
                    else:
                        logger.warning("⚠️ AI provider '%s' not available or not configured", self.config.ai.provider)
                
                # Check if any AI client is available
                if not any([self._claude_client, self._openai_client, self._http_session]):
                    logger.warning("⚠️ No AI clients available - AI features will be disabled")
                
                logger.info("✅ Analysis Engine initialized successfully")
                
            except Exception as e:
                raise ProcessingError(
                    f"Failed to initialize Analysis Engine: {e}",
                    processor="analysis_engine"
                ) from e
    
    def _get_llm_host(self) -> str:
        """Get the appropriate host URL for the configured LLM provider"""
        if self.config.ai.provider == "ollama":
            return self.config.ai.ollama_host
        elif self.config.ai.provider == "lmstudio":
            return self.config.ai.lmstudio_host
        elif self.config.ai.provider == "textgen":
            return self.config.ai.textgen_host
        elif self.config.ai.provider == "localai":
            return self.config.ai.localai_host
        elif self.config.ai.provider == "custom":
            return self.config.ai.custom_host
        else:
            return "http://localhost:8000"
    
    def _get_llm_model(self) -> str:
        """Get the appropriate model name for the configured LLM provider"""
        if self.config.ai.provider == "ollama":
            return self.config.ai.ollama_model
        elif self.config.ai.provider == "lmstudio":
            return self.config.ai.lmstudio_model
        elif self.config.ai.provider == "textgen":
            return "text-generation-webui"
        elif self.config.ai.provider == "localai":
            return self.config.ai.localai_model
        elif self.config.ai.provider == "custom":
            return self.config.ai.custom_model
        else:
            return "default-model"
    
    async def analyze_network_patterns(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network patterns and provide insights"""
        cache_key = f"network_patterns_{hash(str(network_data))}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            return self._analysis_cache[cache_key]['data']
        
        async with error_context("analyze_network_patterns"):
            try:
                results = {
                    'analyzed_at': datetime.now().isoformat(),
                    'data_summary': self._summarize_network_data(network_data),
                    'patterns': {},
                    'insights': {},
                    'confidence_scores': {}
                }
                
                # Basic pattern analysis
                results['patterns'] = await self._analyze_basic_patterns(network_data)
                
                # Industry analysis
                results['insights']['industry_analysis'] = self._analyze_industry_distribution(network_data)
                
                # Geographic analysis
                results['insights']['geographic_analysis'] = self._analyze_geographic_distribution(network_data)
                
                # Connection strength analysis
                results['insights']['connection_strength'] = self._analyze_connection_strength(network_data)
                
                # Growth potential analysis
                results['insights']['growth_potential'] = self._analyze_growth_potential(network_data)
                
                # Set confidence scores
                results['confidence_scores'] = {
                    'overall': 0.85,
                    'pattern_detection': 0.90,
                    'industry_analysis': 0.88,
                    'geographic_analysis': 0.82,
                    'growth_analysis': 0.75
                }
                
                # Cache the result
                self._analysis_cache[cache_key] = {
                    'data': results,
                    'cached_at': datetime.now()
                }
                
                # Store in database
                await self._store_analysis_results('network_patterns', results)
                
                logger.info(f"✅ Network pattern analysis complete with {len(results['patterns'])} patterns identified")
                return results
                
            except Exception as e:
                raise ProcessingError(
                    f"Failed to analyze network patterns: {e}",
                    processor="analysis_engine",
                    data_id="network_patterns"
                ) from e
    
    async def generate_ai_insights(self, analysis_data: Dict[str, Any], 
                                 insight_type: str = 'comprehensive') -> Dict[str, Any]:
        """Generate AI-powered insights using Claude or OpenAI"""
        # Check if any AI service is available
        ai_available = any([
            self._claude_client, 
            self._openai_client, 
            self._http_session and self.config.ai.provider in ["ollama", "lmstudio", "textgen", "localai", "custom"],
            self.config.ai.provider == "local"
        ])
        
        if not ai_available:
            return {
                'insights': 'AI insights unavailable - no AI client configured',
                'source': 'fallback',
                'confidence': 0.0
            }
        
        cache_key = f"ai_insights_{insight_type}_{hash(str(analysis_data))}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            return self._analysis_cache[cache_key]['data']
        
        async with error_context("generate_ai_insights"):
            try:
                # Prepare data for AI analysis
                analysis_summary = self._prepare_ai_analysis_data(analysis_data)
                
                # Generate insights using preferred AI service
                if self._claude_client:
                    insights = await self._generate_claude_insights(analysis_summary, insight_type)
                    source = 'claude'
                elif self._openai_client:
                    insights = await self._generate_openai_insights(analysis_summary, insight_type)
                    source = 'openai'
                elif self._http_session and self.config.ai.provider in ["ollama", "lmstudio", "textgen", "localai", "custom"]:
                    insights = await self._generate_http_llm_insights(analysis_summary, insight_type)
                    source = self.config.ai.provider
                elif self.config.ai.provider == "local":
                    insights = await self._generate_local_insights(analysis_summary, insight_type)
                    source = 'local'
                else:
                    insights = await self._generate_fallback_insights(analysis_summary, insight_type)
                    source = 'fallback'
                
                results = {
                    'insights': insights,
                    'insight_type': insight_type,
                    'generated_at': datetime.now().isoformat(),
                    'source': source,
                    'confidence': 0.9 if source in ['claude', 'openai'] else 0.8 if source in ['ollama', 'llamacpp', 'local'] else 0.6
                }
                
                # Cache the result
                self._analysis_cache[cache_key] = {
                    'data': results,
                    'cached_at': datetime.now()
                }
                
                # Store in database
                await self._store_analysis_results('ai_insights', results)
                
                logger.info(f"✅ AI insights generated using {results['source']}")
                return results
                
            except Exception as e:
                raise ProcessingError(
                    f"Failed to generate AI insights: {e}",
                    processor="analysis_engine",
                    data_id="ai_insights"
                ) from e
    
    async def generate_recommendations(self, analysis_data: Dict[str, Any], 
                                     focus_area: str = 'growth') -> Dict[str, Any]:
        """Generate actionable recommendations"""
        cache_key = f"recommendations_{focus_area}_{hash(str(analysis_data))}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            return self._analysis_cache[cache_key]['data']
        
        async with error_context("generate_recommendations"):
            try:
                # Base recommendations from pattern analysis
                base_recommendations = self._generate_base_recommendations(analysis_data, focus_area)
                
                # Enhance with AI if available
                if self._claude_client or self._openai_client:
                    ai_recommendations = await self._generate_ai_recommendations(analysis_data, focus_area)
                    recommendations = self._merge_recommendations(base_recommendations, ai_recommendations)
                else:
                    recommendations = base_recommendations
                
                results = {
                    'recommendations': recommendations,
                    'focus_area': focus_area,
                    'generated_at': datetime.now().isoformat(),
                    'priority_actions': self._extract_priority_actions(recommendations),
                    'confidence': 0.85 if (self._claude_client or self._openai_client) else 0.70
                }
                
                # Cache the result
                self._analysis_cache[cache_key] = {
                    'data': results,
                    'cached_at': datetime.now()
                }
                
                # Store in database
                await self._store_analysis_results('recommendations', results)
                
                logger.info(f"✅ Generated {len(recommendations)} recommendations for {focus_area}")
                return results
                
            except Exception as e:
                raise ProcessingError(
                    f"Failed to generate recommendations: {e}",
                    processor="analysis_engine",
                    data_id="recommendations"
                ) from e
    
    async def analyze_competitive_landscape(self, network_data: Dict[str, Any], 
                                          industry: Optional[str] = None) -> Dict[str, Any]:
        """Analyze competitive landscape and positioning"""
        async with error_context("analyze_competitive_landscape"):
            try:
                # Extract industry if not provided
                if not industry:
                    industry = self._extract_primary_industry(network_data)
                
                analysis = {
                    'industry': industry,
                    'analyzed_at': datetime.now().isoformat(),
                    'competitive_metrics': {},
                    'positioning': {},
                    'opportunities': [],
                    'threats': []
                }
                
                # Analyze network composition
                industry_connections = self._analyze_industry_connections(network_data, industry)
                analysis['competitive_metrics']['industry_presence'] = industry_connections
                
                # Analyze seniority levels
                seniority_analysis = self._analyze_seniority_levels(network_data)
                analysis['competitive_metrics']['seniority_reach'] = seniority_analysis
                
                # Company analysis
                company_analysis = self._analyze_company_connections(network_data)
                analysis['competitive_metrics']['company_diversity'] = company_analysis
                
                # Positioning assessment
                analysis['positioning'] = self._assess_market_positioning(
                    industry_connections, seniority_analysis, company_analysis
                )
                
                # Identify opportunities and threats
                analysis['opportunities'] = self._identify_competitive_opportunities(analysis)
                analysis['threats'] = self._identify_competitive_threats(analysis)
                
                # Store in database
                await self._store_analysis_results('competitive_landscape', analysis)
                
                logger.info(f"✅ Competitive landscape analysis complete for {industry}")
                return analysis
                
            except Exception as e:
                raise ProcessingError(
                    f"Failed to analyze competitive landscape: {e}",
                    processor="analysis_engine",
                    data_id="competitive_landscape"
                ) from e
    
    async def identify_opportunities(self, network_data: Dict[str, Any], 
                                   analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Identify specific networking and growth opportunities"""
        async with error_context("identify_opportunities"):
            try:
                opportunities = {
                    'identified_at': datetime.now().isoformat(),
                    'networking_opportunities': [],
                    'growth_opportunities': [],
                    'content_opportunities': [],
                    'collaboration_opportunities': [],
                    'priority_score': {}
                }
                
                # Networking opportunities
                opportunities['networking_opportunities'] = self._identify_networking_gaps(network_data)
                
                # Growth opportunities
                opportunities['growth_opportunities'] = self._identify_growth_paths(analysis_results)
                
                # Content opportunities
                opportunities['content_opportunities'] = self._identify_content_gaps(network_data)
                
                # Collaboration opportunities
                opportunities['collaboration_opportunities'] = self._identify_collaboration_potential(network_data)
                
                # Calculate priority scores
                opportunities['priority_score'] = self._calculate_opportunity_priorities(opportunities)
                
                # Store in database
                await self._store_analysis_results('opportunities', opportunities)
                
                total_opportunities = sum(len(opp_list) for opp_list in [
                    opportunities['networking_opportunities'],
                    opportunities['growth_opportunities'],
                    opportunities['content_opportunities'],
                    opportunities['collaboration_opportunities']
                ])
                
                logger.info(f"✅ Identified {total_opportunities} opportunities across all categories")
                return opportunities
                
            except Exception as e:
                raise ProcessingError(
                    f"Failed to identify opportunities: {e}",
                    processor="analysis_engine",
                    data_id="opportunities"
                ) from e
    
    # Helper methods for pattern analysis
    async def _analyze_basic_patterns(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze basic network patterns"""
        connections = network_data.get('connections', [])
        metrics = network_data.get('metrics', {})
        
        patterns = {
            'connection_velocity': self._calculate_connection_velocity(connections),
            'industry_clustering': self._calculate_industry_clustering(metrics),
            'geographic_spread': self._calculate_geographic_spread(metrics),
            'professional_level_mix': self._calculate_professional_mix(connections)
        }
        
        return patterns
    
    def _summarize_network_data(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of network data for analysis"""
        return {
            'total_connections': network_data.get('total_connections', 0),
            'top_industries': list(network_data.get('metrics', {}).get('industry_distribution', {}).keys())[:5],
            'top_locations': list(network_data.get('metrics', {}).get('location_distribution', {}).keys())[:5],
            'analysis_scope': 'comprehensive',
            'data_quality': 'high' if network_data.get('total_connections', 0) > 50 else 'medium'
        }
    
    def _analyze_industry_distribution(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze industry distribution patterns"""
        industry_dist = network_data.get('metrics', {}).get('industry_distribution', {})
        total_connections = network_data.get('total_connections', 1)
        
        return {
            'diversity_score': len(industry_dist) / max(total_connections * 0.1, 1),
            'concentration_ratio': max(industry_dist.values()) / total_connections if industry_dist else 0,
            'top_industry': max(industry_dist.items(), key=lambda x: x[1])[0] if industry_dist else 'Unknown',
            'coverage': list(industry_dist.keys())[:10]
        }
    
    def _analyze_geographic_distribution(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze geographic distribution patterns"""
        location_dist = network_data.get('metrics', {}).get('location_distribution', {})
        total_connections = network_data.get('total_connections', 1)
        
        return {
            'global_reach': len(location_dist),
            'concentration_ratio': max(location_dist.values()) / total_connections if location_dist else 0,
            'primary_market': max(location_dist.items(), key=lambda x: x[1])[0] if location_dist else 'Unknown',
            'geographic_diversity': min(len(location_dist) / 10, 1.0)  # Normalized score
        }
    
    def _analyze_connection_strength(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze connection strength indicators"""
        connections = network_data.get('connections', [])
        
        # Simplified strength analysis
        strong_connections = sum(1 for conn in connections if conn.get('strength', 0) > 0.7)
        medium_connections = sum(1 for conn in connections if 0.3 < conn.get('strength', 0) <= 0.7)
        weak_connections = len(connections) - strong_connections - medium_connections
        
        return {
            'strong_connections': strong_connections,
            'medium_connections': medium_connections,
            'weak_connections': weak_connections,
            'average_strength': sum(conn.get('strength', 0.5) for conn in connections) / len(connections) if connections else 0
        }
    
    def _analyze_growth_potential(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network growth potential"""
        total_connections = network_data.get('total_connections', 0)
        
        # Growth potential based on current network size and diversity
        industry_diversity = len(network_data.get('metrics', {}).get('industry_distribution', {}))
        geographic_diversity = len(network_data.get('metrics', {}).get('location_distribution', {}))
        
        growth_score = min((industry_diversity * geographic_diversity) / 100, 1.0)
        
        return {
            'growth_score': growth_score,
            'optimal_size_gap': max(500 - total_connections, 0),  # Assume 500 is optimal
            'diversity_opportunities': 20 - industry_diversity,  # Room for 20 industries
            'expansion_readiness': 'high' if growth_score > 0.7 else 'medium' if growth_score > 0.4 else 'low'
        }
    
    # AI Integration methods
    async def _generate_claude_insights(self, data: Dict[str, Any], insight_type: str) -> str:
        """Generate insights using Claude"""
        if not self._claude_client:
            return await self._generate_fallback_insights(data, insight_type)
            
        try:
            prompt = f"""
            Analyze this LinkedIn network data and provide {insight_type} insights:
            
            {json.dumps(data, indent=2)}
            
            Please provide:
            1. Key patterns and trends
            2. Strategic opportunities
            3. Potential risks or gaps
            4. Actionable recommendations
            
            Focus on professional networking strategy and business development opportunities.
            """
            
            response = await self._claude_client.messages.create(
                model=self.config.ai.model,
                max_tokens=1000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.warning(f"⚠️ Claude analysis failed: {e}")
            return await self._generate_fallback_insights(data, insight_type)
    
    async def _generate_openai_insights(self, data: Dict[str, Any], insight_type: str) -> str:
        """Generate insights using OpenAI"""
        if not self._openai_client:
            return await self._generate_fallback_insights(data, insight_type)
            
        try:
            prompt = f"""
            Analyze this LinkedIn network data and provide {insight_type} insights:
            
            {json.dumps(data, indent=2)}
            
            Provide strategic analysis focusing on networking opportunities and professional growth.
            """
            
            response = await self._openai_client.chat.completions.create(
                model=self.config.ai.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.warning(f"⚠️ OpenAI analysis failed: {e}")
            return await self._generate_fallback_insights(data, insight_type)
    
    async def _generate_fallback_insights(self, data: Dict[str, Any], insight_type: str) -> str:
        """Generate basic insights without AI"""
        total_connections = data.get('total_connections', 0)
        top_industries = data.get('top_industries', [])
        top_locations = data.get('top_locations', [])
        
        insights = f"""
        Network Analysis Summary:
        
        🎯 Network Size: {total_connections} connections
        📊 Industry Focus: Primary industries include {', '.join(top_industries[:3])}
        🌍 Geographic Reach: Strongest presence in {', '.join(top_locations[:3])}
        
        Key Observations:
        • {"Strong professional network" if total_connections > 100 else "Growing professional network"}
        • {"Diverse industry representation" if len(top_industries) > 5 else "Focused industry presence"}
        • {"Good geographic diversity" if len(top_locations) > 5 else "Concentrated geographic focus"}
        
        Recommendations:
        • Focus on quality engagement with existing connections
        • Consider expanding into complementary industries
        • Leverage geographic concentrations for local opportunities
        """
        
        return insights
    
    async def _generate_ollama_insights(self, data: Dict[str, Any], insight_type: str) -> str:
        """Generate insights using Ollama local LLM"""
        try:
            # Prepare the prompt
            template = self._pattern_templates.get(insight_type, {})
            prompt = template.get('ai_prompt_template', 'Analyze this LinkedIn data: {data}').format(
                data=json.dumps(data, indent=2)
            )
            
            # Call Ollama API
            payload = {
                "model": self.config.ai.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.ai.temperature,
                    "num_predict": self.config.ai.max_tokens
                }
            }
            
            response = requests.post(
                f"{self.config.ai.ollama_host}/api/generate",
                json=payload,
                timeout=self.config.ai.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No insights generated')
            else:
                logger.error("❌ Ollama API error: %s", response.text)
                return "Error generating insights with Ollama"
                
        except Exception as e:
            logger.error("❌ Ollama insight generation failed: %s", e)
            return "Failed to generate insights with Ollama"
    
    async def _generate_http_llm_insights(self, data: Dict[str, Any], insight_type: str) -> str:
        """Generate insights using HTTP API for local LLM services"""
        try:
            if not self._http_session:
                return f"{self.config.ai.provider.capitalize()} HTTP client not available"
            
            if not AIOHTTP_AVAILABLE:
                return "aiohttp library not available for HTTP requests"
            
            # Prepare the prompt
            template = self._pattern_templates.get(insight_type, {})
            prompt = template.get('ai_prompt_template', 'Analyze this LinkedIn data: {data}').format(
                data=json.dumps(data, indent=2)
            )
            
            host = self._get_llm_host()
            model = self._get_llm_model()
            
            # Create request payload based on provider
            if self.config.ai.provider == "ollama":
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config.ai.temperature,
                        "num_predict": self.config.ai.max_tokens
                    }
                }
                endpoint = f"{host}/api/generate"
                
            elif self.config.ai.provider in ["lmstudio", "localai", "custom"]:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self.config.ai.temperature,
                    "max_tokens": self.config.ai.max_tokens,
                    "stream": False
                }
                endpoint = f"{host}/v1/chat/completions"
                
            elif self.config.ai.provider == "textgen":
                payload = {
                    "prompt": prompt,
                    "max_tokens": self.config.ai.max_tokens,
                    "temperature": self.config.ai.temperature,
                    "stop": ["</s>"]
                }
                endpoint = f"{host}/api/v1/generate"
            
            else:
                return f"Unsupported provider: {self.config.ai.provider}"
            
            # Make HTTP request
            headers = {"Content-Type": "application/json"}
            if hasattr(self.config.ai, 'custom_headers') and self.config.ai.custom_headers:
                headers.update(self.config.ai.custom_headers)
            
            # Use aiohttp for async requests
            if aiohttp:
                timeout = aiohttp.ClientTimeout(total=60)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(endpoint, json=payload, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            # Extract response based on provider format
                            if self.config.ai.provider == "ollama":
                                return result.get('response', 'No response from Ollama')
                            elif self.config.ai.provider in ["lmstudio", "localai", "custom"]:
                                return result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
                            elif self.config.ai.provider == "textgen":
                                return result.get('results', [{}])[0].get('text', 'No response from TextGen')
                        else:
                            logger.error("❌ HTTP request failed: %s", response.status)
                            return f"HTTP request failed with status {response.status}"
            else:
                # Fallback to synchronous requests if aiohttp not available
                response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract response based on provider format
                    if self.config.ai.provider == "ollama":
                        return result.get('response', 'No response from Ollama')
                    elif self.config.ai.provider in ["lmstudio", "localai", "custom"]:
                        return result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
                    elif self.config.ai.provider == "textgen":
                        return result.get('results', [{}])[0].get('text', 'No response from TextGen')
                else:
                    logger.error("❌ HTTP request failed: %s", response.status_code)
                    return f"HTTP request failed with status {response.status_code}"
            
            return "No response received from HTTP LLM service"
                        
        except Exception as e:
            logger.error("❌ HTTP LLM insight generation failed: %s", e)
            return f"Failed to generate insights with {self.config.ai.provider}: {str(e)}"
    
    async def _generate_local_insights(self, data: Dict[str, Any], insight_type: str) -> str:
        """Generate insights using generic local model (placeholder for custom implementations)"""
        try:
            # This is a placeholder for custom local model implementations
            # You can extend this method to support other local LLM frameworks
            
            logger.info("🤖 Generating insights with local model provider: %s", self.config.ai.provider)
            
            # For now, return a structured analysis based on the data
            total_connections = data.get('total_connections', 0)
            insights = f"""
            Local AI Analysis - {insight_type.replace('_', ' ').title()}:
            
            Based on analysis of {total_connections} LinkedIn connections:
            
            • Network composition shows professional diversity
            • Strategic opportunities identified in connection patterns  
            • Engagement potential varies across industry segments
            • Geographic distribution suggests market reach capabilities
            
            [Note: This is a template response. Integrate your preferred local LLM here.]
            """
            
            return insights
            
        except Exception as e:
            logger.error("❌ Local model insight generation failed: %s", e)
            return "Failed to generate insights with local model"
    
    # Utility methods
    def _prepare_ai_analysis_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for AI analysis by filtering and summarizing"""
        return {
            'summary': analysis_data.get('data_summary', {}),
            'patterns': analysis_data.get('patterns', {}),
            'insights': analysis_data.get('insights', {}),
            'confidence': analysis_data.get('confidence_scores', {})
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached analysis is still valid"""
        if cache_key not in self._analysis_cache:
            return False
        
        cached_at = self._analysis_cache[cache_key]['cached_at']
        return datetime.now() - cached_at < self._cache_expiry
    
    async def _store_analysis_results(self, analysis_type: str, results: Dict[str, Any]):
        """Store analysis results in database"""
        try:
            with self.resource_manager.get_database_connection("job_search") as conn:
                conn.execute("""
                    INSERT INTO analysis_results 
                    (id, analysis_type, profile_id, results, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    f"{analysis_type}_{int(datetime.now().timestamp())}",
                    analysis_type,
                    'current_user',
                    json.dumps(results),
                    results.get('confidence', 0.8),
                    datetime.now()
                ))
                conn.commit()
        except Exception as e:
            logger.warning(f"⚠️ Failed to store analysis results: {e}")
    
    # Placeholder implementations for complex methods
    def _calculate_connection_velocity(self, connections: List[Dict]) -> float:
        """Calculate connection growth velocity"""
        return len(connections) / max(1, 30)  # Simplified: connections per day over 30 days
    
    def _calculate_industry_clustering(self, metrics: Dict) -> float:
        """Calculate industry clustering coefficient"""
        industry_dist = metrics.get('industry_distribution', {})
        if not industry_dist:
            return 0.0
        return max(industry_dist.values()) / sum(industry_dist.values())
    
    def _calculate_geographic_spread(self, metrics: Dict) -> float:
        """Calculate geographic spread score"""
        location_dist = metrics.get('location_distribution', {})
        return min(len(location_dist) / 10, 1.0)  # Normalized to max 10 locations
    
    def _calculate_professional_mix(self, connections: List[Dict]) -> Dict[str, int]:
        """Calculate professional level mix"""
        levels = {'junior': 0, 'mid': 0, 'senior': 0, 'executive': 0}
        for conn in connections:
            level = conn.get('seniority_level', 'mid').lower()
            if level in levels:
                levels[level] += 1
        return levels
    
    # Additional placeholder methods for comprehensive functionality
    def _generate_base_recommendations(self, analysis_data: Dict, focus_area: str) -> List[Dict]:
        """Generate base recommendations without AI"""
        return [
            {
                'category': 'networking',
                'action': 'Engage with top industry connections weekly',
                'priority': 'high',
                'expected_impact': 'Strengthen professional relationships'
            },
            {
                'category': 'growth',
                'action': 'Join industry-specific LinkedIn groups',
                'priority': 'medium',
                'expected_impact': 'Expand network reach'
            }
        ]
    
    async def _generate_ai_recommendations(self, analysis_data: Dict, focus_area: str) -> List[Dict]:
        """Generate AI-enhanced recommendations"""
        # Placeholder for AI-generated recommendations
        return []
    
    def _merge_recommendations(self, base_recs: List[Dict], ai_recs: List[Dict]) -> List[Dict]:
        """Merge base and AI recommendations"""
        return base_recs + ai_recs
    
    def _extract_priority_actions(self, recommendations: List[Dict]) -> List[Dict]:
        """Extract high-priority actions"""
        return [rec for rec in recommendations if rec.get('priority') == 'high']
    
    def _extract_primary_industry(self, network_data: Dict) -> str:
        """Extract primary industry from network data"""
        industry_dist = network_data.get('metrics', {}).get('industry_distribution', {})
        if not industry_dist:
            return 'Technology'
        return max(industry_dist.items(), key=lambda x: x[1])[0]
    
    def _analyze_industry_connections(self, network_data: Dict, industry: str) -> Dict:
        """Analyze connections within specific industry"""
        return {'industry_penetration': 0.7, 'key_companies': ['Company A', 'Company B']}
    
    def _analyze_seniority_levels(self, network_data: Dict) -> Dict:
        """Analyze seniority level distribution"""
        return {'executive_reach': 0.3, 'peer_connections': 0.5, 'junior_mentoring': 0.2}
    
    def _analyze_company_connections(self, network_data: Dict) -> Dict:
        """Analyze company diversity and connections"""
        return {'fortune_500_presence': 0.4, 'startup_connections': 0.3, 'diversity_score': 0.8}
    
    def _assess_market_positioning(self, industry_conn: Dict, seniority: Dict, company: Dict) -> Dict:
        """Assess market positioning based on network analysis"""
        return {
            'positioning_strength': 'strong',
            'influence_potential': 'high',
            'thought_leadership_readiness': 'medium'
        }
    
    def _identify_competitive_opportunities(self, analysis: Dict) -> List[str]:
        """Identify competitive opportunities"""
        return [
            'Expand C-level network in target industry',
            'Increase presence in emerging market segments'
        ]
    
    def _identify_competitive_threats(self, analysis: Dict) -> List[str]:
        """Identify competitive threats"""
        return [
            'Limited presence in key competitor networks',
            'Potential isolation from industry influencers'
        ]
    
    def _identify_networking_gaps(self, network_data: Dict) -> List[Dict]:
        """Identify networking gaps and opportunities"""
        return [
            {
                'gap_type': 'industry_leader',
                'description': 'Limited connections to industry thought leaders',
                'priority': 'high'
            }
        ]
    
    def _identify_growth_paths(self, analysis_results: Dict) -> List[Dict]:
        """Identify potential growth paths"""
        return [
            {
                'path_type': 'market_expansion',
                'description': 'Expand into adjacent industry verticals',
                'timeline': '3-6 months'
            }
        ]
    
    def _identify_content_gaps(self, network_data: Dict) -> List[Dict]:
        """Identify content and thought leadership opportunities"""
        return [
            {
                'content_type': 'industry_insights',
                'description': 'Share insights on industry trends',
                'frequency': 'weekly'
            }
        ]
    
    def _identify_collaboration_potential(self, network_data: Dict) -> List[Dict]:
        """Identify collaboration opportunities"""
        return [
            {
                'collaboration_type': 'cross_industry',
                'description': 'Partner with complementary industry professionals',
                'potential_partners': 5
            }
        ]
    
    def _calculate_opportunity_priorities(self, opportunities: Dict) -> Dict[str, float]:
        """Calculate priority scores for opportunities"""
        return {
            'networking': 0.9,
            'growth': 0.8,
            'content': 0.7,
            'collaboration': 0.6
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Clear caches
            self._analysis_cache.clear()
            
            # Close AI clients if needed
            self._claude_client = None
            self._openai_client = None
            
            logger.info("🧹 Analysis Engine cleanup complete")
            
        except Exception as e:
            logger.warning(f"⚠️ Analysis cleanup warning: {e}")
