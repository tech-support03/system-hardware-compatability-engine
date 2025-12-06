import tkinter as tk
from tkinter import scrolledtext
import requests
from bs4 import BeautifulSoup
import json
import psutil
import platform
import subprocess
import threading
import google.generativeai as genai

# Configure Google AI Studio API
# Get your API key from: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY = "AIzaSyD-D9AOuFf0FC-fd570njCW5q21S8aCMxU"  # Replace with your actual API key
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the model
model = genai.GenerativeModel('gemini-flash-2.5')

def get_monitor_resolution():import tkinter as tk
from tkinter import scrolledtext
import requests
from bs4 import BeautifulSoup
import psutil
import platform
import subprocess
import threading
import google.generativeai as genai

# Configure Google AI Studio API
GOOGLE_API_KEY = "your-api-key-here"  # Replace with your actual API key
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def get_cpu_name():
    """Get CPU name with improved detection."""
    try:
        if platform.system() == "Windows":
            import wmi
            c = wmi.WMI()
            for processor in c.Win32_Processor():
                return processor.Name
        elif platform.system() == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(':')[1].strip()
        elif platform.system() == "Darwin":  # macOS
            cpu = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], 
                                         encoding='utf-8').strip()
            return cpu
    except:
        pass
    return platform.processor() or "Unknown CPU"

def get_gpu_name():
    """Get GPU name with improved detection."""
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            return gpus[0].name, f"{gpus[0].memoryTotal}MB"
    except:
        pass
    
    try:
        if platform.system() == "Windows":
            gpu = subprocess.check_output(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            gpus = [line.strip() for line in gpu.split('\n') if line.strip() and line.strip() != 'Name']
            return gpus[0] if gpus else "Unknown GPU", None
        elif platform.system() == "Linux":
            try:
                gpu = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    encoding='utf-8'
                ).strip()
                return gpu, None
            except:
                lspci = subprocess.check_output(["lspci"], encoding='utf-8')
                for line in lspci.split('\n'):
                    if 'VGA' in line or '3D' in line:
                        return line.split(':')[-1].strip(), None
        elif platform.system() == "Darwin":
            gpu_info = subprocess.check_output(["system_profiler", "SPDisplaysDataType"], 
                                              encoding='utf-8')
            for line in gpu_info.split('\n'):
                if 'Chipset Model:' in line:
                    return line.split(':')[1].strip(), None
    except:
        pass
    return "Unknown GPU", None

def get_system_specs():
    """Get system specifications for gaming."""
    # Monitor Resolution
    root = tk.Tk()
    root.withdraw()
    resolution = f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}"
    root.destroy()
    
    # CPU
    cpu_name = get_cpu_name()
    cpu_cores = psutil.cpu_count(logical=False)
    cpu_threads = psutil.cpu_count(logical=True)
    
    # GPU
    gpu_name, gpu_memory = get_gpu_name()
    
    # RAM
    ram = psutil.virtual_memory()
    ram_gb = round(ram.total / (1024**3), 2)
    
    # Storage
    disk = psutil.disk_usage('/')
    storage_free = round(disk.free / (1024**3), 2)
    
    return {
        'os': f"{platform.system()} {platform.release()}",
        'resolution': resolution,
        'cpu': cpu_name,
        'cpu_cores': cpu_cores,
        'cpu_threads': cpu_threads,
        'gpu': gpu_name,
        'gpu_memory': gpu_memory,
        'ram_gb': ram_gb,
        'storage_free_gb': storage_free
    }

def search_game(game_name):
    """Search for a game on Steam."""
    url = f"https://steamcommunity.com/actions/SearchApps/{game_name}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        results = response.json()
        return [{"app_id": game['appid'], "name": game['name']} for game in results] if results else []
    except:
        return []

def get_game_requirements(app_id):
    """Get game requirements from Steam API."""
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data[str(app_id)]['success']:
            return {"error": "Game data unavailable"}
        
        game_data = data[str(app_id)]['data']
        pc_req = game_data.get('pc_requirements', {})
        
        return {
            "name": game_data.get('name', 'Unknown'),
            "minimum": pc_req.get('minimum', 'Not specified'),
            "recommended": pc_req.get('recommended', 'Not specified')
        }
    except:
        return {"error": "Failed to fetch game data"}

def clean_html(html_text):
    """Remove HTML tags from text."""
    if not html_text or html_text == 'Not specified':
        return html_text
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text(separator='\n', strip=True)

def analyze_with_ai(game_name, requirements, specs):
    """Use AI to analyze compatibility."""
    req_text = f"REQUIREMENTS FOR {requirements['name']}:\n"
    if requirements['minimum'] != 'Not specified':
        req_text += f"\nMinimum:\n{clean_html(requirements['minimum'])}\n"
    if requirements['recommended'] != 'Not specified':
        req_text += f"\nRecommended:\n{clean_html(requirements['recommended'])}\n"
    
    specs_text = f"""YOUR PC:
OS: {specs['os']}
Resolution: {specs['resolution']}
CPU: {specs['cpu']} ({specs['cpu_cores']} cores / {specs['cpu_threads']} threads)
GPU: {specs['gpu']}{f" ({specs['gpu_memory']})" if specs['gpu_memory'] else ""}
RAM: {specs['ram_gb']} GB
Free Storage: {specs['storage_free_gb']} GB"""
    
    prompt = f"""{specs_text}

{req_text}

Can my PC run {game_name}? Analyze:
1. Minimum requirements compatibility
2. Recommended requirements compatibility
3. Expected performance at {specs['resolution']}
4. Recommended graphics settings
5. Estimated FPS range
6. Upgrade suggestions if needed"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

def check_compatibility(game_name, output_box):
    """Main compatibility check."""
    try:
        output_box.insert(tk.END, "Detecting system specs...\n")
        output_box.see(tk.END)
        specs = get_system_specs()
        
        output_box.insert(tk.END, f"Searching Steam for '{game_name}'...\n")
        output_box.see(tk.END)
        results = search_game(game_name)
        
        if not results:
            output_box.insert(tk.END, "\n❌ No games found!\n\n")
            return
        
        game = results[0]
        output_box.insert(tk.END, f"Found: {game['name']}\n")
        output_box.see(tk.END)
        
        output_box.insert(tk.END, "Fetching requirements...\n")
        output_box.see(tk.END)
        requirements = get_game_requirements(game['app_id'])
        
        if "error" in requirements:
            output_box.insert(tk.END, f"\n❌ {requirements['error']}\n\n")
            return
        
        output_box.insert(tk.END, "\nAnalyzing with AI...\n")
        output_box.insert(tk.END, "=" * 60 + "\n")
        output_box.see(tk.END)
        
        analysis = analyze_with_ai(game['name'], requirements, specs)
        
        output_box.insert(tk.END, f"\n{analysis}\n\n")
        output_box.see(tk.END)
        
    except Exception as e:
        output_box.insert(tk.END, f"\n❌ Error: {str(e)}\n\n")

def run_check(event, game_entry, output_box):
    """Handle check button/enter press."""
    game = game_entry.get().strip()
    if not game:
        output_box.insert(tk.END, "Please enter a game name.\n\n")
        return
    
    output_box.delete(1.0, tk.END)
    output_box.insert(tk.END, f"Checking: {game}\n{'=' * 60}\n\n")
    
    thread = threading.Thread(target=check_compatibility, args=(game, output_box))
    thread.daemon = True
    thread.start()

def show_specs(output_box):
    """Display system specs."""
    output_box.delete(1.0, tk.END)
    output_box.insert(tk.END, "Detecting system specs...\n\n")
    
    specs = get_system_specs()
    
    output_box.insert(tk.END, "SYSTEM SPECIFICATIONS\n")
    output_box.insert(tk.END, "=" * 60 + "\n")
    output_box.insert(tk.END, f"OS: {specs['os']}\n")
    output_box.insert(tk.END, f"Resolution: {specs['resolution']}\n")
    output_box.insert(tk.END, f"CPU: {specs['cpu']}\n")
    output_box.insert(tk.END, f"Cores/Threads: {specs['cpu_cores']}/{specs['cpu_threads']}\n")
    output_box.insert(tk.END, f"GPU: {specs['gpu']}\n")
    if specs['gpu_memory']:
        output_box.insert(tk.END, f"GPU Memory: {specs['gpu_memory']}\n")
    output_box.insert(tk.END, f"RAM: {specs['ram_gb']} GB\n")
    output_box.insert(tk.END, f"Free Storage: {specs['storage_free_gb']} GB\n")
    output_box.insert(tk.END, "=" * 60 + "\n\n")

def main():
    window = tk.Tk()
    window.title("Game Compatibility Checker")
    window.geometry("900x600")
    window.configure(bg="#1a1a1a")

    tk.Label(window, text="Game Compatibility Checker", 
             font=("Arial", 18, "bold"), fg="white", bg="#1a1a1a").pack(pady=15)

    input_frame = tk.Frame(window, bg="#1a1a1a")
    input_frame.pack(pady=10)

    tk.Label(input_frame, text="Game Name:", fg="white", bg="#1a1a1a").grid(row=0, column=0, padx=5)
    
    game_entry = tk.Entry(input_frame, width=40, font=("Arial", 11))
    game_entry.grid(row=0, column=1, padx=5)
    game_entry.focus_set()

    tk.Label(window, text="Press Enter to check", fg="#888", bg="#1a1a1a").pack(pady=5)

    tk.Button(window, text="Show System Specs", 
             command=lambda: show_specs(output_box),
             bg="#333", fg="white", font=("Arial", 10)).pack(pady=5)

    output_box = scrolledtext.ScrolledText(
        window, width=100, height=20,
        bg="#0d0d0d", fg="#00ff00",
        insertbackground="white",
        font=("Consolas", 9)
    )
    output_box.pack(pady=10, padx=10)

    window.bind("<Return>", lambda e: run_check(e, game_entry, output_box))
    window.mainloop()

if __name__ == "__main__":
    main()
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

def get_system_specs():
    """Get relevant system specifications for gaming."""
    specs = {}
    
    # Operating System
    specs['os'] = f"{platform.system()} {platform.release()}"
    
    # Monitor Resolution
    specs['resolution'] = get_monitor_resolution()
    
    # CPU Information
    specs['cpu'] = platform.processor()
    try:
        if platform.system() == "Windows":
            cpu_name = subprocess.check_output(
                ["wmic", "cpu", "get", "name"],
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW
            ).strip()
            # Split by lines and get the actual CPU name (skip header)
            lines = [line.strip() for line in cpu_name.split('\n') if line.strip()]
            if len(lines) > 1:
                specs['cpu'] = lines[1]
            elif lines:
                # Sometimes the header and value are on same line
                specs['cpu'] = lines[0].replace('Name', '').strip()
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
    except:
        pass
    
    specs['cpu_cores'] = psutil.cpu_count(logical=False)
    specs['cpu_threads'] = psutil.cpu_count(logical=True)
    
    # GPU Information
    specs['gpu'] = "Unknown"
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            specs['gpu'] = gpus[0].name
            specs['gpu_memory'] = f"{gpus[0].memoryTotal}MB"
    except:
        pass
    
    # Fallback GPU detection
    if specs['gpu'] == "Unknown":
        try:
            if platform.system() == "Windows":
                gpu_info = subprocess.check_output(["wmic", "path", "win32_VideoController", 
                                                   "get", "name"], encoding='utf-8')
                gpus = [line.strip() for line in gpu_info.split('\n') 
                        if line.strip() and line.strip() != 'Name']
                if gpus:
                    specs['gpu'] = gpus[0]
            elif platform.system() == "Linux":
                try:
                    nvidia_info = subprocess.check_output(["nvidia-smi", "--query-gpu=name", 
                                                          "--format=csv,noheader"], 
                                                         encoding='utf-8')
                    specs['gpu'] = nvidia_info.strip()
                except:
                    lspci_info = subprocess.check_output(["lspci"], encoding='utf-8')
                    for line in lspci_info.split('\n'):
                        if 'VGA' in line or 'Display' in line:
                            specs['gpu'] = line.split(':')[-1].strip()
                            break
            elif platform.system() == "Darwin":
                gpu_info = subprocess.check_output(["system_profiler", "SPDisplaysDataType"], 
                                                  encoding='utf-8')
                for line in gpu_info.split('\n'):
                    if 'Chipset Model:' in line:
                        specs['gpu'] = line.split(':')[1].strip()
                        break
        except:
            pass
    
    # RAM Information
    svmem = psutil.virtual_memory()
    specs['ram_total_gb'] = round(svmem.total / (1024**3), 2)
    specs['ram_available_gb'] = round(svmem.available / (1024**3), 2)
    
    # Storage
    try:
        disk = psutil.disk_usage('/')
        specs['storage_free_gb'] = round(disk.free / (1024**3), 2)
    except:
        specs['storage_free_gb'] = "Unknown"
    
    return specs


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
    if 'gpu_memory' in specs:
        formatted += f"GPU Memory: {specs['gpu_memory']}\n"
    formatted += f"RAM: {specs.get('ram_total_gb', '?')} GB (Available: {specs.get('ram_available_gb', '?')} GB)\n"
    formatted += f"Free Storage: {specs.get('storage_free_gb', '?')} GB\n"
    return formatted


def compare_specs_with_ai(game_name, requirements_text, system_specs_text, system_specs):
    """Send both game requirements and system specs to Google AI for comparison."""
    prompt = f"""{system_specs_text}

{requirements_text}

Question: Can my PC run {game_name}? Please compare my system specs against the game's requirements and tell me:
1. Whether I meet the minimum requirements
2. Whether I meet the recommended requirements
3. What performance I can expect at my monitor resolution ({system_specs.get('resolution', 'unknown')})
4. What graphics settings I should use (low/medium/high/ultra)
5. Estimated FPS range I can expect
6. Any components I should upgrade if needed"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error querying Google AI: {str(e)}"


# GUI Code
def run_check(event=None):
    game = game_entry.get()
    if game.strip() == "":
        output_box.insert(tk.END, "Please enter a game name.\n\n")
        return
    
    # Clear output box
    output_box.delete(1.0, tk.END)
    output_box.insert(tk.END, f"Checking compatibility for: {game}\n")
    output_box.insert(tk.END, "=" * 60 + "\n\n")
    
    # Run in separate thread to avoid freezing GUI
    thread = threading.Thread(target=check_compatibility, args=(game,))
    thread.daemon = True
    thread.start()


def check_compatibility(game_name):
    """Main compatibility check function that runs in a separate thread."""
    try:
        # Get system specs
        output_box.insert(tk.END, "Detecting system specifications...\n")
        output_box.see(tk.END)
        system_specs = get_system_specs()
        
        # Search for game
        output_box.insert(tk.END, f"Searching for '{game_name}' on Steam...\n")
        output_box.see(tk.END)
        search_results = search_game_by_name(game_name)
        
        if not search_results:
            output_box.insert(tk.END, "\nNo games found! Please check the spelling.\n\n")
            return
        
        output_box.insert(tk.END, f"Found {len(search_results)} result(s). Using: {search_results[0]['name']}\n")
        output_box.see(tk.END)
        
        # Get requirements
        output_box.insert(tk.END, "Fetching game requirements...\n")
        output_box.see(tk.END)
        requirements = get_game_requirements(search_results[0]['app_id'])
        
        if "error" in requirements:
            output_box.insert(tk.END, f"\nError: {requirements['error']}\n\n")
            return
        
        # Format data
        req_text = format_requirements_for_ai(requirements)
        specs_text = format_system_specs(system_specs)
        
        # Display requirements
        output_box.insert(tk.END, "\n" + req_text + "\n")
        output_box.see(tk.END)
        
        # Ask AI
        output_box.insert(tk.END, "Analyzing compatibility with AI...\n")
        output_box.insert(tk.END, "=" * 60 + "\n")
        output_box.see(tk.END)
        
        ai_response = compare_specs_with_ai(
            search_results[0]['name'],
            req_text,
            specs_text,
            system_specs
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
    if 'gpu_memory' in specs:
        output_box.insert(tk.END, f"GPU Memory: {specs['gpu_memory']}\n")
    output_box.insert(tk.END, f"RAM: {specs.get('ram_total_gb', '?')} GB\n")
    output_box.insert(tk.END, f"Available RAM: {specs.get('ram_available_gb', '?')} GB\n")
    output_box.insert(tk.END, f"Free Storage: {specs.get('storage_free_gb', '?')} GB\n")
    output_box.insert(tk.END, "=" * 60 + "\n\n")


def main():
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

    global game_entry
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

    global output_box
    output_box = scrolledtext.ScrolledText(window, width=100, height=20,
                                           bg="black", fg="white",
                                           insertbackground="white",
                                           font=("Consolas", 9))
    output_box.pack(pady=10)

    window.mainloop()


game_entry = None
output_box = None

if __name__ == "__main__":
    main()