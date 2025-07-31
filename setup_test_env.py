# setup_test_env.py
import asyncio
from auth_manager import SecureAuthManager
import getpass

async def setup_test_accounts():
    """One-time setup for test accounts"""
    
    auth_manager = SecureAuthManager("test_profile")
    
    print("Setting up test accounts...")
    print("Please use dedicated test accounts, NOT your personal accounts!")
    print("-" * 50)
    
    # Google test account
    print("\nGoogle Test Account:")
    google_email = input("Email: ")
    google_pass = getpass.getpass("Password: ")
    auth_manager.store_test_credentials("google", google_email, google_pass)
    
    # Huggingface test account
    print("\nHuggingface Test Account:")
    huggingface_email = input("Email: ")
    huggingface_pass = getpass.getpass("Password: ")
    auth_manager.store_test_credentials("huggingface", huggingface_email, huggingface_pass)

    # Outlook test account
    print("\nOutlook Test Account:")
    outlook_email = input("Email: ")
    outlook_pass = getpass.getpass("Password: ")
    auth_manager.store_test_credentials("outlook", outlook_email, outlook_pass)

    # Github test account
    print("\nGithub Test Account:")
    github_email = input("Email: ")
    github_pass = getpass.getpass("Password: ")
    auth_manager.store_test_credentials("github", github_email, github_pass)

    
    print("\nTest accounts configured successfully!")
    print("Remember to enable 2FA on these accounts for extra security.")

if __name__ == "__main__":
    asyncio.run(setup_test_accounts())