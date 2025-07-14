"""
API modules for fetching media posters.

This package handles communication with external APIs:
- MediaAPI: Multi-API poster fetching with intelligent fallbacks
- TMDB, OMDb, TVmaze, AniList integration
- Caching and rate limiting
"""

from .media_api import MediaAPI

__all__ = ["MediaAPI"]
