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
GOOGLE_API_KEY = "######"  # Replace with your actual API key
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the model
model = genai.GenerativeModel('gemini-2.5-flash')

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