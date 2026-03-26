"""
LinkedIn Wrapper Module - Part 1: Core Implementation

This module provides a robust wrapper around the LinkedIn API with:
- Improved error handling
- Standardized request handling
- Enhanced session management
- Better type safety
"""

import time
import json
import uuid
import random
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Literal, TypeVar, cast, Type
from types import TracebackType

import requests
from requests.exceptions import RequestException, JSONDecodeError
from linkedin_api import Linkedin
from .linkedin_authenticator import LinkedInAuthenticator
from src.config import AppConfig

T = TypeVar('T')

class LinkedInAPIError(Exception):
    """Base exception for API errors"""
    pass

class RateLimitError(LinkedInAPIError):
    """Raised when rate limits are hit"""
    pass

class AuthenticationError(LinkedInAPIError):
    """Raised for authentication failures"""
    pass

class LinkedInWrapper:
    """
    Enhanced LinkedIn API wrapper with improved reliability and standardization.
    """
    
    # API Constants
    BASE_URL = "https://www.linkedin.com/voyager/api"
    API_VERSION = "v2"
    
    # Request Configuration
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    
    # Rate limiting - these will be loaded from config
    DEFAULT_MIN_DELAY = 2
    DEFAULT_MAX_DELAY = 5
    DEFAULT_RATE_LIMIT_DELAY = 60
    
    # Batch Processing
    BATCH_SIZE = 50
    MAX_BATCH_RETRIES = 3
    
    def __init__(
        self,
        username: str,
        password: str,
        *,
        debug: bool = False,
        refresh_cookies: bool = False,
        max_retries: Optional[int] = None,
        min_delay: Optional[int] = None,
        max_delay: Optional[int] = None,
        cookies: Optional[List[Dict]] = None,
        authenticator: Optional[LinkedInAuthenticator] = None
    ):
        """
        Initialize the LinkedIn API wrapper.
        
        Args:
            username: LinkedIn account username
            password: LinkedIn account password
            debug: Enable debug logging
            refresh_cookies: Force cookie refresh
            max_retries: Override default retry count
            min_delay: Override minimum request delay
            max_delay: Override maximum request delay
            cookies: Pre-existing authentication cookies
            authenticator: Optional authenticator instance
        """
        # Load configuration
        try:
            config = AppConfig()
            rate_config = config.rate_limit
        except Exception as e:
            logging.warning(f"Failed to load rate limiting configuration: {e}")
            # Create default rate limit config
            from dataclasses import dataclass
            @dataclass
            class DefaultRateLimitConfig:
                min_delay: float = self.DEFAULT_MIN_DELAY
                max_delay: float = self.DEFAULT_MAX_DELAY
                penalty_delay: int = self.DEFAULT_RATE_LIMIT_DELAY
                max_requests_per_minute: int = 20
                max_requests_per_hour: int = 100
                max_requests_per_day: int = 1000
                conservative_mode: bool = False
                
            rate_config = DefaultRateLimitConfig()
        
        # Configuration
        self.username = username
        self.password = password
        self.debug = debug
        self.max_retries = max_retries or self.MAX_RETRIES
        
        # Rate limiting configuration
        self.min_delay = min_delay or rate_config.min_delay
        self.max_delay = max_delay or rate_config.max_delay
        self.rate_limit_delay = rate_config.penalty_delay
        self.max_requests_per_minute = rate_config.max_requests_per_minute
        self.max_requests_per_hour = rate_config.max_requests_per_hour
        self.max_requests_per_day = rate_config.max_requests_per_day
        self.conservative_mode = rate_config.conservative_mode
        
        # Setup logging
        self._setup_logging()
        
        # Initialize authenticator
        self.authenticator = authenticator or LinkedInAuthenticator(
            debug=debug
        )
        
        # Initialize API with retry logic
        self.api = self._initialize_api(
            username=username,
            password=password, 
            debug=debug,
            refresh_cookies=refresh_cookies,
            cookies=cookies
        )

    def _setup_logging(self) -> None:
        """Configure logging for the wrapper."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _initialize_api(
        self,
        username: str,
        password: str,
        debug: bool,
        refresh_cookies: bool,
        cookies: Optional[List[Dict]] = None
    ) -> Linkedin:
        """
        Initialize LinkedIn API with enhanced error handling.
        
        Args:
            username: LinkedIn username
            password: LinkedIn password
            debug: Enable debug mode
            refresh_cookies: Force cookie refresh
            cookies: Optional existing cookies
            
        Returns:
            Initialized LinkedIn API client
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            self.logger.info("Initializing LinkedIn API...")
            
            # Initialize API without authentication first
            api = Linkedin(
                username=username,
                password=password,
                debug=debug,
                refresh_cookies=False,
                authenticate=False
            )
            
            # Get fresh cookies if needed
            if not cookies or refresh_cookies:
                cookies = self.authenticator.get_cookies()
                
            if not cookies:
                raise AuthenticationError("Failed to obtain authentication cookies")
            
            # Setup session with cookies
            session = self._setup_session(cookies)
            
            # Attach session to API
            api.client.session = session
            
            # Verify the session works
            if not self._validate_session(api):
                raise AuthenticationError("Failed to verify API session")
            
            self.logger.info("Successfully initialized LinkedIn API")
            return api
            
        except Exception as e:
            self.logger.error(f"API initialization failed: {str(e)}")
            raise AuthenticationError(f"Failed to initialize API: {str(e)}")

    def _setup_session(self, cookies: List[Dict[str, Any]]) -> requests.Session:
        """
        Configure requests session with proper headers and cookies.
        
        Args:
            cookies: Authentication cookies to use
            
        Returns:
            Configured requests Session
        """
        session = requests.Session()
        
        # Set cookies
        for cookie in cookies:
            session.cookies.set(
                cookie['name'],
                cookie['value'],
                domain=cookie.get('domain', '.linkedin.com'),
                path=cookie.get('path', '/')
            )
        
        # Set standard headers
        session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': 'application/vnd.linkedin.normalized+json+2.1',
            'Accept-Language': 'en-US,en;q=0.9',
            'x-li-lang': 'en_US',
            'x-restli-protocol-version': '2.0.0'
        })
        
        # Set CSRF token
        jsessionid = session.cookies.get('JSESSIONID')
        if jsessionid:
            session.headers['csrf-token'] = jsessionid.strip('"')
        
        return session

    def _validate_session(self, api: Linkedin) -> bool:
        """
        Verify if the API session is valid.
        
        Args:
            api: LinkedIn API instance to validate
            
        Returns:
            True if session is valid
        """
        try:
            response = api._fetch(
                "/me",
                headers={'accept': 'application/vnd.linkedin.normalized+json+2.1'}
            )
            
            self.logger.debug(f"Session validation status: {response.status_code}")
            return response.status_code == 200
            
        except Exception as e:
            self.logger.warning(f"Session validation failed: {str(e)}")
            return False
        
    """
    LinkedIn Wrapper Module - Part 2: Request Handling

    This section implements the core request handling functionality:
    - Request execution with retry logic
    - Rate limiting
    - Error handling
    """

    def _make_request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make an API request with comprehensive error handling and retries.
        
        Args:
            method: HTTP method to use
            endpoint: API endpoint to call
            params: Optional URL parameters
            data: Optional request body
            headers: Optional additional headers
            timeout: Optional request timeout
            max_retries: Optional retry count override
            
        Returns:
            Parsed JSON response
            
        Raises:
            LinkedInAPIError: For API-related errors
            RequestException: For network/connection errors
        """
        retries = max_retries or self.max_retries
        timeout = timeout or self.DEFAULT_TIMEOUT
        last_error = None
        
        for attempt in range(retries):
            try:
                # Add random delay between requests
                if attempt > 0:
                    delay = self.min_delay * (2 ** attempt)
                    self.logger.debug(f"Retry attempt {attempt + 1}, waiting {delay}s")
                    time.sleep(delay)
                
                # Prepare request
                url = f"{self.BASE_URL}/{self.API_VERSION}/{endpoint.lstrip('/')}"
                request_headers = self._prepare_headers(headers)
                
                # Make request
                response = self.api.client.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers,
                    timeout=timeout
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                    
                # Check for error responses
                response.raise_for_status()
                
                # Parse response
                try:
                    return response.json()
                except JSONDecodeError as e:
                    raise LinkedInAPIError(f"Failed to parse response: {str(e)}")
                    
            except RateLimitError:
                self.logger.warning(
                    f"Rate limit hit on attempt {attempt + 1}, "
                    f"waiting {self.rate_limit_delay}s"
                )
                time.sleep(self.rate_limit_delay)
                continue
                
            except RequestException as e:
                last_error = e
                if attempt == retries - 1:
                    raise LinkedInAPIError(f"Request failed after {retries} attempts: {str(e)}")
                continue
                
        raise last_error or LinkedInAPIError("Request failed for unknown reason")

    def _prepare_headers(self, additional_headers: Optional[Dict] = None) -> Dict[str, str]:
        """
        Prepare request headers with defaults and tracking info.
        
        Args:
            additional_headers: Optional extra headers to include
            
        Returns:
            Complete headers dictionary
        """
        headers = {
            'accept': 'application/vnd.linkedin.normalized+json+2.1',
            'csrf-token': self.api.client.session.cookies.get('JSESSIONID', '').strip('"'),
            'x-li-track': json.dumps({
                'clientVersion': '1.13.5',
                'mpVersion': '1.13.5',
                'osName': 'web',
                'timezoneOffset': 0,
                'deviceFormFactor': 'DESKTOP',
                'mpName': 'voyager-web'
            })
        }
        
        if additional_headers:
            headers.update(additional_headers)
            
        return headers

    def _execute_batch_request(
        self, 
        operation: str,
        items: List[Any],
        *,
        batch_size: Optional[int] = None,
        max_retries: Optional[int] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Execute a batch request with retries and progress tracking.
        
        Args:
            operation: Operation name to execute
            items: List of items to process
            batch_size: Optional batch size override
            max_retries: Optional retry count override
            **kwargs: Additional operation parameters
            
        Returns:
            List of operation results
            
        Raises:
            LinkedInAPIError: If batch processing fails
        """
        batch_size = batch_size or self.BATCH_SIZE
        max_retries = max_retries or self.MAX_BATCH_RETRIES
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            for attempt in range(max_retries):
                try:
                    batch_results = getattr(self, operation)(
                        items=batch,
                        **kwargs
                    )
                    results.extend(batch_results)
                    break
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise LinkedInAPIError(
                            f"Batch processing failed after {max_retries} attempts: {str(e)}"
                        )
                        
                    delay = self.min_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Batch {i // batch_size + 1} failed (attempt {attempt + 1}), "
                        f"waiting {delay}s"
                    )
                    time.sleep(delay)
                    
        return results

    def _validate_response(
        self,
        response_data: Dict[str, Any],
        required_fields: Optional[List[str]] = None
    ) -> bool:
        """
        Validate API response data.
        
        Args:
            response_data: Response data to validate
            required_fields: Optional list of required fields
            
        Returns:
            True if response is valid
        """
        if not isinstance(response_data, dict):
            return False
            
        if required_fields:
            return all(
                field in response_data 
                for field in required_fields
            )
            
        return True
    
    """
    LinkedIn Wrapper Module - Part 3: Core API Methods

    This section implements the core API functionality:
    - Profile retrieval
    - Network information
    - Connection management
    - Enhanced GraphQL support
    """
    def get_user_profile(
        self,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get the current user's profile with enhanced error handling.
        
        Args:
            use_cache: Use cached profile if available
            
        Returns:
            User profile dictionary
            
        Raises:
            LinkedInAPIError: If profile fetch fails
        """
        try:
            # Attempt to get profile with retry logic
            for attempt in range(self.max_retries):
                try:
                    # First try to get the profile
                    response = self.api._fetch(
                        "/me",
                        headers={
                            'accept': 'application/vnd.linkedin.normalized+json+2.1'
                        }
                    )
                    
                    if response.status_code != 200:
                        raise LinkedInAPIError(
                            f"Failed to get profile: status code {response.status_code}"
                        )
                        
                    data = response.json()
                    
                    # Process profile data
                    profile = {}
                    
                    # Try different profile data structures
                    if 'included' in data:
                        for item in data.get('included', []):
                            if item.get('$type') == 'com.linkedin.voyager.identity.shared.MiniProfile':
                                profile = {
                                    'profile_id': item.get('entityUrn', '').split(':')[-1],
                                    'firstName': item.get('firstName', ''),
                                    'lastName': item.get('lastName', ''),
                                    'publicIdentifier': item.get('publicIdentifier', ''),
                                    'entityUrn': item.get('entityUrn', ''),
                                    'profile_urn': f"urn:li:fs_profile:{item.get('entityUrn', '').split(':')[-1]}"
                                }
                                break
                    
                    # If no profile found in included, try main data
                    if not profile and 'data' in data:
                        main_data = data.get('data', {})
                        profile = {
                            'profile_id': main_data.get('*miniProfile', '').split(':')[-1] if main_data.get('*miniProfile') else None,
                            'firstName': main_data.get('firstName', ''),
                            'lastName': main_data.get('lastName', ''),
                            'publicIdentifier': main_data.get('publicIdentifier', ''),
                            'entityUrn': main_data.get('*miniProfile'),
                            'profile_urn': f"urn:li:fs_profile:{main_data.get('*miniProfile', '').split(':')[-1]}" if main_data.get('*miniProfile') else None
                        }
                    
                    # Validate profile
                    if not self._validate_profile(profile):
                        raise LinkedInAPIError("Invalid profile data received")
                    
                    return profile
                    
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise
                        
                    self.logger.warning(
                        f"Profile fetch attempt {attempt + 1} failed: {str(e)}"
                    )
                    time.sleep(self.min_delay * (2 ** attempt))
                    
            raise LinkedInAPIError("Failed to fetch profile after all retries")
            
        except Exception as e:
            self.logger.error(f"Failed to get user profile: {str(e)}")
            raise LinkedInAPIError(f"Profile fetch failed: {str(e)}")

    def _validate_profile(
        self,
        profile: Dict[str, Any]
    ) -> bool:
        """
        Validate profile data structure.
        
        Args:
            profile: Profile data to validate
            
        Returns:
            True if profile is valid
        """
        if not profile:
            return False
            
        # Check required fields
        required_fields = ['profile_id', 'firstName', 'lastName']
        
        for field in required_fields:
            if not profile.get(field):
                self.logger.debug(f"Missing required field: {field}")
                return False
                
        # Validate profile ID format
        if profile.get('profile_id') == 'None' or not str(profile.get('profile_id', '')).strip():
            return False
            
        return True
    
    def get_profile(
        self,
        public_id: Optional[str] = None,
        urn_id: Optional[str] = None,
        *,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch a LinkedIn profile with enhanced error handling.
        
        Args:
            public_id: Public profile identifier
            urn_id: Profile URN identifier
            fields: Optional list of specific fields to fetch
            
        Returns:
            Profile data dictionary
            
        Raises:
            LinkedInAPIError: If profile fetch fails
        """
        if not (public_id or urn_id):
            raise ValueError("Must provide either public_id or urn_id")
            
        try:
            # Construct GraphQL query for better field control
            query = """
                query Profile($profileId: String!, $fields: [String!]) {
                    identity {
                        profileView(profileId: $profileId) {
                            profile {
                                firstName
                                lastName
                                headline
                                summary
                                industryName
                                geoLocationName
                                positions {
                                    companyName
                                    title
                                    startDate
                                    endDate
                                    description
                                }
                                education {
                                    schoolName
                                    degreeName
                                    fieldOfStudy
                                    startDate
                                    endDate
                                }
                                skills {
                                    name
                                    endorsementCount
                                }
                                languages {
                                    name
                                    proficiency
                                }
                                certifications {
                                    name
                                    authority
                                    licenseNumber
                                    startDate
                                    endDate
                                }
                            }
                        }
                    }
                }
            """
            
            variables = {
                "profileId": urn_id or public_id,
                "fields": fields or []
            }
            
            response = self._make_request(
                method="POST",
                endpoint="/graphql",
                data={
                    "query": query,
                    "variables": variables
                }
            )
            
            if not self._validate_response(response, ["data", "identity", "profileView"]):
                raise LinkedInAPIError("Invalid profile response format")
                
            profile_data = response["data"]["identity"]["profileView"]["profile"]
            
            # Clean and standardize the response
            return self._clean_profile_data(profile_data)
            
        except Exception as e:
            self.logger.error(f"Failed to fetch profile: {str(e)}")
            raise LinkedInAPIError(f"Profile fetch failed: {str(e)}")

    def get_profile_network_info(
        self,
        profile_id: str,
        *,
        include_connections: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive network information for a profile.
        
        Args:
            profile_id: Profile identifier
            include_connections: Include connection data
            
        Returns:
            Network information dictionary
        """
        try:
            # Clean profile ID
            clean_id = self._clean_profile_id(profile_id)
            
            # GraphQL query for network info
            query = """
                query NetworkInfo($profileId: String!) {
                    identity {
                        profileView(profileId: $profileId) {
                            networkInfo {
                                followersCount
                                followingCount
                                connectionsCount
                                followable
                                distance
                                mutualConnectionsCount
                                mutualConnectionsTopConnections {
                                    firstName
                                    lastName
                                    occupation
                                    profileId
                                }
                            }
                            followingState {
                                following
                                follower
                            }
                        }
                    }
                }
            """
            
            response = self._make_request(
                method="POST",
                endpoint="/graphql",
                data={
                    "query": query,
                    "variables": {
                        "profileId": f"urn:li:fsd_profile:{clean_id}"
                    }
                }
            )
            
            if not self._validate_response(response, ["data", "identity", "profileView"]):
                raise LinkedInAPIError("Invalid network info response")
                
            network_data = response["data"]["identity"]["profileView"]
            
            # Extract and clean network information
            network_info = {
                "followers_count": network_data["networkInfo"]["followersCount"],
                "following_count": network_data["networkInfo"]["followingCount"],
                "connections_count": network_data["networkInfo"]["connectionsCount"],
                "is_followable": network_data["networkInfo"]["followable"],
                "network_distance": network_data["networkInfo"]["distance"],
                "mutual_connections_count": network_data["networkInfo"]["mutualConnectionsCount"],
                "following_state": network_data["followingState"]
            }
            
            # Fetch connections if requested
            if include_connections:
                network_info["connections"] = self.get_profile_connections(clean_id)
                
            return network_info
            
        except Exception as e:
            self.logger.error(f"Failed to fetch network info: {str(e)}")
            raise LinkedInAPIError(f"Network info fetch failed: {str(e)}")

    def get_profile_connections(
        self,
        profile_id: str,
        *,
        start: int = 0,
        count: int = 50,
        network_depth: str = "F"
    ) -> List[Dict[str, Any]]:
        """
        Fetch connections for a profile with pagination support.
        
        Args:
            profile_id: Profile identifier
            start: Starting index for pagination
            count: Number of connections to fetch
            network_depth: Connection degree (F/S/O)
            
        Returns:
            List of connection dictionaries
        """
        try:
            # GraphQL query for connections
            query = """
                query ProfileConnections(
                    $profileId: String!,
                    $start: Int!,
                    $count: Int!
                ) {
                    identity {
                        profileView(profileId: $profileId) {
                            connections(start: $start, count: $count) {
                                elements {
                                    entityUrn
                                    profileId
                                    firstName
                                    lastName
                                    headline
                                    publicIdentifier
                                    occupation
                                    geoLocation {
                                        name
                                    }
                                    industry {
                                        name
                                    }
                                    profilePicture {
                                        displayImageUrl
                                    }
                                }
                                paging {
                                    total
                                    count
                                    start
                                    links {
                                        type
                                        rel
                                        href
                                    }
                                }
                            }
                        }
                    }
                }
            """
            
            variables = {
                "profileId": f"urn:li:fsd_profile:{self._clean_profile_id(profile_id)}",
                "start": start,
                "count": min(count, 100)  # LinkedIn limit
            }
            
            response = self._make_request(
                method="POST",
                endpoint="/graphql",
                data={
                    "query": query,
                    "variables": variables
                }
            )
            
            # Validate and extract connection data
            connections_data = (
                response.get("data", {})
                .get("identity", {})
                .get("profileView", {})
                .get("connections", {})
            )
            
            if not connections_data or "elements" not in connections_data:
                return []
                
            # Process connections
            connections = []
            for element in connections_data["elements"]:
                connection = {
                    "urn_id": element.get("profileId"),
                    "name": f"{element.get('firstName', '')} {element.get('lastName', '')}".strip(),
                    "headline": element.get("headline") or element.get("occupation"),
                    "public_id": element.get("publicIdentifier"),
                    "location": element.get("geoLocation", {}).get("name"),
                    "industry": element.get("industry", {}).get("name"),
                    "picture_url": element.get("profilePicture", {}).get("displayImageUrl")
                }
                
                if connection["urn_id"] and connection["name"]:
                    connections.append(connection)
                    
            return connections
            
        except Exception as e:
            self.logger.error(f"Failed to fetch connections: {str(e)}")
            raise LinkedInAPIError(f"Connection fetch failed: {str(e)}")

    def _clean_profile_id(self, profile_id: str) -> str:
        """
        Clean and standardize profile identifiers.
        
        Args:
            profile_id: Raw profile identifier
            
        Returns:
            Cleaned profile ID
        """
        if not profile_id:
            raise ValueError("Profile ID cannot be empty")
            
        # Handle URN format
        if profile_id.startswith("urn:li:"):
            parts = profile_id.split(":")
            return parts[-1]
            
        # Handle fs_miniProfile format
        if "fs_" in profile_id:
            parts = profile_id.split("_")
            return parts[-1]
            
        return profile_id.strip()

    def _clean_profile_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and standardize profile response data.
        
        Args:
            profile_data: Raw profile data
            
        Returns:
            Cleaned profile dictionary
        """
        if not profile_data:
            return {}
            
        # Extract basic information
        cleaned = {
            "name": {
                "first_name": profile_data.get("firstName"),
                "last_name": profile_data.get("lastName")
            },
            "headline": profile_data.get("headline"),
            "summary": profile_data.get("summary"),
            "industry": profile_data.get("industryName"),
            "location": profile_data.get("geoLocationName")
        }
        
        # Clean experience data
        cleaned["experience"] = [
            {
                "company": pos.get("companyName"),
                "title": pos.get("title"),
                "start_date": pos.get("startDate"),
                "end_date": pos.get("endDate"),
                "description": pos.get("description")
            }
            for pos in profile_data.get("positions", [])
        ]
        
        # Clean education data
        cleaned["education"] = [
            {
                "school": edu.get("schoolName"),
                "degree": edu.get("degreeName"),
                "field": edu.get("fieldOfStudy"),
                "start_date": edu.get("startDate"),
                "end_date": edu.get("endDate")
            }
            for edu in profile_data.get("education", [])
        ]
        
        # Clean skills data
        cleaned["skills"] = [
            {
                "name": skill.get("name"),
                "endorsements": skill.get("endorsementCount", 0)
            }
            for skill in profile_data.get("skills", [])
        ]
        
        return cleaned    
    
    """
    LinkedIn Wrapper Module - Part 4: Advanced API Methods 

    This section implements advanced API functionality:
    - Search capabilities
    - Job APIs
    - Company APIs 
    - Post interaction
    """

    def search_people(
        self,
        keywords: Optional[str] = None,
        connection_of: Optional[str] = None,
        network_depths: Optional[List[Union[Literal["F"], Literal["S"], Literal["O"]]]] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Enhanced people search with GraphQL support.
        
        Args:
            keywords: Search keywords
            connection_of: Filter by connection to profile
            network_depths: Connection depth filters
            **kwargs: Additional search parameters
            
        Returns:
            List of search results
        """
        try:
            # GraphQL search query
            query = """
                query PeopleSearch(
                    $keywords: String,
                    $connectionOf: String,
                    $networkDepths: [String!],
                    $start: Int!,
                    $count: Int!
                ) {
                    peopleSearch(
                        keywords: $keywords,
                        connectionOf: $connectionOf,
                        networkDepths: $networkDepths,
                        start: $start,
                        count: $count
                    ) {
                        elements {
                            entityUrn
                            title {
                                text
                            }
                            subtitle {
                                text
                            }
                            publicIdentifier
                            trackingId
                            socialProofText
                            image {
                                attributes {
                                    sourceType
                                    vectorImage {
                                        rootUrl
                                        artifacts {
                                            width
                                            height
                                            fileIdentifyingUrlPathSegment
                                        }
                                    }
                                }
                            }
                        }
                        paging {
                            total
                            count
                            start
                        }
                    }
                }
            """
            
            variables = {
                "keywords": keywords,
                "connectionOf": connection_of,
                "networkDepths": network_depths,
                "start": kwargs.get("start", 0),
                "count": min(kwargs.get("count", 25), 100)
            }
            
            response = self._make_request(
                method="POST",
                endpoint="/graphql",
                data={
                    "query": query,
                    "variables": variables
                }
            )
            
            return self._process_search_results(response)
            
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            raise LinkedInAPIError(f"Search operation failed: {str(e)}")

    def get_company_updates(
        self,
        company_id: str,
        *,
        start: int = 0,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch company updates with enhanced metadata.
        
        Args:
            company_id: Company identifier
            start: Starting index
            count: Number of updates to fetch
            
        Returns:
            List of company updates
        """
        try:
            query = """
                query CompanyUpdates(
                    $companyId: String!,
                    $start: Int!,
                    $count: Int!
                ) {
                    company(id: $companyId) {
                        updates(start: $start, count: $count) {
                            elements {
                                id
                                text
                                created
                                author {
                                    name
                                    profileId
                                }
                                social {
                                    numLikes
                                    numComments
                                    numShares
                                }
                                content {
                                    type
                                    title
                                    description
                                    url
                                }
                            }
                        }
                    }
                }
            """
            
            response = self._make_request(
                method="POST",
                endpoint="/graphql",
                data={
                    "query": query,
                    "variables": {
                        "companyId": company_id,
                        "start": start,
                        "count": min(count, 100)
                    }
                }
            )
            
            return self._process_company_updates(response)
            
        except Exception as e:
            self.logger.error(f"Failed to fetch company updates: {str(e)}")
            raise LinkedInAPIError(f"Company updates fetch failed: {str(e)}")

    def get_job_details(
        self,
        job_id: str
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive job posting details.
        
        Args:
            job_id: Job posting identifier
            
        Returns:
            Job details dictionary
        """
        try:
            query = """
                query JobDetails($jobId: String!) {
                    job(id: $jobId) {
                        title
                        description
                        formattedLocation
                        listedAt
                        expireAt
                        company {
                            name
                            industry
                            companySize
                            websiteUrl
                        }
                        applicationSettings {
                            applyMethod
                            externalApplyUrl
                        }
                        compensation {
                            salary {
                                minimum
                                maximum
                                currency
                            }
                            benefits
                        }
                        requirements {
                            experienceLevel
                            education
                            skills
                        }
                    }
                }
            """
            
            response = self._make_request(
                method="POST",
                endpoint="/graphql",
                data={
                    "query": query,
                    "variables": {
                        "jobId": job_id
                    }
                }
            )
            
            return self._process_job_details(response)
            
        except Exception as e:
            self.logger.error(f"Failed to fetch job details: {str(e)}")
            raise LinkedInAPIError(f"Job details fetch failed: {str(e)}")

    def react_to_post(
        self,
        post_urn: str,
        reaction_type: str = "LIKE"
    ) -> bool:
        """
        React to a post with enhanced error handling.
        
        Args:
            post_urn: Post URN identifier
            reaction_type: Type of reaction
            
        Returns:
            Success status
        """
        try:
            mutation = """
                mutation AddReaction(
                    $postUrn: String!,
                    $reactionType: String!
                ) {
                    addReaction(
                        postUrn: $postUrn,
                        reactionType: $reactionType
                    ) {
                        status
                    }
                }
            """
            
            response = self._make_request(
                method="POST",
                endpoint="/graphql",
                data={
                    "query": mutation,
                    "variables": {
                        "postUrn": post_urn,
                        "reactionType": reaction_type
                    }
                }
            )
            
            return response.get("data", {}).get("addReaction", {}).get("status") == "SUCCESS"
            
        except Exception as e:
            self.logger.error(f"Failed to add reaction: {str(e)}")
            raise LinkedInAPIError(f"Reaction failed: {str(e)}")

    def _process_search_results(
        self,
        response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process and clean search results."""
        try:
            results = []
            elements = (
                response.get("data", {})
                .get("peopleSearch", {})
                .get("elements", [])
            )
            
            for element in elements:
                result = {
                    "urn_id": element.get("entityUrn", "").split(":")[-1],
                    "name": element.get("title", {}).get("text", ""),
                    "headline": element.get("subtitle", {}).get("text", ""),
                    "public_id": element.get("publicIdentifier"),
                    "tracking_id": element.get("trackingId"),
                    "social_proof": element.get("socialProofText")
                }
                
                # Process profile image if available
                if "image" in element:
                    image_data = element["image"]["attributes"].get("vectorImage", {})
                    if image_data:
                        result["profile_picture"] = {
                            "root_url": image_data.get("rootUrl"),
                            "artifacts": image_data.get("artifacts", [])
                        }
                
                results.append(result)
                
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to process search results: {str(e)}")
            return []

    def _process_company_updates(
        self,
        response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process and clean company updates."""
        try:
            updates = []
            elements = (
                response.get("data", {})
                .get("company", {})
                .get("updates", {})
                .get("elements", [])
            )
            
            for element in elements:
                update = {
                    "id": element.get("id"),
                    "text": element.get("text"),
                    "created_at": element.get("created"),
                    "author": element.get("author", {}),
                    "metrics": element.get("social", {}),
                    "content": element.get("content", {})
                }
                updates.append(update)
                
            return updates
            
        except Exception as e:
            self.logger.error(f"Failed to process company updates: {str(e)}")
            return []

    def _process_job_details(
        self,
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process and clean job posting details."""
        try:
            job_data = response.get("data", {}).get("job", {})
            if not job_data:
                return {}
                
            return {
                "title": job_data.get("title"),
                "description": job_data.get("description"),
                "location": job_data.get("formattedLocation"),
                "listed_at": job_data.get("listedAt"),
                "expire_at": job_data.get("expireAt"),
                "company": job_data.get("company", {}),
                "application": job_data.get("applicationSettings", {}),
                "compensation": job_data.get("compensation", {}),
                "requirements": job_data.get("requirements", {})
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process job details: {str(e)}")
            return {}
        
    """
    LinkedIn Wrapper Module - Part 5: Utilities and Session Management

    This section implements utility functions and session management:
    - Session handling
    - Rate limiting
    - Caching
    - Helper functions
    """

    def _manage_session(self) -> None:
        """Manage API session state and rate limiting."""
        self.session_info = {
            "requests": 0,
            "last_request": datetime.now(),
            "rate_limit_hits": 0,
            "errors": 0
        }
        
        # Update session metrics
        self.session_info["requests"] += 1
        current_time = datetime.now()
        time_diff = (current_time - self.session_info["last_request"]).total_seconds()
        
        # Implement rate limiting if needed
        if time_diff < self.min_delay:
            sleep_time = self.min_delay - time_diff
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.session_info["last_request"] = current_time

    def _generate_tracking_id(self) -> str:
        """Generate a unique tracking ID for requests."""
        return f"linkedin_{uuid.uuid4().hex[:16]}_{int(time.time())}"

    def get_session_metrics(self) -> Dict[str, Any]:
        """
        Get current session metrics.
        
        Returns:
            Session statistics dictionary
        """
        return {
            "total_requests": self.session_info["requests"],
            "rate_limit_hits": self.session_info["rate_limit_hits"],
            "error_count": self.session_info["errors"],
            "last_request": self.session_info["last_request"].isoformat()
        }

    def clear_session(self) -> None:
        """Clear current session state and metrics."""
        self.session_info = {
            "requests": 0,
            "last_request": datetime.now(),
            "rate_limit_hits": 0,
            "errors": 0
        }
        self.logger.info("Session state cleared")

    def _handle_rate_limit(self) -> None:
        """Handle rate limit situations."""
        self.session_info["rate_limit_hits"] += 1
        wait_time = self.rate_limit_delay * (2 ** self.session_info["rate_limit_hits"])
        
        self.logger.warning(
            f"Rate limit hit {self.session_info['rate_limit_hits']} times. "
            f"Waiting {wait_time}s"
        )
        
        time.sleep(wait_time)

    @property
    def session_valid(self) -> bool:
        """Check if current session is valid."""
        try:
            response = self.api._fetch(
                "/me",
                headers={'accept': 'application/vnd.linkedin.normalized+json+2.1'}
            )
            return response.status_code == 200
        except Exception:
            return False

    def refresh_session(self) -> bool:
        """
        Refresh the current session.
        
        Returns:
            Success status
        """
        try:
            self.api = self._initialize_api(
                username=self.username,
                password=self.password,
                debug=self.debug,
                refresh_cookies=True
            )
            return True
        except Exception as e:
            self.logger.error(f"Session refresh failed: {str(e)}")
            return False
        
    def _log_available_methods(self) -> None:
        """
        Log all available methods from the base API and wrapper.
        This helps with debugging and understanding available functionality.
        """
        try:
            self.logger.info("Inspecting available API methods...")
            print("\n=== Available LinkedIn API Methods ===")
            
            # Get all methods from base API
            base_methods = [
                method for method in dir(self.api)
                if callable(getattr(self.api, method)) and not method.startswith('_')
            ]
            
            # Get all methods from wrapper
            wrapper_methods = [
                method for method in dir(self)
                if callable(getattr(self, method)) and not method.startswith('_')
            ]
            
            # Log base API methods
            self.logger.info("Base API Methods:")
            print("\nBase API Methods:")
            for method in sorted(base_methods):
                try:
                    # Get method signature
                    method_obj = getattr(self.api, method)
                    import inspect
                    signature = str(inspect.signature(method_obj))
                    docstring = inspect.getdoc(method_obj)
                    
                    # Log method info
                    self.logger.info(f"- {method}{signature}")
                    print(f"\n• {method}{signature}")
                    if docstring:
                        # Print first line of docstring
                        doc_summary = docstring.split('\n')[0]
                        print(f"  Description: {doc_summary}")
                        
                except Exception as e:
                    self.logger.debug(f"Error inspecting method {method}: {str(e)}")
            
            # Log wrapper methods
            self.logger.info("\nWrapper Methods:")
            print("\nWrapper Methods:")
            for method in sorted(wrapper_methods):
                try:
                    method_obj = getattr(self, method)
                    signature = str(inspect.signature(method_obj))
                    docstring = inspect.getdoc(method_obj)
                    
                    self.logger.info(f"- {method}{signature}")
                    print(f"\n• {method}{signature}")
                    if docstring:
                        doc_summary = docstring.split('\n')[0]
                        print(f"  Description: {doc_summary}")
                        
                except Exception as e:
                    self.logger.debug(f"Error inspecting method {method}: {str(e)}")
                    
            # Log API compatibility status
            missing_methods = set(base_methods) - set(wrapper_methods)
            if missing_methods:
                self.logger.warning(
                    f"Missing base API methods in wrapper: {', '.join(missing_methods)}"
                )
                print("\nWarning: Some base API methods are not implemented in wrapper:")
                for method in sorted(missing_methods):
                    print(f"- {method}")
                    
        except Exception as e:
            self.logger.error(f"Error inspecting API methods: {str(e)}")

    def _inspect_api(self) -> None:
        """
        Perform detailed API inspection and logging.
        Helps with debugging and understanding API structure.
        """
        try:
            self.logger.info("Performing detailed API inspection...")
            print("\n=== API Inspection Results ===")
            
            # Check API instance
            print("\nAPI Instance Information:")
            print(f"• Type: {type(self.api)}")
            print(f"• Module: {self.api.__module__}")
            
            # Check session status
            session_valid = self._validate_session()
            print(f"\nSession Status: {'Valid' if session_valid else 'Invalid'}")
            
            # Check authentication state
            cookies = self.api.client.session.cookies
            auth_status = "Authenticated" if cookies.get('li_at') else "Not authenticated"
            print(f"Authentication Status: {auth_status}")
            
            # Log API endpoints
            print("\nAvailable API Endpoints:")
            if hasattr(self.api, 'client'):
                base_url = self.api.client.API_BASE_URL
                print(f"• Base URL: {base_url}")
                
            # Inspect request headers
            print("\nRequest Headers:")
            for header, value in self.api.client.session.headers.items():
                print(f"• {header}: {value}")
                
            # Check API version info
            if hasattr(self.api, '_MAX_POST_COUNT'):
                print("\nAPI Limits:")
                print(f"• Max Post Count: {self.api._MAX_POST_COUNT}")
                print(f"• Max Update Count: {self.api._MAX_UPDATE_COUNT}")
                print(f"• Max Search Count: {self.api._MAX_SEARCH_COUNT}")
                
        except Exception as e:
            self.logger.error(f"API inspection failed: {str(e)}")

    def debug_info(self) -> None:
        """
        Print comprehensive debug information.
        This method combines all debug functionality.
        """
        print("\n=== LinkedIn API Debug Information ===")
        
        # Log API methods
        self._log_available_methods()
        
        # Inspect API
        self._inspect_api()
        
        # Log session info
        print("\nSession Information:")
        print(f"• Debug Mode: {self.debug}")
        print(f"• Max Retries: {self.max_retries}")
        print(f"• Min Delay: {self.min_delay}s")
        print(f"• Max Delay: {self.max_delay}s")
        
        # Log configuration
        print("\nConfiguration:")
        print(f"• Username: {self.username}")
        print(f"• API Base URL: {self.api.client.API_BASE_URL}")
        
        # Test basic API functionality
        print("\nAPI Functionality Test:")
        try:
            me = self.get_user_profile()
            print("✓ User profile fetch successful")
            print(f"• Profile ID: {me.get('profile_id')}")
            print(f"• Name: {me.get('firstName')} {me.get('lastName')}")
        except Exception as e:
            print(f"✗ User profile fetch failed: {str(e)}")

    def __enter__(self) -> 'LinkedInWrapper':
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        """Context manager exit with cleanup."""
        self.clear_session()

    def __repr__(self) -> str:
        """Object representation."""
        return (
            f"LinkedInWrapper(username='{self.username}', "
            f"debug={self.debug}, "
            f"requests={self.session_info['requests']})"
        )