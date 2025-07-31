import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import base64
from PIL import Image
import io

class AgentRunAnalyzer:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.screenshot_dir = self._get_screenshot_dir()
        self.steps = []
        self.task = ""
        self._parse_log()

    def _get_screenshot_dir(self) -> str:
        # Extract task name from log filename
        match = re.search(r'agent_run_(.*?)\.log', self.log_file)
        if match:
            task_name = match.group(1)
            # Create a directory name that's safe for filesystem
            safe_task_name = re.sub(r'[^a-zA-Z0-9_-]', '_', task_name)
            return f"agent_screenshots/agent_screenshots_{safe_task_name}"
        return ""

    def _parse_log(self):
        with open(self.log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract task
        task_match = re.search(r'🚀 Starting task: (.*?)\n', content)
        if task_match:
            self.task = task_match.group(1)

        # Extract steps
        step_pattern = r'📍 Step (\d+)\n(.*?)(?=📍 Step \d+|$)'
        steps = re.finditer(step_pattern, content, re.DOTALL)
        
        for step in steps:
            step_num = int(step.group(1))
            step_content = step.group(2)
            
            # Extract evaluation
            eval_match = re.search(r'([👍👎🤷]) Eval: (.*?)\n', step_content)
            evaluation = eval_match.group(2) if eval_match else "Unknown"
            
            # Extract next goal
            goal_match = re.search(r'🎯 Next goal: (.*?)\n', step_content)
            next_goal = goal_match.group(1) if goal_match else ""
            
            # Extract actions
            action_match = re.search(r'🛠️  Action \d+/\d+: (.*?)\n', step_content)
            action = action_match.group(1) if action_match else ""
            
            # Get screenshot path
            screenshot_path = os.path.join(self.screenshot_dir, f"step_{step_num:03d}.png")
            
            self.steps.append({
                "step_number": step_num,
                "evaluation": evaluation,
                "next_goal": next_goal,
                "action": action,
                "screenshot_path": screenshot_path if os.path.exists(screenshot_path) else None
            })

    def _encode_screenshot(self, image_path: str) -> Optional[Dict]:
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (JPEG doesn't support RGBA)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Start with a reasonable size and compress until we're under 5MB
                max_size = (800, 800)
                quality = 85
                max_base64_size = 5 * 1024 * 1024  # 5MB in bytes
                
                while True:
                    # Create a copy to resize
                    img_copy = img.copy()
                    img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Convert to bytes with compression
                    img_byte_arr = io.BytesIO()
                    img_copy.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
                    img_byte_arr = img_byte_arr.getvalue()
                    
                    # Check if base64 size is under limit
                    base64_size = len(base64.b64encode(img_byte_arr))
                    if base64_size <= max_base64_size:
                        break
                    
                    # If still too large, reduce quality or size
                    if quality > 30:
                        quality -= 10
                    elif max_size[0] > 400:
                        max_size = (max_size[0] - 100, max_size[1] - 100)
                    else:
                        # If we can't compress further, skip this image
                        print(f"Warning: Could not compress image {image_path} to under 5MB, skipping")
                        return None
                
                # Encode to base64
                base64_data = base64.b64encode(img_byte_arr).decode('utf-8')
                
                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64_data
                    }
                }
        except Exception as e:
            print(f"Error encoding screenshot {image_path}: {e}")
            return None

    def generate_analysis_prompt(self) -> List[Dict]:
        # Start with the task description
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"""Task: {self.task}

You are a specialized web application bug detection agent. Your task is to analyze agent-website interaction trajectories and identify potential bugs, glitches, and usability issues in the target website.
IMPORTANT: Focus on website malfunctions, NOT agent errors. Distinguish between agent mistakes and actual website problems. A small note:  the web browser is lauched from an automated browser, so it is not always the website that is causing the issue.
For bugs, consider both feature bugs (missing or incorrect functionality) and glitch-like bugs (visual or behavioral anomalies). Also consider any functionality that is not working as expected, these are not striclty bugs, but could pose difficulties for the website users to navigate. One example is light colored text on a light background, which is hard to read. Note that the type of bug is not always obvious, so don't be afraid to make an assumption. For example, if the website does not support certain features that the agent is trying to use, that is a bug (e.g. the agent is trying to use the "add to cart" feature, but the website does not have a cart, or that the agent is searching in some language that the website does not support).

For each step, I'll provide:
0. The screenshot of the current browser state
1. The agent's evaluation of the step
2. The next goal
3. The action taken

Please analyze the entire sequence of steps and identify:
1. Any unexpected behaviors or errors of the website itself (*note: not the agent's actions*)
2. Missing or incorrect functionality
3. Visual glitches or UI inconsistencies
4. Any other anomalies that might indicate bugs
5. Any functionality that is not working as expected, these are not striclty bugs, but could pose difficulties for the website users to navigate. One example is light colored text on a light background, which is hard to read.
Here's the step-by-step trajectory:

"""
                }
            ]
        }]

        # Add each step with its screenshot and information
        for step in self.steps:
            step_content = []
            
            # Add screenshot if available
            if step['screenshot_path']:
                screenshot_data = self._encode_screenshot(step['screenshot_path'])
                if screenshot_data:
                    step_content.append(screenshot_data)
            
            # Add step information
            step_text = f"""
Step {step['step_number']}:
Evaluation: {step['evaluation']}
Next Goal: {step['next_goal']}
Action: {step['action']}
{'-' * 80}
"""
            step_content.append({
                "type": "text",
                "text": step_text
            })
            
            messages.append({
                "role": "user",
                "content": step_content
            })

        # Add the final analysis request
        messages.append({
            "role": "user",
            "content": [{
                "type": "text",
                "text": """
Based on the above trajectory, please provide:
1. A summary of any bugs or glitches identified
2. The specific steps where issues occurred
3. The nature of each issue (feature bug, visual glitch, etc.)
4. Any patterns or recurring problems
5. Recommendations for fixing the identified issues

For each identified issue, please specify:
- The step number where it occurred
- Whether it's a feature bug or visual glitch
- The severity of the issue
- The expected behavior vs actual behavior
"""
            }]
        })

        return messages

def analyze_agent_run(log_file: str) -> List[Dict]:
    analyzer = AgentRunAnalyzer(log_file)
    return analyzer.generate_analysis_prompt()

if __name__ == "__main__":
    # Example usage
    log_file = "agent_logs/agent_run_walmart.log"
    messages = analyze_agent_run(log_file)
    
    # Save the messages to a file for inspection
    output_file = "analysis_messages.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2)
    
    print(f"Analysis messages have been generated and saved to {output_file}")
    print("You can now feed these messages to the Anthropic API for analysis.") 