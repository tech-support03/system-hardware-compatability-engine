import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
from bs4 import BeautifulSoup
import json
import psutil
import platform
import subprocess
import threading
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# ============================================
# ENVIRONMENT VARIABLE API KEY MANAGEMENT
# ============================================

def get_api_key():
    """
    Get API key from environment variable.
    Priority order:
    1. GOOGLE_AI_API_KEY environment variable
    2. .env file (loaded by python-dotenv)
    3. Prompt user to set it
    """
    api_key = os.getenv('GOOGLE_AI_API_KEY')
    
    if api_key:
        return api_key
    
    # If no environment variable is set, show instructions
    show_env_setup_instructions()
    return None

def show_env_setup_instructions():
    """Show instructions for setting up the environment variable."""
    instructions = """
╔═══════════════════════════════════════════════════════════╗
║         GOOGLE AI API KEY NOT FOUND                       ║
╚═══════════════════════════════════════════════════════════╝

To use this app, you need to set the GOOGLE_AI_API_KEY environment variable.

📋 SETUP INSTRUCTIONS:

┌─────────────────────────────────────────────────────────┐
🪟 WINDOWS - Option 1: Permanent (Recommended)
└─────────────────────────────────────────────────────────┘

1. Press Win + R, type: sysdm.cpl
2. Go to "Advanced" tab → "Environment Variables"
3. Under "User variables", click "New"
4. Variable name: GOOGLE_AI_API_KEY
5. Variable value: [Paste your API key]
6. Click OK, restart this app

┌─────────────────────────────────────────────────────────┐
🪟 WINDOWS - Option 2: Command Prompt (Current Session)
└─────────────────────────────────────────────────────────┘

set GOOGLE_AI_API_KEY=your_api_key_here
python main.py

┌─────────────────────────────────────────────────────────┐
🪟 WINDOWS - Option 3: PowerShell (Current Session)
└─────────────────────────────────────────────────────────┘

$env:GOOGLE_AI_API_KEY="your_api_key_here"
python main.py

┌─────────────────────────────────────────────────────────┐
🐧 LINUX / 🍎 MAC - Permanent
└─────────────────────────────────────────────────────────┘

1. Open terminal
2. Edit your shell config file:
   - Bash: nano ~/.bashrc
   - Zsh: nano ~/.zshrc
3. Add this line:
   export GOOGLE_AI_API_KEY="your_api_key_here"
4. Save and run: source ~/.bashrc (or ~/.zshrc)
5. Restart this app

┌─────────────────────────────────────────────────────────┐
🐧 LINUX / 🍎 MAC - Current Session
└─────────────────────────────────────────────────────────┘

export GOOGLE_AI_API_KEY="your_api_key_here"
python main.py

┌─────────────────────────────────────────────────────────┐
📄 EASIEST METHOD: .env File (All Platforms)
└─────────────────────────────────────────────────────────┘

1. Create a file named ".env" in the same folder as this app
2. Add this line to the file:
   GOOGLE_AI_API_KEY=your_api_key_here
3. Save and restart the app

─────────────────────────────────────────────────────────

🔗 Get your API key from:
   https://aistudio.google.com/app/apikey

⚠️  After setting the environment variable, you MUST restart the app!
"""
    
    print(instructions)
    
    # Show GUI dialog too
    root = tk.Tk()
    root.withdraw()
    
    result = messagebox.askquestion(
        "API Key Setup Required",
        "No API key found in environment variables.\n\n"
        "Would you like to open the setup instructions in your browser?\n\n"
        "(Instructions have also been printed to the console)",
        icon='warning'
    )
    
    if result == 'yes':
        import webbrowser
        webbrowser.open("https://aistudio.google.com/app/apikey")
    
    root.destroy()

def setup_api_key():
    """Initialize and configure the API key from environment variable."""
    api_key = get_api_key()
    
    if not api_key:
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        return model
    except Exception as e:
        messagebox.showerror(
            "API Error", 
            f"Failed to initialize Google AI: {str(e)}\n\n"
            "Your API key might be invalid. Please check the GOOGLE_AI_API_KEY environment variable."
        )
        return None

# ============================================
# SYSTEM INFORMATION FUNCTIONS (WMIC REPLACED)
# ============================================

def run_powershell_command(command):
    """Run a PowerShell command and return the output."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"PowerShell command error: {e}")
        return ""

def get_monitor_resolution():
    """Get the monitor resolution."""
    try:
        root = tk.Tk()
        root.withdraw()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return f"{width}x{height}"
    except:
        return "Unknown"

def get_gpu_info_fixed():
    """Get GPU information using PowerShell."""
    gpu_name = "Unknown"
    
    virtual_keywords = ['parsec', 'virtual', 'remote', 'microsoft basic', 'vnc', 
                       'teamviewer', 'splashtop', 'citrix', 'vmware', 'hyper-v',
                       'generic pnp', 'rdp', 'standard vga']
    
    try:
        if platform.system() == "Windows":
            ps_command = """
            $gpu = Get-CimInstance Win32_VideoController | Where-Object {
                $_.Name -notmatch 'Parsec|Virtual|Remote|Microsoft Basic|Generic PnP|RDP|Standard VGA'
            } | Select-Object -First 1
            
            $result = @{
                Name = $gpu.Name
            }
            
            $result | ConvertTo-Json
            """
            
            gpu_info = run_powershell_command(ps_command)
            
            if gpu_info:
                try:
                    gpu_data = json.loads(gpu_info)
                    name = gpu_data.get('Name', '').strip()
                    name_lower = name.lower()
                    
                    # Check if it's a real GPU
                    if (name and 
                        ('amd' in name_lower or 'radeon' in name_lower or
                         'nvidia' in name_lower or 'geforce' in name_lower or
                         'intel' in name_lower and 'arc' in name_lower or
                         'intel' in name_lower and 'uhd' in name_lower or
                         'intel' in name_lower and 'iris' in name_lower or
                         'gtx' in name_lower or 'rtx' in name_lower or
                         'rx' in name_lower)):
                        
                        gpu_name = name
                        return gpu_name
                
                except json.JSONDecodeError:
                    print("Failed to parse GPU JSON data")
        
        elif platform.system() == "Linux":
            try:
                nvidia_info = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    encoding='utf-8'
                )
                gpu_name = nvidia_info.strip()
            except:
                lspci_info = subprocess.check_output(["lspci"], encoding='utf-8')
                for line in lspci_info.split('\n'):
                    if 'VGA' in line or 'Display' in line or '3D' in line:
                        line_lower = line.lower()
                        if not any(keyword in line_lower for keyword in virtual_keywords):
                            gpu_name = line.split(':')[-1].strip()
                            break
        
        elif platform.system() == "Darwin":
            gpu_info = subprocess.check_output(
                ["system_profiler", "SPDisplaysDataType"],
                encoding='utf-8'
            )
            for line in gpu_info.split('\n'):
                if 'Chipset Model:' in line:
                    gpu_name = line.split(':')[1].strip()
                    break
    
    except Exception as e:
        print(f"GPU detection error: {e}")
    
    return gpu_name

def get_cpu_info_windows():
    """Get CPU information using PowerShell instead of WMIC."""
    try:
        ps_command = "Get-CimInstance Win32_Processor | Select-Object Name | ConvertTo-Json"
        cpu_info = run_powershell_command(ps_command)
        
        if cpu_info:
            cpu_data = json.loads(cpu_info)
            
            # Handle both single CPU (dict) and multiple CPUs (list)
            if isinstance(cpu_data, dict):
                return cpu_data.get('Name', '').strip()
            elif isinstance(cpu_data, list) and len(cpu_data) > 0:
                return cpu_data[0].get('Name', '').strip()
    except Exception as e:
        print(f"CPU detection error: {e}")
    
    return platform.processor()

def get_system_specs():
    """Get relevant system specifications for gaming."""
    specs = {}
    
    specs['os'] = f"{platform.system()} {platform.release()}"
    specs['resolution'] = get_monitor_resolution()
    
    # Get CPU info
    specs['cpu'] = platform.processor()
    try:
        if platform.system() == "Windows":
            specs['cpu'] = get_cpu_info_windows()
        elif platform.system() == "Linux":
            cpu_info = subprocess.check_output(["cat", "/proc/cpuinfo"], 
                                              encoding='utf-8')
            for line in cpu_info.split('\n'):
                if "model name" in line:
                    specs['cpu'] = line.split(':')[1].strip()
                    break
        elif platform.system() == "Darwin":
            cpu_name = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], 
                                              encoding='utf-8').strip()
            specs['cpu'] = cpu_name
    except Exception as e:
        print(f"CPU info error: {e}")
    
    specs['cpu_cores'] = psutil.cpu_count(logical=False)
    specs['cpu_threads'] = psutil.cpu_count(logical=True)
    
    specs['gpu'] = get_gpu_info_fixed()
    
    svmem = psutil.virtual_memory()
    specs['ram_total_gb'] = round(svmem.total / (1024**3), 2)
    
    try:
        disk = psutil.disk_usage('/')
        specs['storage_free_gb'] = round(disk.free / (1024**3), 2)
    except:
        specs['storage_free_gb'] = "Unknown"
    
    return specs

# ============================================
# STEAM API FUNCTIONS
# ============================================

def search_game_by_name(game_name):
    """Search for a game by name and return matching results with app IDs."""
    url = "https://steamcommunity.com/actions/SearchApps/" + game_name
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        results = response.json()
        
        if not results:
            return []
        
        return [{"app_id": game['appid'], "name": game['name']} for game in results]
        
    except:
        return []

def get_game_requirements(app_id):
    """Get system requirements for a Steam game using the official API."""
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if not data[str(app_id)]['success']:
            return {"error": "Game not found or data unavailable"}
        
        game_data = data[str(app_id)]['data']
        
        result = {
            "name": game_data.get('name', 'Unknown'),
            "app_id": app_id,
            "type": game_data.get('type', 'Unknown'),
            "is_free": game_data.get('is_free', False),
        }
        
        pc_req = game_data.get('pc_requirements', {})
        if pc_req:
            result['pc_requirements'] = {
                'minimum': pc_req.get('minimum', 'Not specified'),
                'recommended': pc_req.get('recommended', 'Not specified')
            }
        
        return result
        
    except:
        return {"error": "Failed to fetch game data"}

def clean_html_requirements(html_text):
    """Clean HTML from requirements text to make it more readable."""
    if not html_text or html_text == 'Not specified':
        return html_text
    
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text(separator='\n', strip=True)

def format_requirements_for_ai(requirements):
    """Format the requirements data into a clean string for the AI."""
    if "error" in requirements:
        return f"Error: {requirements['error']}"
    
    formatted = f"GAME REQUIREMENTS FOR: {requirements['name']}\n"
    formatted += "=" * 50 + "\n"
    
    if 'pc_requirements' in requirements:
        if requirements['pc_requirements']['minimum'] != 'Not specified':
            formatted += "\nMinimum Requirements:\n"
            formatted += clean_html_requirements(requirements['pc_requirements']['minimum']) + "\n"
        
        if requirements['pc_requirements']['recommended'] != 'Not specified':
            formatted += "\nRecommended Requirements:\n"
            formatted += clean_html_requirements(requirements['pc_requirements']['recommended']) + "\n"
    
    return formatted

def format_system_specs(specs):
    """Format system specs into readable text."""
    formatted = "YOUR PC SPECS:\n"
    formatted += "=" * 50 + "\n"
    formatted += f"OS: {specs.get('os', 'Unknown')}\n"
    formatted += f"Monitor Resolution: {specs.get('resolution', 'Unknown')}\n"
    formatted += f"CPU: {specs.get('cpu', 'Unknown')}\n"
    formatted += f"CPU Cores/Threads: {specs.get('cpu_cores', '?')}/{specs.get('cpu_threads', '?')}\n"
    formatted += f"GPU: {specs.get('gpu', 'Unknown')}\n"
    formatted += f"RAM: {specs.get('ram_total_gb', '?')} GB\n"
    formatted += f"Free Storage: {specs.get('storage_free_gb', '?')} GB\n"
    return formatted

def compare_specs_with_ai(game_name, requirements_text, system_specs_text, system_specs, model):
    """Send both game requirements and system specs to Google AI for comparison."""
    prompt = f"""{system_specs_text}

{requirements_text}

Question: Can my PC run {game_name}? Please compare my system specs against the game's requirements and tell me:
1. What performance I can expect at my monitor resolution ({system_specs.get('resolution', 'unknown')})
2. What graphics settings I should use (low/medium/high/ultra)
3. Estimated FPS range I can expect"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error querying Google AI: {str(e)}"

# ============================================
# GUI CODE
# ============================================

def run_check(event=None):
    game = game_entry.get()
    if game.strip() == "":
        output_box.insert(tk.END, "Please enter a game name.\n\n")
        return
    
    output_box.delete(1.0, tk.END)
    output_box.insert(tk.END, f"Checking compatibility for: {game}\n")
    output_box.insert(tk.END, "=" * 60 + "\n\n")
    
    thread = threading.Thread(target=check_compatibility, args=(game,))
    thread.daemon = True
    thread.start()

def check_compatibility(game_name):
    """Main compatibility check function that runs in a separate thread."""
    try:
        output_box.insert(tk.END, "Detecting system specifications...\n")
        output_box.see(tk.END)
        system_specs = get_system_specs()
        
        output_box.insert(tk.END, f"Searching for '{game_name}' on Steam...\n")
        output_box.see(tk.END)
        search_results = search_game_by_name(game_name)
        
        if not search_results:
            output_box.insert(tk.END, "\nNo games found! Please check the spelling.\n\n")
            return
        
        output_box.insert(tk.END, f"Found {len(search_results)} result(s). Using: {search_results[0]['name']}\n")
        output_box.see(tk.END)
        
        output_box.insert(tk.END, "Fetching game requirements...\n")
        output_box.see(tk.END)
        requirements = get_game_requirements(search_results[0]['app_id'])
        
        if "error" in requirements:
            output_box.insert(tk.END, f"\nError: {requirements['error']}\n\n")
            return
        
        req_text = format_requirements_for_ai(requirements)
        specs_text = format_system_specs(system_specs)
        
        output_box.insert(tk.END, "\n" + req_text + "\n")
        output_box.see(tk.END)
        
        output_box.insert(tk.END, "Analyzing compatibility with AI...\n")
        output_box.insert(tk.END, "=" * 60 + "\n")
        output_box.see(tk.END)
        
        ai_response = compare_specs_with_ai(
            search_results[0]['name'],
            req_text,
            specs_text,
            system_specs,
            ai_model
        )
        
        output_box.insert(tk.END, "\nAI COMPATIBILITY ANALYSIS:\n")
        output_box.insert(tk.END, "=" * 60 + "\n")
        output_box.insert(tk.END, ai_response + "\n\n")
        output_box.see(tk.END)
        
    except Exception as e:
        output_box.insert(tk.END, f"\nError: {str(e)}\n\n")

def show_specs():
    """Display system specifications."""
    output_box.delete(1.0, tk.END)
    output_box.insert(tk.END, "Detecting system specifications...\n\n")
    
    specs = get_system_specs()
    
    output_box.insert(tk.END, "--- SYSTEM SPECS ---\n")
    output_box.insert(tk.END, "=" * 60 + "\n")
    output_box.insert(tk.END, f"OS: {specs.get('os', 'Unknown')}\n")
    output_box.insert(tk.END, f"Resolution: {specs.get('resolution', 'Unknown')}\n")
    output_box.insert(tk.END, f"CPU: {specs.get('cpu', 'Unknown')}\n")
    output_box.insert(tk.END, f"CPU Cores/Threads: {specs.get('cpu_cores', '?')}/{specs.get('cpu_threads', '?')}\n")
    output_box.insert(tk.END, f"GPU: {specs.get('gpu', 'Unknown')}\n")
    output_box.insert(tk.END, f"RAM: {specs.get('ram_total_gb', '?')} GB\n")
    output_box.insert(tk.END, f"Free Storage: {specs.get('storage_free_gb', '?')} GB\n")
    output_box.insert(tk.END, "=" * 60 + "\n\n")

def main():
    global ai_model, game_entry, output_box
    
    # Setup API key from environment variable
    ai_model = setup_api_key()
    
    if not ai_model:
        messagebox.showerror(
            "Startup Failed", 
            "Cannot start without a valid API key.\n\n"
            "Please set the GOOGLE_AI_API_KEY environment variable.\n"
            "Check the console for detailed instructions."
        )
        return
    
    window = tk.Tk()
    window.title("System Hardware Compatibility Checker")
    window.geometry("900x600")
    window.configure(bg="black")

    title = tk.Label(window, text="System Hardware Compatibility Checker",
                     font=("Arial", 18), fg="white", bg="black")
    title.pack(pady=10)

    input_frame = tk.Frame(window, bg="black")
    input_frame.pack(pady=10)

    game_label = tk.Label(input_frame, text="Enter Game Name:", fg="white", bg="black")
    game_label.grid(row=0, column=0, padx=5)

    game_entry = tk.Entry(input_frame, width=40)
    game_entry.grid(row=0, column=1, padx=5)
    game_entry.focus_set()

    window.bind("<Return>", run_check)

    press_label = tk.Label(window, text="Press Enter to check compatibility",
                           fg="white", bg="black")
    press_label.pack(pady=5)

    specs_btn = tk.Button(window, text="Show System Specs", command=show_specs,
                         bg="#333333", fg="white", activebackground="#555555")
    specs_btn.pack(pady=5)

    output_box = scrolledtext.ScrolledText(window, width=140, height=50,
                                           bg="black", fg="white",
                                           insertbackground="white",
                                           font=("Consolas", 9))
    output_box.pack(pady=10)

    window.mainloop()

ai_model = None
game_entry = None
output_box = None

if __name__ == "__main__":
    main()