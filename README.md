# WebProber: AI Agent for web testing

WebProber is an initial implementation and research framework for AI-driven web testing based on `browser-use (https://github.com/browser-use/browser-use)`. This executable framework provides template-based prompts and a foundation for building intelligent web testing systems that can automatically discover usability issues and bugs. WebProber operates through a three-stage pipeline that you can customize: 
1. **Task prompt generation:** we provide a template in `task.txt` that you can customize for your target website URL and type. 

2. **Interaction simulation:** An AI agent controls the browser using visual language models for intelligent decision-making and web navigation 

3. **Bug report generation:** We provide a code snippet for generating comprehensive bug reports, with a engineered prompt in `analyze_agent_run.py`.

## Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/TianyiPeng/WebProber.git
cd WebProber

# Install dependencies
uv sync
```

### Environment Setup

Create a `.env` file in the project root with your API keys:

```bash
# For Anthropic (Claude)
ANTHROPIC_API_KEY=your_anthropic_key_here

# For OpenAI (GPT)
OPENAI_API_KEY=your_openai_key_here
```

## Quick Start

1. **Configure your settings** by editing `configs/config.yaml`:
   - Choose your LLM provider (OpenAI or Anthropic)
   - Set browser preferences
   - Configure authentication if needed

2. **Create a tasks file** (e.g., `task.txt`) with tasks in the format:
   ```
   task1: Navigate to Google and search for "AI news"
   task2: Go to GitHub and find trending Python repositories
   ```

3. **Run your first automation**:
```bash
uv run main.py
```

The agent will open a browser, execute your tasks with AI-powered decision making, and provide detailed logs of its actions in `agent_logs/` and `agent_screenshots/`.

4. **Generate bug report**:
```bash
uv run generate_bug_report.py
```

This will generate a bug report in the `bug_reports/` directory.

## Detailed Usage

### 1. Configuration

The main configuration is handled through `configs/config.yaml`:

#### Browser Settings
```yaml
browser:
  headless: false              # Set to true for headless operation
  use_test_profile: true       # Use persistent browser profile
  test_profile_name: "test_profile"
  extra_browser_args:
    - "--disable-blink-features=AutomationControlled"
```

#### LLM Configuration
```yaml
llm:
  provider: "anthropic"        # "anthropic" or "openai"
  model: "claude-3-7-sonnet-20250219"
  temperature: 0.7
  max_tokens: 1000
```

#### Agent Behavior
```yaml
agent:
  max_steps: 25               # Maximum steps per task
  max_failures: 3             # Max consecutive failures
  use_vision: true            # Enable screenshot analysis
  enable_memory: true         # Enable long-term memory
  max_actions_per_step: 10    # Max actions per step
```

### 2. Task Definition

Tasks are defined in a text file (default: `task.txt`) with the format:
```
task_name: Task description
```

Examples:
```
search_ai: Navigate to Google and search for "latest AI developments"
github_trending: Go to GitHub trending page and find top Python repositories
amazon_product: Search Amazon for "wireless headphones" and compare top 3 products
```

### 3. Setup Environment (One-time)

Run the setup script to configure authentication:
```bash
uv run setup_test_env.py
```

This script will:
- Prompt you to input login credentials for automated processing
- Save browser cookies for future launches

### 4. Run the Agent

Execute the main script:
```bash
uv run main.py
```

The script will:
- Load configuration from `configs/config.yaml`
- Potnetially load saved cookies
- Read tasks from the configured task file
- Execute each task using the AI agent with your configured settings
- Generate logs in the `agent_logs/` directory
- Capture screenshots in the `agent_screenshots/` directory


### 5. Generate Bug Reports

Run the bug report generation pipeline:
```bash
uv run generate_bug_report.py
```
This generates bug reports in the `bug_reports/` directory - change the specific task to generate a report on.


### Logging and Debugging

WebProber provides comprehensive logging:

- **Agent logs**: Saved to `agent_logs/agent_run_{task_name}.log`
- **Screenshots**: Saved to `agent_screenshots/agent_screenshots_{task_name}/`
- **Browser state**: Detailed DOM and interaction logs

### Security Features

- **Domain restrictions**: Configure allowed domains in `config.yaml`
- **Secure credential storage**: Encrypted authentication data
- **Safe browser profiles**: Isolated test environments
- **Sensitive data protection**: Automatic redaction of sensitive information

