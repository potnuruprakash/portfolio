"""
Reusable MongoDB connection module for Portfolio backend.
Uses PyMongo client pooling and protects credentials.
"""
import logging
import threading
from typing import Optional, Tuple
from django.conf import settings
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, ConfigurationError

logger = logging.getLogger('api.mongo')

# Recognized portfolio collections
PORTFOLIO_COLLECTIONS = (
    'profiles',
    'education',
    'skills',
    'projects',
    'experience',
    'certifications',
    'achievements',
    'resumes',
    'social_links',
    'site_settings',
    'admins',
    'audit_logs',
    'files',
)


class MongoDBManager:
    """
    Thread-safe Singleton manager for MongoDB Atlas connection.
    Reuses a single MongoClient across requests with internal connection pooling.
    """
    _instance: Optional['MongoDBManager'] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> 'MongoDBManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MongoDBManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, '_initialized', False):
            return

        self._client: Optional[MongoClient] = None
        self._database_name: str = getattr(settings, 'MONGODB_DATABASE', 'portfolio') or 'portfolio'
        self._initialized = True

    def _get_client(self) -> MongoClient:
        """
        Lazily initialize and return the reusable MongoClient.
        """
        if self._client is None:
            with self._lock:
                if self._client is None:
                    uri = getattr(settings, 'MONGODB_URI', '').strip()
                    if not uri:
                        raise ConfigurationError("MONGODB_URI environment variable is not configured.")

                    normalized_uri = self._normalize_uri(uri)

                    # Timeout after 5 seconds to prevent hanging on network/DNS failure
                    self._client = MongoClient(
                        normalized_uri,
                        serverSelectionTimeoutMS=5000,
                        connectTimeoutMS=5000,
                        maxPoolSize=50,
                        minPoolSize=5,
                    )
                    logger.info("MongoDB client pool initialized for database: %s", self._database_name)
        return self._client

    @staticmethod
    def _normalize_uri(uri: str) -> str:
        """Ensure password in MongoDB URI is properly percent-encoded if unescaped."""
        import urllib.parse
        if '://' in uri and '@' in uri:
            scheme, rest = uri.split('://', 1)
            if '@' in rest:
                auth_part, host_part = rest.rsplit('@', 1)
                if ':' in auth_part:
                    user_part, pass_part = auth_part.split(':', 1)
                    # Unquote first to prevent double-encoding, then quote
                    unquoted_pass = urllib.parse.unquote_plus(pass_part)
                    quoted_pass = urllib.parse.quote_plus(unquoted_pass)
                    return f"{scheme}://{user_part}:{quoted_pass}@{host_part}"
        return uri

    @property
    def db(self) -> Database:
        """Return the target database instance (defaults to 'portfolio')."""
        client = self._get_client()
        return client[self._database_name]

    def get_collection(self, collection_name: str) -> Collection:
        """Return a handle to the requested collection."""
        return self.db[collection_name]

    # Pre-defined collection accessors
    @property
    def profiles(self) -> Collection:
        return self.get_collection('profiles')

    @property
    def education(self) -> Collection:
        return self.get_collection('education')

    @property
    def skills(self) -> Collection:
        return self.get_collection('skills')

    @property
    def projects(self) -> Collection:
        return self.get_collection('projects')

    @property
    def experience(self) -> Collection:
        return self.get_collection('experience')

    @property
    def certifications(self) -> Collection:
        return self.get_collection('certifications')

    @property
    def achievements(self) -> Collection:
        return self.get_collection('achievements')

    @property
    def resumes(self) -> Collection:
        return self.get_collection('resumes')

    @property
    def social_links(self) -> Collection:
        return self.get_collection('social_links')

    @property
    def site_settings(self) -> Collection:
        return self.get_collection('site_settings')

    @property
    def admins(self) -> Collection:
        return self.get_collection('admins')

    @property
    def audit_logs(self) -> Collection:
        return self.get_collection('audit_logs')

    @property
    def files(self) -> Collection:
        return self.get_collection('files')

    def check_connection(self) -> Tuple[bool, str]:
        """
        Verify live connectivity with MongoDB Atlas.
        Returns:
            Tuple of (is_connected: bool, message: str)
            Never includes sensitive credentials in logs or output.
        """
        try:
            client = self._get_client()
            # Send ping command to verify connection
            client.admin.command('ping')
            logger.info("MongoDB Atlas health check ping: SUCCESS")
            return True, "connected"
        except ConfigurationError as ce:
            logger.warning("MongoDB configuration issue: %s", str(ce))
            return False, "Database not configured"
        except PyMongoError as pe:
            # Mask any credentials or raw connection strings in logs
            logger.error("MongoDB Atlas connection error during ping check: %s", type(pe).__name__)
            return False, "disconnected"
        except Exception as ex:
            logger.error("Unexpected error during MongoDB ping check: %s", type(ex).__name__)
            return False, "disconnected"

    def close(self) -> None:
        """Close MongoClient connection pool."""
        with self._lock:
            if self._client is not None:
                self._client.close()
                self._client = None
                logger.info("MongoDB client connection pool closed.")


# Global singleton instance
mongo_manager = MongoDBManager()
