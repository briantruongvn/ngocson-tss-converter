"""
Configuration management for Excel Template Converter
Provides centralized configuration handling with validation and defaults.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import logging

from .exceptions import ConfigurationError, FileAccessError

logger = logging.getLogger(__name__)


class TSConverterConfig:
    """
    Configuration manager for TSS Converter
    Handles loading, validation, and access to configuration settings.
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        "general": {
            "base_dir": ".",
            "output_dir": "output",
            "input_dir": "input",
            "log_level": "INFO",
            "max_workers": 4
        },
        "validation": {
            "strict_mode": True,
            "skip_format_validation": False,
            "skip_structure_validation": False,
            "allow_missing_columns": False
        },
        "step1": {
            "template_headers": [
                {"name": "Combination", "bg_color": "00FFFF00", "font_color": "00000000", "width": 15.0},
                {"name": "General Type Component(Type)", "bg_color": "00FF0000", "font_color": "00FFFFFF", "width": 20.0},
                {"name": "Sub-Type Component Identity Process Name", "bg_color": "00FF0000", "font_color": "00FFFFFF", "width": 25.0},
                {"name": "Material Designation", "bg_color": "00FF0000", "font_color": "00FFFFFF", "width": 18.0},
                {"name": "Material Distributor", "bg_color": "00FF0000", "font_color": "00FFFFFF", "width": 15.0},
                {"name": "Producer", "bg_color": "00FF0000", "font_color": "00FFFFFF", "width": 12.0},
                {"name": "Material Type In Process", "bg_color": "00FF0000", "font_color": "00FFFFFF", "width": 20.0},
                {"name": "Document type", "bg_color": "000000FF", "font_color": "00FFFFFF", "width": 15.0},
                {"name": "Requirement Source/TED", "bg_color": "000000FF", "font_color": "00FFFFFF", "width": 20.0},
                {"name": "Sub-type", "bg_color": "000000FF", "font_color": "00FFFFFF", "width": 12.0},
                {"name": "Regulation or substances", "bg_color": "000000FF", "font_color": "00FFFFFF", "width": 20.0},
                {"name": "Limit", "bg_color": "00B8E6B8", "font_color": "00000000", "width": 10.0},
                {"name": "Test method", "bg_color": "00B8E6B8", "font_color": "00000000", "width": 15.0},
                {"name": "Frequency", "bg_color": "00B8E6B8", "font_color": "00000000", "width": 12.0},
                {"name": "Level", "bg_color": "000000FF", "font_color": "00FFFFFF", "width": 10.0},
                {"name": "Warning Limit", "bg_color": "00B8E6B8", "font_color": "00000000", "width": 15.0},
                {"name": "Additional Information", "bg_color": "00B8E6B8", "font_color": "00000000", "width": 20.0}
            ]
        },
        "step2": {
            "name_headers": ["Product name", "Article name", "product name", "article name"],
            "number_headers": ["Product number", "Article number", "product number", "article number"],
            "max_search_rows": 100
        },
        "step3": {
            "f_type_mapping": {
                "C": "D", "H": "F", "KL": "I", "M": "J", "N": "K", 
                "O": "L", "P": "M", "Q": "N", "S": "O", "T": "H", "W": "P"
            },
            "m_type_mapping": {
                "B": "B", "C": "C", "I": "D", "J": "F", "K": "E", 
                "NO": "I", "P": "J", "Q": "K", "R": "L", "S": "M", "T": "N", "W": "H", "Z": "P"
            },
            "c_type_mapping": {
                "B": "B", "C": "C", "H": "D", "I": "F", "J": "E", 
                "MN": "I", "O": "J", "P": "K", "Q": "L", "R": "M", "S": "N", "V": "H", "Y": "P"
            },
            "column_delimiter": "-"
        },
        "step4": {
            "fill_columns": ["D", "E", "F"],
            "start_row": 4,
            "max_iterations": 1000
        },
        "step5": {
            "comparison_columns": ["B", "C", "D", "E", "F", "I", "J"],
            "clear_columns": ["K", "L", "M"],
            "start_row": 4,
            "na_values": ["", "NA", "-"],
            "sd_identifier": "SD",
            "default_frequency": "Yearly"
        },
        "file_formats": {
            "supported_extensions": [".xlsx"],
            "supported_mimetypes": [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel"
            ],
            "max_file_size_mb": 100
        }
    }
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None, base_dir: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to configuration file (optional)
            base_dir: Base directory for relative paths
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.config_file = None
        self._config = self.DEFAULT_CONFIG.copy()
        
        # Try to load configuration file
        if config_file:
            self.config_file = Path(config_file)
        else:
            # Look for default config files
            candidates = [
                self.base_dir / "tsconverter.json",
                self.base_dir / "config.json",
                Path.home() / ".tsconverter.json"
            ]
            
            for candidate in candidates:
                if candidate.exists():
                    self.config_file = candidate
                    break
        
        if self.config_file:
            self.load_config()
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Validate configuration
        self.validate_config()
    
    def load_config(self) -> None:
        """
        Load configuration from file
        
        Raises:
            ConfigurationError: If config file is invalid
            FileAccessError: If config file cannot be read
        """
        if not self.config_file or not self.config_file.exists():
            logger.info("No configuration file found, using defaults")
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # Deep merge with defaults
            self._config = self._deep_merge(self.DEFAULT_CONFIG, user_config)
            logger.info(f"Loaded configuration from: {self.config_file}")
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                config_key=str(self.config_file),
                issue=f"Invalid JSON format: {str(e)}"
            )
        except Exception as e:
            raise FileAccessError(
                file_path=str(self.config_file),
                operation="read",
                reason=f"Failed to load config: {str(e)}"
            )
    
    def save_config(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """
        Save current configuration to file
        
        Args:
            file_path: Path to save config (if None, use current config file)
        """
        if file_path:
            self.config_file = Path(file_path)
        elif not self.config_file:
            self.config_file = self.base_dir / "tsconverter.json"
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved configuration to: {self.config_file}")
            
        except Exception as e:
            raise FileAccessError(
                file_path=str(self.config_file),
                operation="write",
                reason=f"Failed to save config: {str(e)}"
            )
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries
        
        Args:
            base: Base dictionary
            update: Dictionary to merge into base
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides"""
        env_mappings = {
            "TSCONVERTER_BASE_DIR": ["general", "base_dir"],
            "TSCONVERTER_OUTPUT_DIR": ["general", "output_dir"],
            "TSCONVERTER_LOG_LEVEL": ["general", "log_level"],
            "TSCONVERTER_STRICT_MODE": ["validation", "strict_mode"],
            "TSCONVERTER_MAX_WORKERS": ["general", "max_workers"]
        }
        
        for env_var, config_path in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Convert boolean strings
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                # Convert numeric strings
                elif value.isdigit():
                    value = int(value)
                
                # Set nested config value
                current = self._config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current[config_path[-1]] = value
                
                logger.debug(f"Applied environment override: {env_var} = {value}")
    
    def validate_config(self) -> None:
        """
        Validate configuration values
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Validate general settings
        if not isinstance(self._config.get("general", {}).get("max_workers"), int):
            raise ConfigurationError("general.max_workers", "Must be an integer")
        
        if self._config["general"]["max_workers"] < 1:
            raise ConfigurationError("general.max_workers", "Must be greater than 0")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = self._config.get("general", {}).get("log_level")
        if log_level not in valid_log_levels:
            raise ConfigurationError("general.log_level", f"Must be one of: {valid_log_levels}")
        
        # Validate paths
        base_dir = self.get("general.base_dir")
        if base_dir and not Path(base_dir).exists():
            logger.warning(f"Base directory does not exist: {base_dir}")
        
        # Validate file formats
        extensions = self.get("file_formats.supported_extensions")
        if not isinstance(extensions, list) or not extensions:
            raise ConfigurationError("file_formats.supported_extensions", "Must be non-empty list")
        
        logger.debug("Configuration validation passed")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'general.base_dir')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        current = self._config
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'general.base_dir')
            value: Value to set
        """
        keys = key.split('.')
        current = self._config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get_paths(self) -> Dict[str, Path]:
        """
        Get all configured paths as Path objects
        
        Returns:
            Dictionary of path configurations
        """
        base_dir = Path(self.get("general.base_dir", "."))
        
        return {
            "base_dir": base_dir,
            "output_dir": base_dir / self.get("general.output_dir", "output"),
            "input_dir": base_dir / self.get("general.input_dir", "input")
        }
    
    def get_step_config(self, step: str) -> Dict[str, Any]:
        """
        Get configuration for specific step
        
        Args:
            step: Step name (step1, step2, etc.)
            
        Returns:
            Step configuration dictionary
        """
        return self.get(step, {})
    
    def is_validation_strict(self) -> bool:
        """Check if validation is in strict mode"""
        return self.get("validation.strict_mode", True)
    
    def should_skip_format_validation(self) -> bool:
        """Check if format validation should be skipped"""
        return self.get("validation.skip_format_validation", False)
    
    def should_skip_structure_validation(self) -> bool:
        """Check if structure validation should be skipped"""
        return self.get("validation.skip_structure_validation", False)
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return self.get("file_formats.supported_extensions", [".xlsx"])
    
    def get_supported_mimetypes(self) -> List[str]:
        """Get list of supported MIME types"""
        return self.get("file_formats.supported_mimetypes", [])
    
    def get_max_file_size_mb(self) -> int:
        """Get maximum file size in MB"""
        return self.get("file_formats.max_file_size_mb", 100)
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return f"TSConverterConfig(base_dir={self.get('general.base_dir')}, config_file={self.config_file})"


# Global configuration instance
_global_config: Optional[TSConverterConfig] = None


def get_config() -> TSConverterConfig:
    """
    Get global configuration instance
    
    Returns:
        Global TSConverterConfig instance
    """
    global _global_config
    if _global_config is None:
        _global_config = TSConverterConfig()
    return _global_config


def set_config(config: TSConverterConfig) -> None:
    """
    Set global configuration instance
    
    Args:
        config: TSConverterConfig instance to set as global
    """
    global _global_config
    _global_config = config


def init_config(config_file: Optional[Union[str, Path]] = None, base_dir: Optional[str] = None) -> TSConverterConfig:
    """
    Initialize global configuration
    
    Args:
        config_file: Path to configuration file
        base_dir: Base directory for relative paths
        
    Returns:
        Initialized TSConverterConfig instance
    """
    global _global_config
    _global_config = TSConverterConfig(config_file, base_dir)
    return _global_config