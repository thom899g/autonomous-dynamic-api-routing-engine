"""
Configuration management for the Autonomous Dynamic API Routing Engine.
Centralizes all configuration settings with environment-aware defaults.
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class Environment(str, Enum):
    """Environment types for the routing engine."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class RoutingStrategy(str, Enum):
    """Available routing strategies."""
    LATENCY_OPTIMIZED = "latency_optimized"
    COST_OPTIMIZED = "cost_optimized"
    LOAD_BALANCED = "load_balanced"
    FAILOVER = "failover"


@dataclass
class FirebaseConfig:
    """Firebase configuration."""
    project_id: str = os.getenv("FIREBASE_PROJECT_ID", "api-routing-engine")
    credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "./service-account-key.json")
    database_url: str = os.getenv("FIREBASE_DATABASE_URL", "")
    
    def validate(self) -> bool:
        """Validate Firebase configuration."""
        if not self.project_id:
            raise ValueError("Firebase project ID is required")
        return True


@dataclass
class APIConfig:
    """API server configuration."""
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    workers: int = int(os.getenv("API_WORKERS", "4"))
    debug: bool = os.getenv("API_DEBUG", "false").lower() == "true"
    cors_origins: list[str] = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","))


@dataclass
class RoutingConfig:
    """Routing engine configuration."""
    default_strategy: RoutingStrategy = RoutingStrategy(
        os.getenv("DEFAULT_ROUTING_STRATEGY", "latency_optimized")
    )
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    timeout_seconds: int = int(os.getenv("TIMEOUT_SECONDS", "30"))
    circuit_breaker_threshold: int = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
    
    # Performance thresholds
    latency_threshold_ms: int = int(os.getenv("LATENCY_THRESHOLD_MS", "1000"))
    error_rate_threshold: float = float(os.getenv("ERROR_RATE_THRESHOLD", "0.1"))
    success_rate_threshold: float = float(os.getenv("SUCCESS_RATE_THRESHOLD", "0.95"))


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = os.getenv("LOG_LEVEL", "INFO")
    format: str = os.getenv("LOG_FORMAT", "json")
    enable_structured_logging: bool = os.getenv("ENABLE_STRUCTURED_LOGGING", "true").lower() == "true"


@dataclass
class Config:
    """Main configuration class."""
    environment: Environment = Environment(os.getenv("ENVIRONMENT", "development"))
    firebase: FirebaseConfig = field(default_factory=FirebaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    routing: RoutingConfig = field(default_factory=RoutingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.firebase.validate()
        
        if self.environment == Environment.PRODUCTION:
            if self.api.debug:
                raise ValueError("Debug mode cannot be enabled in production")
            if "*" in self.api.cors_origins:
                raise ValueError("Wildcard CORS origins not allowed in production")


# Global configuration instance
config = Config()