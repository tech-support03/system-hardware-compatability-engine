import eel
import requests
from bs4 import BeautifulSoup
import json
import psutil
import platform
import subprocess
from transformers import pipeline

# ============================================
# AI MODEL INITIALIZATION
# ============================================

print("Loading AI model... This may take a minute on first run.")
print("The model will be cached for future use.")

try:
    # Initialize the model - downloads automatically on first run
    ai_model = pipeline(
        'text-generation',
        model='microsoft/Phi-3-mini-4k-instruct',
        device=0  # Use CPU (-1), change to 0 for GPU
    )
    print("AI model loaded successfully!")
except Exception as e:
    print(f"Error loading AI model: {e}")
    ai_model = None

# ============================================
# SYSTEM INFORMATION FUNCTIONS
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
        # Use psutil for cross-platform compatibility
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return f"{width}x{height}"
    except:
        return "1920x1080"

def get_gpu_info_fixed():
    """Get GPU information using PowerShell, prioritizing dedicated GPUs."""
    gpu_name = "Unknown"
    
    virtual_keywords = ['parsec', 'virtual', 'remote', 'microsoft basic', 'vnc', 
                       'teamviewer', 'splashtop', 'citrix', 'vmware', 'hyper-v',
                       'generic pnp', 'rdp', 'standard vga']
    
    integrated_keywords = ['intel(r) uhd', 'intel(r) hd', 'intel hd', 'intel uhd',
                          'amd radeon(tm) graphics', 'radeon graphics', 'vega graphics',
                          'radeon vega', 'intel iris xe']
    
    try:
        if platform.system() == "Windows":
            ps_command = """
            Get-CimInstance Win32_VideoController | Where-Object {
                $_.Name -notmatch 'Parsec|Virtual|Remote|Microsoft Basic|Generic PnP|RDP|Standard VGA'
            } | Select-Object Name | ConvertTo-Json
            """
            
            gpu_info = run_powershell_command(ps_command)
            
            if gpu_info:
                try:
                    gpu_data = json.loads(gpu_info)
                    
                    if isinstance(gpu_data, dict):
                        gpu_data = [gpu_data]
                    
                    dedicated_gpus = []
                    integrated_gpus = []
                    
                    for gpu in gpu_data:
                        name = gpu.get('Name', '').strip()
                        name_lower = name.lower()
                        
                        if (name and 
                            ('amd' in name_lower or 'radeon' in name_lower or
                             'nvidia' in name_lower or 'geforce' in name_lower or
                             'intel' in name_lower and 'arc' in name_lower or
                             'intel' in name_lower and 'uhd' in name_lower or
                             'intel' in name_lower and 'iris' in name_lower or
                             'intel' in name_lower and 'hd graphics' in name_lower or
                             'gtx' in name_lower or 'rtx' in name_lower or
                             'rx' in name_lower)):
                            
                            is_integrated = any(keyword in name_lower for keyword in integrated_keywords)
                            
                            if is_integrated:
                                integrated_gpus.append(name)
                            else:
                                dedicated_gpus.append(name)
                    
                    if dedicated_gpus:
                        gpu_name = dedicated_gpus[0]
                    elif integrated_gpus:
                        gpu_name = integrated_gpus[0]
                    
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
    """Get CPU information using PowerShell."""
    try:
        ps_command = "Get-CimInstance Win32_Processor | Select-Object Name | ConvertTo-Json"
        cpu_info = run_powershell_command(ps_command)
        
        if cpu_info:
            cpu_data = json.loads(cpu_info)
            
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
    """Send both game requirements and system specs to local AI for comparison."""
    prompt = f"""{system_specs_text}

{requirements_text}

Question: Can my PC run {game_name}? Please analyze and provide:
1. Performance at {system_specs.get('resolution', 'unknown')} resolution
2. Recommended graphics settings (low/medium/high/ultra)
3. Expected FPS range

Answer:"""
    
    try:
        response = model(
            prompt,
            max_length=500,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True,
            pad_token_id=model.tokenizer.eos_token_id
        )
        
        # Extract the generated text after the prompt
        generated_text = response[0]['generated_text']
        
        # Remove the prompt from the response to get only the answer
        answer = generated_text[len(prompt):].strip()
        
        return answer
        
    except Exception as e:
        return f"Error analyzing with AI: {str(e)}"

# ============================================
# EEL EXPOSED FUNCTIONS
# ============================================

@eel.expose
def get_system_info():
    """Exposed function to get system specs from frontend."""
    return get_system_specs()

@eel.expose
def check_game_compatibility(game_name):
    """Main compatibility check function exposed to frontend."""
    try:
        if ai_model is None:
            return {
                "success": False,
                "error": "AI model not loaded. Please restart the application."
            }
        
        system_specs = get_system_specs()
        
        search_results = search_game_by_name(game_name)
        
        if not search_results:
            return {
                "success": False,
                "error": "No games found! Please check the spelling."
            }
        
        requirements = get_game_requirements(search_results[0]['app_id'])
        
        if "error" in requirements:
            return {
                "success": False,
                "error": requirements['error']
            }
        
        req_text = format_requirements_for_ai(requirements)
        specs_text = format_system_specs(system_specs)
        
        print(f"Analyzing {search_results[0]['name']}...")
        
        ai_response = compare_specs_with_ai(
            search_results[0]['name'],
            req_text,
            specs_text,
            system_specs,
            ai_model
        )
        
        return {
            "success": True,
            "game_name": search_results[0]['name'],
            "requirements": requirements,
            "system_specs": system_specs,
            "ai_analysis": ai_response,
            "requirements_text": req_text
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ============================================
# MAIN FUNCTION
# ============================================

def main():
    if ai_model is None:
        print("\nERROR: AI model failed to load!")
        print("Please ensure you have internet connection for first-time model download.")
        print("Required packages: transformers, torch")
        print("\nInstall with: pip install transformers torch\n")
        return
    
    print("\n" + "="*60)
    print("Game Compatibility Checker - Starting...")
    print("="*60)
    print("\nAI model ready!")
    print("Opening web interface...\n")
    
    # Initialize Eel with the web folder
    eel.init('web')
    
    # Start the application
    eel.start('index.html', size=(1400, 900), port=8080)

if __name__ == "__main__":
    main()