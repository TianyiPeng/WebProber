import os
from dotenv import load_dotenv
from anthropic import Anthropic
from analyze_agent_run import analyze_agent_run

def generate_bug_report(log_file: str) -> str:
    # Load environment variables
    load_dotenv()
    
    # Initialize the Anthropic client
    client = Anthropic()
    
    # Generate the analysis messages
    messages = analyze_agent_run(log_file)
    
    # Get the analysis from Claude
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=1024,
        messages=messages
    )
    
    return response.content[0].text

if __name__ == "__main__":

    # Get all log files for Startup Website Testing tasks
    log_dir = "agent_logs"
    startup_logs = [f for f in os.listdir(log_dir) if f.startswith("agent_run_")]
    
    # Generate bug reports for each log file
    for log_file in startup_logs:
        log_path = os.path.join(log_dir, log_file)
        bug_report = generate_bug_report(log_path)
        
        # Create output filename based on log filename
        output_filename = log_file.replace("agent_run_", "bug_report_").replace(".log", ".md")
        
        # Save the bug report to a file
        output_dir = "bug_reports"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, output_filename)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(bug_report)
        
        print(f"Bug report has been generated and saved to {output_file}")