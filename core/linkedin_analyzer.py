"""
LinkedIn Network Analyzer - Part 1: Core Implementation

Enhanced analyzer with improved:
- Network analysis
- Data processing
- Error handling
- Metrics calculation
"""

import os
import sys
import time
import json
import logging
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union
import argparse
from dataclasses import dataclass, field

from .linkedin_authenticator import LinkedInAuthenticator
from .linkedin_wrapper import LinkedInWrapper

# Custom exceptions
class LinkedInAnalyzerError(Exception):
    """Base exception for analyzer errors"""
    pass

class NetworkAnalysisError(LinkedInAnalyzerError):
    """Network analysis specific errors"""
    pass

class DataProcessingError(LinkedInAnalyzerError):
    """Data processing specific errors"""
    pass

@dataclass
class NetworkMetrics:
    """Store and calculate network metrics"""
    total_connections: int = 0
    total_followers: int = 0
    mutual_connections: int = 0
    follower_only: int = 0
    non_followers: int = 0
    unique_companies: int = 0
    unique_locations: int = 0
    unique_industries: int = 0
    connection_growth_rate: float = 0.0
    follower_growth_rate: float = 0.0
    engagement_rate: float = 0.0
    network_density: float = 0.0
    execution_time: float = 0.0
    analysis_date: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "network_size": {
                "total_connections": self.total_connections,
                "total_followers": self.total_followers,
                "mutual_connections": self.mutual_connections
            },
            "network_composition": {
                "follower_only": self.follower_only,
                "non_followers": self.non_followers,
                "unique_companies": self.unique_companies,
                "unique_locations": self.unique_locations,
                "unique_industries": self.unique_industries
            },
            "growth_metrics": {
                "connection_growth_rate": f"{self.connection_growth_rate:.2%}",
                "follower_growth_rate": f"{self.follower_growth_rate:.2%}"
            },
            "engagement_metrics": {
                "engagement_rate": f"{self.engagement_rate:.2%}",
                "network_density": f"{self.network_density:.2%}"
            },
            "execution_metrics": {
                "execution_time": f"{self.execution_time:.2f}s",
                "analysis_date": self.analysis_date
            }
        }

class LinkedInAnalyzer:
    """
    Enhanced LinkedIn Network Analyzer with improved analysis capabilities.
    """
    
    # Analysis Configuration
    BATCH_SIZE = 50
    MAX_RETRIES = 3
    DEFAULT_TIMEOUT = 30
    CACHE_DURATION = timedelta(hours=24)
    
    # Network Size Thresholds
    NETWORK_THRESHOLDS = {
        'small': 100,
        'medium': 500,
        'large': 1000,
        'very_large': 5000
    }
    
    # Metric Weights
    METRIC_WEIGHTS = {
        'connections': 0.3,
        'followers': 0.3,
        'mutual': 0.4
    }
    
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        debug: bool = False,
        cache_dir: Union[str, Path] = 'cache',
        output_dir: Union[str, Path] = 'output',
        manual_auth: bool = False
    ):
        """
        Initialize the analyzer with enhanced configuration.
        
        Args:
            username: LinkedIn username (optional if using env vars)
            password: LinkedIn password (optional if using env vars)
            debug: Enable debug logging
            cache_dir: Directory for caching data
            output_dir: Directory for analysis output
            manual_auth: Enable manual authentication
        """
        self.debug = debug
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.manual_auth = manual_auth
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Load credentials
        self._load_credentials(username, password)
        
        # Create required directories
        self._setup_directories()
        
        # Initialize metrics
        self.metrics = NetworkMetrics()
        self.start_time = time.time()
        
        # Initialize API components
        try:
            self._initialize_api()
        except Exception as e:
            self.logger.error(f"Failed to initialize analyzer: {str(e)}")
            raise LinkedInAnalyzerError(f"Initialization failed: {str(e)}")

    def _setup_logger(self) -> logging.Logger:
        """Configure enhanced logging system."""
        logger = logging.getLogger('LinkedInAnalyzer')
        logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        
        if not logger.handlers:
            # Create logs directory
            log_dir = Path('logs')
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Configure file handler
            log_file = log_dir / f'linkedin_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(file_handler)
            
            # Configure console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter('%(message)s'))
            logger.addHandler(console_handler)
        
        return logger

    def _load_credentials(
        self,
        username: Optional[str],
        password: Optional[str]
    ) -> None:
        """Load and validate credentials."""
        from dotenv import load_dotenv
        load_dotenv()
        
        self.username = username or os.getenv('LINKEDIN_USERNAME')
        self.password = password or os.getenv('LINKEDIN_PASSWORD')
        
        if not all([self.username, self.password]):
            raise LinkedInAnalyzerError(
                "LinkedIn credentials not found. Provide them directly or "
                "set LINKEDIN_USERNAME and LINKEDIN_PASSWORD environment variables."
            )

    def _setup_directories(self) -> None:
        """Create and validate required directories."""
        directories = [self.cache_dir, self.output_dir, Path('logs')]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                
                # Validate write permissions
                test_file = directory / '.test'
                test_file.touch()
                test_file.unlink()
                
            except Exception as e:
                raise LinkedInAnalyzerError(f"Cannot access directory {directory}: {str(e)}")

    def _initialize_api(self) -> None:
        """Initialize API components with proper authentication."""
        try:
            # Initialize authenticator
            self.authenticator = LinkedInAuthenticator(
                force_manual_auth=self.manual_auth
            )
            
            # Get authentication cookies
            cookies = self.authenticator.get_cookies()
            
            if not cookies:
                raise LinkedInAnalyzerError("Failed to obtain authentication cookies")
            
            # Initialize API wrapper
            self.api = LinkedInWrapper(
                username=self.username,
                password=self.password,
                debug=self.debug,
                cookies=cookies,
                authenticator=self.authenticator
            )
            
            # Validate connection
            if not self._validate_connection():
                raise LinkedInAnalyzerError("Failed to validate API connection")
                
        except Exception as e:
            self.logger.error(f"API initialization failed: {str(e)}")
            raise LinkedInAnalyzerError(f"API initialization failed: {str(e)}")

    def _validate_connection(self) -> bool:
        """Validate API connection with retry logic."""
        for attempt in range(self.MAX_RETRIES):
            try:
                if self.api.session_valid:
                    return True
                    
                if attempt < self.MAX_RETRIES - 1:
                    self.logger.warning(
                        f"Connection validation attempt {attempt + 1} failed, retrying..."
                    )
                    time.sleep(2 ** attempt)
                    
            except Exception as e:
                self.logger.warning(f"Validation error: {str(e)}")
                if attempt == self.MAX_RETRIES - 1:
                    return False
                    
        return False
    
    """
    LinkedIn Network Analyzer - Part 2: Network Analysis

    This module implements core network analysis functionality:
    - Connection analysis
    - Network metrics calculation
    - Pattern detection
    """

    def analyze_network(self) -> Dict[str, Any]:
        """
        Perform comprehensive network analysis.
        
        Returns:
            Complete analysis results dictionary
            
        Raises:
            NetworkAnalysisError: If analysis fails
        """
        try:
            self.logger.info("Starting comprehensive network analysis...")
            start_time = time.time()
            
            # Get current user's profile
            user_profile = self.api.get_user_profile()
            if not user_profile:
                raise NetworkAnalysisError("Failed to retrieve user profile")
            
            # Fetch network data
            connections = self._get_connections(user_profile)
            self.metrics.total_connections = len(connections)
            
            # Get follower information
            try:
                profile_id = self._extract_profile_id(user_profile)
                follower_info = self._get_follower_info(profile_id)
                
                # Update metrics
                self.metrics.total_followers = follower_info.get('follower_count', 0)
                self.metrics.mutual_connections = follower_info.get('mutual_connections_count', 0)
                
            except Exception as e:
                self.logger.warning(f"Follower analysis failed: {str(e)}")
                follower_info = {}
            
            # Analyze relationships and patterns
            relationship_data = self._analyze_relationships(connections)
            network_patterns = self._analyze_network_patterns(connections, follower_info)
            
            # Calculate engagement metrics
            engagement_metrics = self._calculate_engagement_metrics(
                connections=connections,
                follower_info=follower_info,
                relationship_data=relationship_data
            )
            
            # Calculate execution time
            self.metrics.execution_time = time.time() - start_time
            
            # Compile results
            results = {
                "user_profile": user_profile,
                "network_composition": {
                    "connections": self.metrics.total_connections,
                    "followers": self.metrics.total_followers,
                    "mutual_connections": self.metrics.mutual_connections
                },
                "relationship_data": relationship_data,
                "network_patterns": network_patterns,
                "engagement_metrics": engagement_metrics,
                "metrics": self.metrics.to_dict()
            }
            
            # Save analysis results
            self._save_analysis_results(results)
            
            self.logger.info("Network analysis completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Network analysis failed: {str(e)}")
            raise NetworkAnalysisError(f"Analysis failed: {str(e)}")

    def _get_connections(
        self,
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Fetch and process user connections.
        
        Args:
            user_profile: User profile data
            
        Returns:
            List of processed connections
        """
        try:
            self.logger.info("Fetching network connections...")
            
            profile_id = self._extract_profile_id(user_profile)
            connections = []
            
            # Fetch connections with pagination
            start = 0
            while True:
                batch = self.api.get_profile_connections(
                    profile_id,
                    start=start,
                    count=self.BATCH_SIZE
                )
                
                if not batch:
                    break
                    
                connections.extend(batch)
                
                if len(batch) < self.BATCH_SIZE:
                    break
                    
                start += self.BATCH_SIZE
                
            self.logger.info(f"Found {len(connections)} connections")
            
            # Process connections
            processed_connections = []
            for conn in connections:
                try:
                    processed = {
                        'urn_id': conn.get('urn_id'),
                        'name': conn.get('name'),
                        'headline': conn.get('headline'),
                        'industry': conn.get('industry'),
                        'location': conn.get('location'),
                        'public_id': conn.get('public_id'),
                        'picture_url': conn.get('picture_url')
                    }
                    
                    if processed['urn_id'] and processed['name']:
                        processed_connections.append(processed)
                        
                except Exception as e:
                    self.logger.debug(f"Error processing connection: {str(e)}")
                    continue
                    
            return processed_connections
            
        except Exception as e:
            self.logger.error(f"Failed to get connections: {str(e)}")
            raise NetworkAnalysisError(f"Connection retrieval failed: {str(e)}")

    def _get_follower_info(
        self,
        profile_id: str
    ) -> Dict[str, Any]:
        """
        Fetch follower information with enhanced error handling.
        
        Args:
            profile_id: Profile identifier
            
        Returns:
            Follower information dictionary
        """
        try:
            self.logger.info("Fetching follower information...")
            
            # Clean profile ID
            clean_id = self._clean_profile_id(profile_id)
            
            # Get network information
            network_info = self.api.get_profile_network_info(
                clean_id,
                include_connections=False
            )
            
            if not network_info:
                raise NetworkAnalysisError("No network information returned")
            
            # Extract relevant data
            follower_info = {
                'follower_count': network_info.get('followers_count', 0),
                'following_count': network_info.get('following_count', 0),
                'mutual_connections_count': network_info.get('mutual_connections_count', 0),
                'network_distance': network_info.get('network_distance', ''),
                'is_followable': network_info.get('is_followable', False)
            }
            
            # Validate information
            if not self._validate_follower_info(follower_info):
                raise NetworkAnalysisError("Invalid follower information received")
            
            self.logger.info(
                f"Retrieved follower information: "
                f"{follower_info['follower_count']} followers"
            )
            return follower_info
            
        except Exception as e:
            self.logger.error(f"Failed to fetch follower information: {str(e)}")
            raise NetworkAnalysisError(f"Follower information retrieval failed: {str(e)}")

    def _analyze_relationships(
        self,
        connections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze network relationships and patterns.
        
        Args:
            connections: List of network connections
            
        Returns:
            Relationship analysis results
        """
        try:
            self.logger.info("Analyzing network relationships...")
            
            # Initialize pattern containers
            patterns = {
                'locations': {},
                'industries': {},
                'companies': {},
                'roles': {}
            }
            
            # Process each connection
            for conn in connections:
                # Process location
                location = conn.get('location', 'Unknown')
                patterns['locations'][location] = patterns['locations'].get(location, 0) + 1
                
                # Process industry
                industry = conn.get('industry', 'Unknown')
                patterns['industries'][industry] = patterns['industries'].get(industry, 0) + 1
                
                # Extract and process company/role
                if conn.get('headline'):
                    company = self._extract_company(conn['headline'])
                    if company:
                        patterns['companies'][company] = patterns['companies'].get(company, 0) + 1
                    
                    role = self._extract_role(conn['headline'])
                    if role:
                        patterns['roles'][role] = patterns['roles'].get(role, 0) + 1
            
            # Calculate unique counts
            self.metrics.unique_locations = len(patterns['locations'])
            self.metrics.unique_industries = len(patterns['industries'])
            self.metrics.unique_companies = len(patterns['companies'])
            
            # Calculate relationship strengths
            relationship_strengths = self._calculate_relationship_strengths(patterns)
            
            return {
                'patterns': patterns,
                'strengths': relationship_strengths,
                'summary': self._generate_pattern_summary(patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze relationships: {str(e)}")
            raise NetworkAnalysisError(f"Relationship analysis failed: {str(e)}")
        
    """
    LinkedIn Network Analyzer - Part 3: Metrics and Pattern Analysis

    This module implements:
    - Advanced metrics calculation
    - Pattern detection
    - Network analysis algorithms
    """

    def _calculate_engagement_metrics(
        self,
        connections: List[Dict[str, Any]],
        follower_info: Dict[str, Any],
        relationship_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive engagement metrics.
        
        Args:
            connections: List of network connections
            follower_info: Follower information
            relationship_data: Relationship analysis data
            
        Returns:
            Engagement metrics dictionary
        """
        try:
            # Calculate base metrics
            total_network = len(connections)
            total_followers = follower_info.get('follower_count', 0)
            mutual_count = follower_info.get('mutual_connections_count', 0)
            
            if total_network == 0:
                return self._get_default_metrics()
                
            # Calculate ratios
            follower_ratio = total_followers / total_network if total_network > 0 else 0
            mutual_ratio = mutual_count / total_network if total_network > 0 else 0
            
            # Calculate network density
            possible_connections = (total_network * (total_network - 1)) / 2
            actual_connections = sum(
                len(group) for group in relationship_data['patterns'].values()
            )
            network_density = actual_connections / possible_connections if possible_connections > 0 else 0
            
            # Calculate engagement score using weighted factors
            engagement_score = (
                (mutual_ratio * self.METRIC_WEIGHTS['mutual']) +
                (follower_ratio * self.METRIC_WEIGHTS['followers'])
            )
            
            # Calculate network reach
            reach_score = self._calculate_network_reach(
                total_network=total_network,
                mutual_count=mutual_count,
                relationship_data=relationship_data
            )
            
            # Update metrics object
            self.metrics.engagement_rate = engagement_score
            self.metrics.network_density = network_density
            
            return {
                'basic_metrics': {
                    'follower_ratio': round(follower_ratio, 3),
                    'mutual_ratio': round(mutual_ratio, 3),
                    'network_density': round(network_density, 3)
                },
                'advanced_metrics': {
                    'engagement_score': round(engagement_score, 3),
                    'network_reach': round(reach_score, 3)
                },
                'network_quality': {
                    'connection_diversity': self._calculate_diversity_score(relationship_data),
                    'relationship_strength': self._calculate_relationship_score(relationship_data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate engagement metrics: {str(e)}")
            return self._get_default_metrics()

    def _analyze_network_patterns(
        self,
        connections: List[Dict[str, Any]],
        follower_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze network patterns and trends.
        
        Args:
            connections: List of network connections
            follower_info: Follower information
            
        Returns:
            Pattern analysis results
        """
        try:
            # Initialize pattern containers
            patterns = {
                'industry_clusters': {},
                'location_clusters': {},
                'role_hierarchies': {},
                'company_relationships': {}
            }
            
            # Analyze industry clusters
            for conn in connections:
                industry = conn.get('industry', 'Unknown')
                if industry != 'Unknown':
                    if industry not in patterns['industry_clusters']:
                        patterns['industry_clusters'][industry] = {
                            'count': 0,
                            'connections': [],
                            'roles': set()
                        }
                    
                    patterns['industry_clusters'][industry]['count'] += 1
                    patterns['industry_clusters'][industry]['connections'].append(conn['urn_id'])
                    
                    if conn.get('headline'):
                        role = self._extract_role(conn['headline'])
                        if role:
                            patterns['industry_clusters'][industry]['roles'].add(role)
            
            # Analyze location patterns
            for conn in connections:
                location = conn.get('location', 'Unknown')
                if location != 'Unknown':
                    if location not in patterns['location_clusters']:
                        patterns['location_clusters'][location] = {
                            'count': 0,
                            'industries': set(),
                            'connections': []
                        }
                    
                    patterns['location_clusters'][location]['count'] += 1
                    patterns['location_clusters'][location]['connections'].append(conn['urn_id'])
                    
                    if conn.get('industry'):
                        patterns['location_clusters'][location]['industries'].add(conn['industry'])
            
            # Analyze role hierarchies
            for conn in connections:
                if conn.get('headline'):
                    role = self._extract_role(conn['headline'])
                    seniority = self._extract_seniority(conn['headline'])
                    
                    if role and seniority:
                        key = f"{seniority}_{role}"
                        if key not in patterns['role_hierarchies']:
                            patterns['role_hierarchies'][key] = {
                                'count': 0,
                                'connections': [],
                                'industries': set()
                            }
                        
                        patterns['role_hierarchies'][key]['count'] += 1
                        patterns['role_hierarchies'][key]['connections'].append(conn['urn_id'])
                        
                        if conn.get('industry'):
                            patterns['role_hierarchies'][key]['industries'].add(conn['industry'])
            
            # Analyze company relationships
            for conn in connections:
                if conn.get('headline'):
                    company = self._extract_company(conn['headline'])
                    if company:
                        if company not in patterns['company_relationships']:
                            patterns['company_relationships'][company] = {
                                'count': 0,
                                'connections': [],
                                'roles': set(),
                                'industries': set()
                            }
                        
                        patterns['company_relationships'][company]['count'] += 1
                        patterns['company_relationships'][company]['connections'].append(conn['urn_id'])
                        
                        role = self._extract_role(conn['headline'])
                        if role:
                            patterns['company_relationships'][company]['roles'].add(role)
                        
                        if conn.get('industry'):
                            patterns['company_relationships'][company]['industries'].add(conn['industry'])
            
            return {
                'patterns': patterns,
                'insights': self._generate_pattern_insights(patterns),
                'recommendations': self._generate_network_recommendations(patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze network patterns: {str(e)}")
            return {}

    def _calculate_relationship_strengths(
        self,
        patterns: Dict[str, Dict[str, int]]
    ) -> Dict[str, float]:
        """
        Calculate relationship strength metrics.
        
        Args:
            patterns: Network pattern data
            
        Returns:
            Relationship strength metrics
        """
        try:
            total_connections = sum(
                len(group['connections']) 
                for groups in patterns.values() 
                for group in groups.values()
            )
            
            if total_connections == 0:
                return {}
                
            strengths = {}
            
            # Calculate industry strength
            industry_connections = sum(
                group['count'] for group in patterns['industry_clusters'].values()
            )
            strengths['industry_strength'] = industry_connections / total_connections
            
            # Calculate location strength
            location_connections = sum(
                group['count'] for group in patterns['location_clusters'].values()
            )
            strengths['location_strength'] = location_connections / total_connections
            
            # Calculate role strength
            role_connections = sum(
                group['count'] for group in patterns['role_hierarchies'].values()
            )
            strengths['role_strength'] = role_connections / total_connections
            
            # Calculate company strength
            company_connections = sum(
                group['count'] for group in patterns['company_relationships'].values()
            )
            strengths['company_strength'] = company_connections / total_connections
            
            # Calculate overall strength
            strengths['overall_strength'] = (
                strengths['industry_strength'] * 0.3 +
                strengths['location_strength'] * 0.2 +
                strengths['role_strength'] * 0.25 +
                strengths['company_strength'] * 0.25
            )
            
            return {k: round(v, 3) for k, v in strengths.items()}
            
        except Exception as e:
            self.logger.error(f"Failed to calculate relationship strengths: {str(e)}")
            return {}

    def _calculate_diversity_score(
        self,
        relationship_data: Dict[str, Any]
    ) -> float:
        """
        Calculate network diversity score.
        
        Args:
            relationship_data: Relationship analysis data
            
        Returns:
            Diversity score between 0 and 1
        """
        try:
            patterns = relationship_data.get('patterns', {})
            if not patterns:
                return 0.0
                
            # Calculate diversity components
            industry_diversity = len(patterns['industry_clusters']) / max(
                sum(g['count'] for g in patterns['industry_clusters'].values()), 1
            )
            
            location_diversity = len(patterns['location_clusters']) / max(
                sum(g['count'] for g in patterns['location_clusters'].values()), 1
            )
            
            role_diversity = len(patterns['role_hierarchies']) / max(
                sum(g['count'] for g in patterns['role_hierarchies'].values()), 1
            )
            
            # Weight and combine scores
            diversity_score = (
                industry_diversity * 0.4 +
                location_diversity * 0.3 +
                role_diversity * 0.3
            )
            
            return round(diversity_score, 3)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate diversity score: {str(e)}")
            return 0.0

    def _calculate_network_reach(
        self,
        total_network: int,
        mutual_count: int,
        relationship_data: Dict[str, Any]
    ) -> float:
        """
        Calculate network reach score.
        
        Args:
            total_network: Total network size
            mutual_count: Number of mutual connections
            relationship_data: Relationship analysis data
            
        Returns:
            Network reach score between 0 and 1
        """
        try:
            # Calculate size factor
            if total_network <= self.NETWORK_THRESHOLDS['small']:
                size_factor = 0.5
            elif total_network <= self.NETWORK_THRESHOLDS['medium']:
                size_factor = 0.75
            elif total_network <= self.NETWORK_THRESHOLDS['large']:
                size_factor = 0.9
            else:
                size_factor = 1.0
                
            # Calculate quality factor
            quality_factor = mutual_count / total_network if total_network > 0 else 0
            
            # Calculate diversity factor
            diversity_factor = self._calculate_diversity_score(relationship_data)
            
            # Combine factors with weights
            reach_score = (
                size_factor * 0.4 +
                quality_factor * 0.3 +
                diversity_factor * 0.3
            )
            
            return round(reach_score, 3)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate network reach: {str(e)}")
            return 0.0
        
    """
    LinkedIn Network Analyzer - Part 4: Data Processing and Utilities

    This module implements:
    - Data extraction and cleaning
    - Information processing
    - Utility functions
    - File handling
    """

    def _clean_profile_id(self, profile_id: str) -> str:
        """
        Clean and standardize profile identifiers.
        
        Args:
            profile_id: Raw profile identifier
            
        Returns:
            Cleaned profile ID
        
        Raises:
            ValueError: If profile ID is invalid
        """
        if not profile_id:
            raise ValueError("Profile ID cannot be empty")
            
        # Handle URN format
        if 'urn:li:' in profile_id:
            parts = profile_id.split(':')
            return parts[-1]
            
        # Handle fs_miniProfile format
        if 'fs_' in profile_id:
            parts = profile_id.split('_')
            return parts[-1]
            
        return profile_id.strip()

    def _extract_company(self, headline: str) -> Optional[str]:
        """
        Extract company name from headline/title.
        
        Args:
            headline: LinkedIn headline string
            
        Returns:
            Company name if found, None otherwise
        """
        try:
            if not headline:
                return None
                
            # Common company indicators
            indicators = ['at', '@', 'for', 'with']
            
            headline_lower = headline.lower()
            
            for indicator in indicators:
                if indicator in headline_lower:
                    parts = headline_lower.split(indicator)
                    if len(parts) > 1:
                        company = parts[1].strip()
                        
                        # Clean up common separators
                        for sep in ['|', '-', '•', '/', '\\']:
                            if sep in company:
                                company = company.split(sep)[0].strip()
                        
                        return company.title() if company else None
                        
            return None
            
        except Exception as e:
            self.logger.debug(f"Company extraction failed for '{headline}': {str(e)}")
            return None

    def _extract_role(self, headline: str) -> Optional[str]:
        """
        Extract professional role with pattern matching.
        
        Args:
            headline: LinkedIn headline string
            
        Returns:
            Role title if found, None otherwise
        """
        try:
            if not headline:
                return None
                
            headline_lower = headline.lower()
            
            # Role patterns dictionary
            role_patterns = {
                'engineer': ['engineer', 'engineering', 'developer', 'architect'],
                'manager': ['manager', 'management', 'head of', 'lead'],
                'director': ['director', 'directeur'],
                'executive': ['ceo', 'cto', 'cfo', 'chief', 'vp', 'president'],
                'consultant': ['consultant', 'consulting', 'advisor'],
                'analyst': ['analyst', 'analytics', 'research'],
                'designer': ['designer', 'design', 'ux', 'ui'],
                'sales': ['sales', 'account', 'business development'],
                'marketing': ['marketing', 'brand', 'growth', 'content'],
                'product': ['product', 'program', 'project'],
                'operations': ['operations', 'ops', 'operational'],
                'hr': ['hr', 'human resources', 'talent', 'recruiting']
            }
            
            for role_category, patterns in role_patterns.items():
                for pattern in patterns:
                    if pattern in headline_lower:
                        # Find complete phrase around role
                        pattern_pos = headline_lower.find(pattern)
                        
                        # Get context before role
                        start_pos = max(0, pattern_pos - 30)
                        prefix = headline_lower[start_pos:pattern_pos].strip()
                        
                        # Get context after role
                        end_pos = min(len(headline_lower), pattern_pos + len(pattern) + 30)
                        suffix = headline_lower[pattern_pos:end_pos].strip()
                        
                        # Combine and clean
                        role_phrase = (prefix + " " + suffix).strip()
                        
                        # Remove company information
                        for sep in ['at', 'for', 'with', '|', '-', '@']:
                            if sep in role_phrase:
                                role_phrase = role_phrase.split(sep)[0].strip()
                        
                        return role_phrase.title()
                        
            return None
            
        except Exception as e:
            self.logger.debug(f"Role extraction failed for '{headline}': {str(e)}")
            return None

    def _extract_seniority(self, headline: str) -> Optional[str]:
        """
        Extract seniority level from headline.
        
        Args:
            headline: LinkedIn headline string
            
        Returns:
            Seniority level if found, None otherwise
        """
        try:
            if not headline:
                return None
                
            headline_lower = headline.lower()
            
            # Seniority patterns
            seniority_patterns = {
                'entry': ['junior', 'entry level', 'associate'],
                'mid': ['mid level', 'intermediate', 'regular'],
                'senior': ['senior', 'sr', 'lead'],
                'manager': ['manager', 'head', 'director'],
                'executive': ['chief', 'cxo', 'vp', 'president', 'founder']
            }
            
            for level, patterns in seniority_patterns.items():
                if any(p in headline_lower for p in patterns):
                    return level
                    
            return None
            
        except Exception as e:
            self.logger.debug(f"Seniority extraction failed for '{headline}': {str(e)}")
            return None

    def _get_default_metrics(self) -> Dict[str, float]:
        """
        Get default metrics for error cases.
        
        Returns:
            Default metrics dictionary
        """
        return {
            'basic_metrics': {
                'follower_ratio': 0.0,
                'mutual_ratio': 0.0,
                'network_density': 0.0
            },
            'advanced_metrics': {
                'engagement_score': 0.0,
                'network_reach': 0.0
            },
            'network_quality': {
                'connection_diversity': 0.0,
                'relationship_strength': 0.0
            }
        }

    def _validate_follower_info(self, follower_info: Dict[str, Any]) -> bool:
        """
        Validate follower information completeness.
        
        Args:
            follower_info: Follower information dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            required_fields = {
                'follower_count',
                'following_count',
                'mutual_connections_count',
                'network_distance'
            }
            
            # Check required fields
            if not all(field in follower_info for field in required_fields):
                return False
                
            # Validate numeric fields
            numeric_fields = ['follower_count', 'following_count', 'mutual_connections_count']
            for field in numeric_fields:
                value = follower_info.get(field)
                if not isinstance(value, (int, float)) or value < 0:
                    return False
                    
            return True
            
        except Exception:
            return False

    def _extract_profile_id(self, profile: Dict[str, Any]) -> str:
        """
        Extract profile ID from profile data.
        
        Args:
            profile: Profile data dictionary
            
        Returns:
            Profile ID string
            
        Raises:
            ValueError: If no valid ID found
        """
        try:
            # Try all possible ID fields
            possible_ids = [
                ('entityUrn', profile.get('entityUrn')),
                ('profile_urn', profile.get('profile_urn')),
                ('profile_id', profile.get('profile_id')),
                ('public_id', profile.get('public_id')),
                ('miniProfile', profile.get('miniProfile', {}).get('entityUrn'))
            ]
            
            for field_name, value in possible_ids:
                if value:
                    clean_id = self._clean_profile_id(value)
                    if clean_id:
                        self.logger.debug(f"Using {field_name} as profile identifier: {clean_id}")
                        return clean_id
                        
            raise ValueError("No valid profile ID found")
            
        except Exception as e:
            raise ValueError(f"Failed to extract profile ID: {str(e)}")

    def _save_analysis_results(self, results: Dict[str, Any]) -> None:
        """
        Save analysis results to files.
        
        Args:
            results: Analysis results dictionary
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save complete results as JSON
            with open(self.output_dir / f'network_analysis_{timestamp}.json', 'w') as f:
                json.dump(results, f, indent=2)
                
            # Save metrics summary as CSV
            metrics_df = pd.DataFrame([results['metrics']])
            metrics_df.to_csv(
                self.output_dir / f'network_metrics_{timestamp}.csv',
                index=False
            )
            
            # Save pattern analysis
            if 'network_patterns' in results:
                patterns_file = self.output_dir / f'network_patterns_{timestamp}.json'
                with open(patterns_file, 'w') as f:
                    json.dump(results['network_patterns'], f, indent=2)
                    
            self.logger.info(f"Analysis results saved to {self.output_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to save analysis results: {str(e)}")
            raise DataProcessingError(f"Could not save results: {str(e)}")
        
    """
    LinkedIn Network Analyzer - Part 5: CLI and Main Execution

    This module implements:
    - Command-line interface
    - Main execution flow
    - Progress tracking
    - Result presentation
    """

    import sys
    import argparse
    from pathlib import Path
    from typing import Optional, Dict, Any
    from tqdm import tqdm

    def analyze_and_present(
        self,
        show_progress: bool = True,
        output_format: str = 'both'
    ) -> Dict[str, Any]:
        """
        Analyze network and present results.
        
        Args:
            show_progress: Show progress bars
            output_format: Output format ('console', 'file', or 'both')
            
        Returns:
            Analysis results dictionary
        """
        try:
            print("\n🔍 LinkedIn Network Analyzer")
            print("========================")
            
            if show_progress:
                # Define analysis stages
                stages = [
                    "Authentication",
                    "Profile Analysis",
                    "Connection Analysis",
                    "Follower Analysis",
                    "Pattern Detection",
                    "Metrics Calculation",
                    "Report Generation"
                ]
                
                results = None
                with tqdm(total=len(stages), desc="Overall Progress") as pbar:
                    try:
                        # Stage 1: Authentication
                        pbar.set_description("Authenticating")
                        if not self._validate_connection():
                            raise NetworkAnalysisError("Authentication failed")
                        pbar.update(1)
                        
                        # Stage 2-6: Core Analysis
                        pbar.set_description("Analyzing Network")
                        results = self.analyze_network()
                        pbar.update(5)
                        
                        # Stage 7: Report Generation
                        pbar.set_description("Generating Report")
                        self._present_results(results, output_format)
                        pbar.update(1)
                        
                    except Exception as e:
                        self.logger.error(f"Analysis failed: {str(e)}")
                        raise
            else:
                # Execute without progress bars
                results = self.analyze_network()
                self._present_results(results, output_format)
                
            return results
            
        except Exception as e:
            self.logger.error(f"Analysis execution failed: {str(e)}")
            raise

    def _present_results(
        self,
        results: Dict[str, Any],
        output_format: str = 'both'
    ) -> None:
        """
        Present analysis results in specified format.
        
        Args:
            results: Analysis results dictionary
            output_format: Desired output format
        """
        if not results:
            print("\n❌ No analysis results to present")
            return
            
        # Console output
        if output_format in ['console', 'both']:
            self._print_console_report(results)
            
        # File output
        if output_format in ['file', 'both']:
            self._save_analysis_results(results)

    def _print_console_report(self, results: Dict[str, Any]) -> None:
        """
        Print formatted analysis report to console.
        
        Args:
            results: Analysis results dictionary
        """
        print("\n📊 Network Analysis Results")
        print("=======================")
        
        # Network Size
        metrics = results['metrics']['network_size']
        print("\n🌐 Network Composition")
        print(f"• Total Connections: {metrics['total_connections']:,}")
        print(f"• Total Followers: {metrics['total_followers']:,}")
        print(f"• Mutual Connections: {metrics['mutual_connections']:,}")
        
        # Network Quality
        engagement = results['metrics']['engagement_metrics']
        print("\n📈 Engagement Metrics")
        print(f"• Follower Ratio: {engagement['follower_ratio']}")
        print(f"• Network Reach: {engagement['network_reach']}")
        
        # Patterns
        if 'network_patterns' in results:
            patterns = results['network_patterns']
            print("\n🔍 Key Patterns")
            
            # Industry patterns
            if 'industry_clusters' in patterns['patterns']:
                top_industries = sorted(
                    patterns['patterns']['industry_clusters'].items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:5]
                
                print("\nTop Industries:")
                for industry, data in top_industries:
                    print(f"• {industry}: {data['count']} connections")
                    
            # Location patterns
            if 'location_clusters' in patterns['patterns']:
                top_locations = sorted(
                    patterns['patterns']['location_clusters'].items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:5]
                
                print("\nTop Locations:")
                for location, data in top_locations:
                    print(f"• {location}: {data['count']} connections")
        
        # Execution Info
        execution = results['metrics']['execution_metrics']
        print(f"\n⏱️  Execution time: {execution['execution_time']}")
        print(f"📅 Analysis date: {execution['analysis_date']}")
        
        # File locations
        print("\n📁 Detailed Results")
        print(f"• Complete Analysis: {self.output_dir}/network_analysis_*.json")
        print(f"• Metrics Summary: {self.output_dir}/network_metrics_*.csv")
        print(f"• Pattern Analysis: {self.output_dir}/network_patterns_*.json")

def main() -> None:
    """Main CLI execution function."""
    parser = argparse.ArgumentParser(
        description="LinkedIn Network Analyzer CLI"
    )
    
    parser.add_argument(
        "--username",
        help="LinkedIn username (or set LINKEDIN_USERNAME env var)"
    )
    parser.add_argument(
        "--password",
        help="LinkedIn password (or set LINKEDIN_PASSWORD env var)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory for analysis results"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="cache",
        help="Cache directory for temporary data"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--manual-auth",
        action="store_true",
        help="Use manual authentication"
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars"
    )
    parser.add_argument(
        "--output-format",
        choices=['console', 'file', 'both'],
        default='both',
        help="Output format for results"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = LinkedInAnalyzer(
            username=args.username,
            password=args.password,
            debug=args.debug,
            cache_dir=args.cache_dir,
            output_dir=args.output_dir,
            manual_auth=args.manual_auth
        )
        
        # Run analysis
        analyzer.analyze_and_present(
            show_progress=not args.no_progress,
            output_format=args.output_format
        )
        
        print("\n✅ Analysis completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()