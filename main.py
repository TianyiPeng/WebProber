# main.py
from browser_use.agent.service import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
import asyncio
from dotenv import load_dotenv
from auth_manager import SecureAuthManager
from login_handlers import LoginHandlers
from sacred import Experiment
from sacred.observers import FileStorageObserver
import yaml
import os

# Initialize Sacred experiment
ex = Experiment('browser-use')
#ex.observers.append(FileStorageObserver('runs'))

@ex.config
def config():
    # Load default configuration from YAML
    config_path = 'configs/config.yaml'
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Define Sacred variables from config
    browser = config_data['browser']
    context = config_data['context']
    llm = config_data['llm']
    tasks_file = config_data['tasks_file']
    agent = config_data.get('agent', {'max_steps': 100})  # Default to 100 if not specified
    auth_manager = config_data.get('auth_manager', {'save_auth_state': False})

class BrowserManager:
    def __init__(self, browser_config, context_config, auth_manager_config):
        self.browser_config = browser_config
        self.context_config = context_config
        self.auth_manager_config = auth_manager_config
        self.auth_manager = SecureAuthManager(browser_config['test_profile_name'])

    async def setup_authenticated_browser(self):
        """Set up browser with test account authentication"""
        
        # Configure browser
        browser_config = BrowserConfig(
            headless=self.browser_config['headless'],
            use_test_profile=self.browser_config['use_test_profile'],
            test_profile_name=self.browser_config['test_profile_name'],
            extra_browser_args=self.browser_config['extra_browser_args'],
        )
        
        # Configure context with security settings
        context_config = BrowserContextConfig(
            disable_security=self.context_config['disable_security'],
            cookies_file=self.context_config['cookies_file'],
            user_agent=self.context_config['user_agent'],
            permissions=self.context_config['permissions'],
            allowed_domains=self.context_config['allowed_domains'],
        )

        browser = Browser(config=browser_config)
        context = await browser.new_context(config=context_config)
        
        # Check if we need to login
        if self.auth_manager_config['ensure_logged_in']:
            await self.ensure_logged_in(context)
        return browser, context

    async def ensure_logged_in(self, context):
        """Ensure we're logged into required services"""
        
        # Try to load existing auth
        google_auth_loaded = await self.auth_manager.load_auth_state(context, "google")
        if google_auth_loaded:
            print("Google already logged in")
        if not google_auth_loaded:
            # Need to login
            username, password = self.auth_manager.get_credentials("google")
            success = await LoginHandlers.login_google(context, username, password)
            print("Logged in to Google")
            
            if success:
                await self.auth_manager.save_auth_state(context, "google")
            else:
                raise Exception("Failed to login to Google")

def create_llm(llm_config):
    """Create LLM instance based on provider configuration"""
    provider = llm_config.get('provider', 'openai').lower()
    model = llm_config['model']
    
    # Common LLM parameters
    common_params = {
        'temperature': llm_config.get('temperature', 0.0),
        'max_tokens': llm_config.get('max_tokens', None),
    }
    
    if provider == 'anthropic':
        # Check for Anthropic API key
        if not os.getenv('ANTHROPIC_API_KEY'):
            raise ValueError("ANTHROPIC_API_KEY environment variable is required for Anthropic provider")
        
        anthropic_params = {
            'model': model,
            **common_params
        }
        return ChatAnthropic(**anthropic_params)
    
    elif provider == 'openai':
        # Check for OpenAI API key
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI provider")
        
        openai_params = {
            'model': model,
            **common_params
        }
        return ChatOpenAI(**openai_params)
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported providers: 'anthropic', 'openai'")

async def run_tasks(browser_config, context_config, llm_config, tasks_file, agent_config, auth_manager_config):
    load_dotenv()
    
    print(f"=== Starting task execution session ===")
    
    browser = None
    browser_context = None
    
    try:
        # Set up browser manager
        browser_manager = BrowserManager(browser_config, context_config, auth_manager_config)
        
        # Set up authenticated browser
        browser, browser_context = await browser_manager.setup_authenticated_browser()
        print("Browser and context initialized, ready to run tasks")
        
        # Create LLM instance based on configuration
        llm = create_llm(llm_config)
        print(f"Using {llm_config.get('provider', 'openai').upper()} provider with model: {llm_config['model']}")
        
        # Read tasks
        task_count = 0
        print(f"Reading tasks from: {tasks_file}")
        
        with open(tasks_file, "r") as f:
            tasks = [line.strip() for line in f if line.strip()]
            print(f"Found {len(tasks)} tasks to process")
            
            for line in tasks:
                task_count += 1
                name, task = line.split(":", 1)
                print(f"[{task_count}/{len(tasks)}] Running task: {name} - {task.strip()}")
                
                # Create agent with authenticated browser and dynamic LLM
                agent = Agent(
                    task=task,
                    llm=llm,
                    task_name=name,
                    browser=browser,
                    browser_context=browser_context,
                    # Agent configuration from YAML
                    max_failures=agent_config.get('max_failures', 3),
                    retry_delay=agent_config.get('retry_delay', 10),
                    use_vision=agent_config.get('use_vision', True),
                    enable_memory=agent_config.get('enable_memory', True),
                    max_actions_per_step=agent_config.get('max_actions_per_step', 10)
                )
                
                try:
                    await agent.run(max_steps=agent_config['max_steps'])
                except Exception as e:
                    print(f"Error running task '{name}': {e}")
                finally:
                    # Save auth state after each task
                    if auth_manager_config.get('save_auth_state', False):
                        try:
                            await browser_manager.auth_manager.save_auth_state(browser_context, "google")
                        except Exception as e:
                            print(f"Warning: Failed to save auth state: {e}")
                    
                    # Clean up agent resources
                    try:
                        await agent.close()
                    except Exception as e:
                        print(f"Warning: Failed to close agent: {e}")
    
    finally:
        # Ensure proper cleanup of browser resources
        if browser_context:
            try:
                await browser_context.close()
                print("Browser context closed successfully")
            except Exception as e:
                print(f"Warning: Failed to close browser context: {e}")
        
        if browser:
            try:
                await browser.close()
                print("Browser closed successfully")
            except Exception as e:
                print(f"Warning: Failed to close browser: {e}")

@ex.automain
def main(browser, context, llm, tasks_file, agent, auth_manager):
    asyncio.run(run_tasks(browser, context, llm, tasks_file, agent, auth_manager))
      