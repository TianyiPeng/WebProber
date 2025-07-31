# login_handlers.py
from browser_use.browser.context import BrowserContext
from browser_use.agent.service import Agent
import asyncio
import logging

logger = logging.getLogger(__name__)

class LoginHandlers:
    @staticmethod
    async def login_google(context: BrowserContext, username: str, password: str):
        """Handle Google login flow"""
        page = await context.get_current_page()
        logger.info("Starting Google login process")

        try:
            await page.goto("https://accounts.google.com")
            await page.wait_for_selector('input[type="email"]', timeout=10000)
            
            # Enter email
            await page.fill('input[type="email"]', username)
            await page.click("#identifierNext")

            # Wait for password field
            await page.wait_for_selector('input[type="password"]', timeout=10000)
            await page.fill('input[type="password"]', password)
            await page.click("#passwordNext")
            
            # Wait for successful login
            await page.wait_for_load_state('networkidle',timeout=30000)
            # Handle 2FA if needed
            if "challenge" in page.url:
                logger.warning("2FA required - manual intervention needed")
                input("Please complete 2FA and press Enter...")
            return True
            
        except Exception as e:
            logger.error(f"Google login failed: {e}")
            return False
    
    @staticmethod
    async def login_amazon(context: BrowserContext, username: str, password: str):
        """Handle Amazon login flow"""
        page = await context.get_current_page()
        
        try:
            await page.goto("https://www.amazon.com/ap/signin")
            await page.wait_for_selector('input[name="email"]', timeout=10000)
            
            # Enter email
            await page.fill('input[name="email"]', username)
            await page.click("#continue")
            
            # Enter password
            await page.wait_for_selector('input[name="password"]', timeout=10000)
            await page.fill('input[name="password"]', password)
            await page.click("#signInSubmit")
            
            # Wait for successful login
            await page.wait_for_navigation(timeout=30000)
            
            return True
            
        except Exception as e:
            logger.error(f"Amazon login failed: {e}")
            return False