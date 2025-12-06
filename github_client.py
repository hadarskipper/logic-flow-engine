"""GitHub client for fetching and caching YAML configuration files."""

import logging
from typing import Dict, Optional

import requests
import yaml

logger = logging.getLogger(__name__)

# Default GitHub repository configuration
DEFAULT_GITHUB_REPO = "hadarskipper/my-special-test-flow"
DEFAULT_BRANCH = "main"
DEFAULT_FILE_PATH = "logic.yaml"
DEFAULT_GITHUB_URL = f"https://github.com/{DEFAULT_GITHUB_REPO}/blob/{DEFAULT_BRANCH}/{DEFAULT_FILE_PATH}"


class GitHubConfigCache:
    """Cache for GitHub YAML configurations keyed by commit SHA."""
    
    def __init__(self):
        """Initialize the cache."""
        self._cache: Dict[str, Dict] = {}
        self._latest_commit_sha: Optional[str] = None
        logger.info("GitHub config cache initialized")
    
    def _build_raw_url(self, commit_sha: Optional[str] = None) -> str:
        """
        Build GitHub raw content URL.
        
        Args:
            commit_sha: Optional commit SHA (defaults to main branch)
            
        Returns:
            Raw content URL
        """
        if commit_sha:
            return f"https://raw.githubusercontent.com/{DEFAULT_GITHUB_REPO}/{commit_sha}/{DEFAULT_FILE_PATH}"
        else:
            return f"https://raw.githubusercontent.com/{DEFAULT_GITHUB_REPO}/{DEFAULT_BRANCH}/{DEFAULT_FILE_PATH}"
    
    def _fetch_yaml_from_github(self, commit_sha: Optional[str] = None) -> Dict:
        """
        Fetch YAML configuration from GitHub.
        
        Args:
            commit_sha: Optional commit SHA (defaults to latest/main branch)
            
        Returns:
            Parsed YAML configuration as dictionary
        """
        url = self._build_raw_url(commit_sha)
        cache_key = commit_sha or "latest"
        
        logger.info(f"Fetching configuration from GitHub: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            yaml_content = response.text
            config = yaml.safe_load(yaml_content)
            
            # Cache the result
            self._cache[cache_key] = config
            logger.info(f"Cached configuration for commit SHA: {cache_key}")
            
            return config
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching configuration from GitHub: {e}")
            raise ValueError(f"Failed to fetch configuration from GitHub: {e}")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            raise ValueError(f"Failed to parse YAML configuration: {e}")
    
    def get_config(self, commit_sha: Optional[str] = None) -> Dict:
        """
        Get YAML configuration, using cache if available.
        
        Args:
            commit_sha: Optional commit SHA (defaults to latest/main branch)
            
        Returns:
            Parsed YAML configuration as dictionary
        """
        cache_key = commit_sha or "latest"
        
        # Check cache first
        if cache_key in self._cache:
            logger.info(f"Using cached configuration for commit SHA: {cache_key}")
            return self._cache[cache_key]
        
        # Fetch from GitHub if not in cache
        return self._fetch_yaml_from_github(commit_sha)
    
    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cache.clear()
        logger.info("Configuration cache cleared")
    
    def get_cache_size(self) -> int:
        """Get the number of cached configurations."""
        return len(self._cache)
    
    def get_cached_commits(self) -> list:
        """Get list of cached commit SHAs."""
        return list(self._cache.keys())
    
    def get_latest_commit_sha(self, branch: str = DEFAULT_BRANCH, use_cache: bool = False) -> str:
        """
        Get the latest commit SHA from GitHub for the specified branch.
        
        Args:
            branch: Branch name (defaults to main)
            use_cache: If True, use cached value if available. If False, fetch fresh from GitHub.
            
        Returns:
            Latest commit SHA string
        """
        # Use cached value if requested and available
        if use_cache and self._latest_commit_sha:
            logger.info(f"Using cached latest commit SHA: {self._latest_commit_sha}")
            return self._latest_commit_sha
        
        # Fetch from GitHub API
        api_url = f"https://api.github.com/repos/{DEFAULT_GITHUB_REPO}/commits/{branch}"
        logger.info(f"Fetching latest commit SHA from GitHub API: {api_url}")
        
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            commit_data = response.json()
            commit_sha = commit_data.get("sha")
            
            if not commit_sha:
                raise ValueError("No SHA found in GitHub API response")
            
            # Update cache
            self._latest_commit_sha = commit_sha
            logger.info(f"Fetched latest commit SHA: {commit_sha}")
            
            return commit_sha
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching latest commit SHA from GitHub: {e}")
            raise ValueError(f"Failed to fetch latest commit SHA from GitHub: {e}")


# Global cache instance
_github_cache = GitHubConfigCache()


def get_github_config(commit_sha: Optional[str] = None) -> Dict:
    """
    Get GitHub YAML configuration with caching.
    
    Args:
        commit_sha: Optional commit SHA (defaults to latest/main branch)
        
    Returns:
        Parsed YAML configuration as dictionary
    """
    return _github_cache.get_config(commit_sha)


def get_default_github_url() -> str:
    """
    Get the default GitHub URL.
    
    Returns:
        Default GitHub repository URL
    """
    return DEFAULT_GITHUB_URL


def get_latest_commit_sha(branch: str = DEFAULT_BRANCH, use_cache: bool = False) -> str:
    """
    Get the latest commit SHA from GitHub for the specified branch.
    
    Args:
        branch: Branch name (defaults to main)
        use_cache: If True, use cached value if available. If False, fetch fresh from GitHub.
        
    Returns:
        Latest commit SHA string
    """
    return _github_cache.get_latest_commit_sha(branch, use_cache=use_cache)

