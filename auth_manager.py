import os
import time
import json
import logging
from typing import Dict, Optional
from pathlib import Path
import keyring
from cryptography.fernet import Fernet
from browser_use.browser.context import BrowserContext

logger = logging.getLogger(__name__)

class SecureAuthManager:
    def __init__(self, profile_name: str = "test_profile"):
        self.profile_name = profile_name
        self.auth_dir = Path("auth_data") / profile_name
        self.auth_dir.mkdir(parents=True, exist_ok=True)
        
        # Use keyring for secure credential storage
        self.service_name = f"browser_use_{profile_name}"
        
    def store_test_credentials(self, site: str, username: str, password: str):
        """Securely store test account credentials"""
        keyring.set_password(self.service_name, f"{site}_user", username)
        keyring.set_password(self.service_name, f"{site}_pass", password)
        logger.info(f"Stored credentials for {site}")
    
    def get_credentials(self, site: str) -> tuple[str, str]:
        """Retrieve test account credentials"""
        username = keyring.get_password(self.service_name, f"{site}_user")
        password = keyring.get_password(self.service_name, f"{site}_pass")
        if not username or not password:
            raise ValueError(f"No credentials found for {site}")
        return username, password
    
    async def save_auth_state(self, context: BrowserContext, site: str):
        """Save authentication state after successful login"""
        auth_file = self.auth_dir / f"{site}_auth.json"
        
        # Get cookies and local storage
        cookies = await context.session.context.cookies()
        
        # Save to encrypted file
        auth_data = {
            "cookies": cookies,
            "timestamp": time.time()
        }
        
        # Encrypt the data
        key = self._get_or_create_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(json.dumps(auth_data).encode())
        
        auth_file.write_bytes(encrypted)
        logger.info(f"Saved auth state for {site}")
    
    async def load_auth_state(self, context: BrowserContext, site: str) -> bool:
        """Load saved authentication state"""
        auth_file = self.auth_dir / f"{site}_auth.json"
        
        if not auth_file.exists():
            return False
        
        try:
            # Decrypt the data
            key = self._get_or_create_key()
            fernet = Fernet(key)
            encrypted = auth_file.read_bytes()
            auth_data = json.loads(fernet.decrypt(encrypted).decode())
            print(f"Auth data: {auth_data}")
            
            # Check if auth is still fresh (e.g., less than 7 days old)
            if time.time() - auth_data["timestamp"] > 7 * 24 * 3600:
                logger.info(f"Auth state for {site} is too old")
                return False
            # Load cookies
            session = await context.get_session()
            await session.context.add_cookies(auth_data["cookies"])
            logger.info(f"Loaded auth state for {site}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load auth state: {e}")
            return False
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        key_file = self.auth_dir / ".key"
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            return key