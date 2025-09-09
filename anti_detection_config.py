"""
Anti-detection configuration for Hyperbrowser sessions
Implements stealth mode, proxy rotation, and bot prevention measures
"""

import random
import json
from typing import Dict, Any, Optional
from pathlib import Path
from hyperbrowser.models import StartClaudeComputerUseTaskParams
from utils import get_logger

logger = get_logger("AntiDetection")

class AntiDetectionConfig:
    """Manages anti-detection configurations for browser sessions"""
    
    def __init__(self, config_file: str = "user/platform_configs.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load platform configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_file}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing configuration file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default anti-detection configuration"""
        return {
            "platforms": {},
            "global_settings": {
                "max_concurrent_browsers": 3,
                "rate_limit_delay": "1-3"
            }
        }
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """Get configuration for a specific platform"""
        platforms = self.config.get("platforms", {})
        return platforms.get(platform, {})
    
    def get_anti_detection_params(self, platform: str) -> Dict[str, Any]:
        """Generate anti-detection parameters for Hyperbrowser session"""
        platform_config = self.get_platform_config(platform)
        anti_detection = platform_config.get("anti_detection", {})
        
        # Base parameters
        params = {
            "use_stealth": anti_detection.get("stealth_mode", True),
            "keep_browser_open": True
        }
        
        # Device and OS configuration
        device = anti_detection.get("device", "desktop")
        os_type = anti_detection.get("operating_system", "macos")
        locale = anti_detection.get("locale", "en-US")
        
        params.update({
            "device": [device],
            "operating_systems": [os_type],
            "locales": [locale]
        })
        
        # Screen configuration
        screen_config = anti_detection.get("screen", {})
        if screen_config:
            params["screen"] = {
                "width": screen_config.get("width", 1920),
                "height": screen_config.get("height", 1080)
            }
        
        # Proxy configuration
        if anti_detection.get("use_proxy", False):
            params["use_proxy"] = True
            proxy_country = anti_detection.get("proxy_country", "US")
            params["proxy_country"] = proxy_country
            
            # Optional proxy city
            proxy_city = anti_detection.get("proxy_city")
            if proxy_city:
                params["proxy_city"] = proxy_city
                
        logger.debug(f"Generated anti-detection params for {platform}: {params}")
        return params
    
    def get_randomized_params(self, platform: str) -> Dict[str, Any]:
        """Get randomized anti-detection parameters to vary fingerprint"""
        base_params = self.get_anti_detection_params(platform)
        
        # Randomize screen resolution slightly
        if "screen" in base_params:
            base_width = base_params["screen"]["width"]
            base_height = base_params["screen"]["height"]
            
            # Vary by ±50 pixels
            width_variation = random.randint(-50, 50)
            height_variation = random.randint(-50, 50)
            
            base_params["screen"]["width"] = max(1024, base_width + width_variation)
            base_params["screen"]["height"] = max(768, base_height + height_variation)
        
        # Randomly vary locale for some diversity
        locales = ["en-US", "en-CA", "en-GB"]
        base_params["locales"] = [random.choice(locales)]
        
        # Randomly vary device profiles occasionally  
        if random.random() < 0.2:
            os_options = ["macos", "windows", "linux"]
            current_os = base_params["operating_systems"][0]
            # 20% chance to use different OS
            base_params["operating_systems"] = [random.choice(os_options)]
        
        return base_params
    
    def get_delay_range(self, platform: str) -> tuple[int, int]:
        """Get delay range for actions on this platform"""
        platform_config = self.get_platform_config(platform)
        delay_str = platform_config.get("delay_between_actions", "2-8")
        
        try:
            min_delay, max_delay = map(int, delay_str.split("-"))
            return (min_delay, max_delay)
        except (ValueError, AttributeError):
            logger.warning(f"Invalid delay format for {platform}: {delay_str}")
            return (2, 8)
    
    def get_random_delay(self, platform: str) -> int:
        """Get a random delay in seconds for this platform"""
        min_delay, max_delay = self.get_delay_range(platform)
        return random.randint(min_delay, max_delay)
    
    def is_platform_enabled(self, platform: str) -> bool:
        """Check if a platform is enabled in configuration"""
        platform_config = self.get_platform_config(platform)
        return platform_config.get("enabled", False)
    
    def requires_login(self, platform: str) -> bool:
        """Check if platform requires login"""
        platform_config = self.get_platform_config(platform)
        return platform_config.get("requires_login", False)
    
    def get_max_applications(self, platform: str) -> int:
        """Get maximum applications allowed per session for this platform"""
        platform_config = self.get_platform_config(platform)
        return platform_config.get("max_applications_per_session", 3)
    
    def get_session_timeout(self, platform: str) -> int:
        """Get session timeout in seconds for this platform"""
        platform_config = self.get_platform_config(platform)
        return platform_config.get("session_timeout", 1200)
    
    def get_enabled_platforms(self) -> list[str]:
        """Get list of enabled platforms sorted by priority"""
        platforms = self.config.get("platforms", {})
        enabled = []
        
        for platform_key, config in platforms.items():
            if config.get("enabled", False):
                priority = config.get("priority", 999)
                enabled.append((priority, platform_key))
        
        # Sort by priority and return platform names
        enabled.sort(key=lambda x: x[0])
        return [platform for _, platform in enabled]
    
    def get_global_setting(self, key: str, default: Any = None) -> Any:
        """Get a global configuration setting"""
        global_settings = self.config.get("global_settings", {})
        return global_settings.get(key, default)
    
    def get_search_url(self, platform: str) -> str:
        """Get search URL for a platform"""
        platform_config = self.get_platform_config(platform)
        return platform_config.get("search_url", "")
    
    def get_platform_name(self, platform: str) -> str:
        """Get display name for a platform"""
        platform_config = self.get_platform_config(platform)
        return platform_config.get("name", platform.title())