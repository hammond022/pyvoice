import json
import os
import logging

CONFIG_FILE = "config.json"
logger = logging.getLogger(__name__)

def validate_config(config):
    """Validate the configuration data structure"""
    required_types = {
        'telegram_token': str,
        'keywords': list,
        'keyword_data': dict
    }
    
    for key, expected_type in required_types.items():
        if key in config and not isinstance(config[key], expected_type):
            raise ValueError(f"Config validation error: {key} must be of type {expected_type.__name__}")
    
    return True

def save_config(telegram_token=None, keywords=None, keyword_data=None):
    try:
        # Load existing config first
        existing_config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                existing_config = json.load(f)
        
        # Update only the provided values
        if telegram_token:
            existing_config['telegram_token'] = telegram_token
        if keywords is not None:
            existing_config['keywords'] = keywords
        if keyword_data is not None:
            existing_config['keyword_data'] = keyword_data
            
        validate_config(existing_config)
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(existing_config, f, indent=4)
        logger.info("Configuration saved successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to save configuration: {str(e)}")
        return False

def load_config():
    if not os.path.exists(CONFIG_FILE):
        logger.warning("Config file not found, using defaults")
        return None, [], {}
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        validate_config(config)
        
        token = config.get('telegram_token')
        if token:
            token = token.strip().replace('\n', '').replace('\r', '')
            
        return (
            token,
            config.get('keywords', []),
            config.get('keyword_data', {})
        )
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {str(e)}")
        return None, [], {}
    except ValueError as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        return None, [], {}
    except Exception as e:
        logger.error(f"Unexpected error loading config: {str(e)}")
        return None, [], {}
