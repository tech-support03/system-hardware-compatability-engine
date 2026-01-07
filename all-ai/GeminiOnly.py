import eel
import psutil
import platform
import subprocess
import google.generativeai as genai
import os
import sys
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# ============================================
# ENVIRONMENT VARIABLE API KEY MANAGEMENT
# ============================================

def get_api_key():
    """Get API key from environment variable or .env file."""
    # First, try to load from environment variable directly
    api_key = os.getenv('GOOGLE_AI_API_KEY')
    if api_key:
        return api_key
    
    # Determine where to look for .env file
    if getattr(sys, 'frozen', False):
        # Running as compiled executable - look next to the .exe
        application_path = os.path.dirname(sys.executable)
    else:
        # Running as script - look in script directory
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    # Try to load .env from the executable's directory
    env_path = os.path.join(application_path, '.env')
    print(f"Looking for .env at: {env_path}")
    
    if os.path.exists(env_path):
        print(f".env file found!")
        load_dotenv(env_path)
        api_key = os.getenv('GOOGLE_AI_API_KEY')
        if api_key:
            return api_key
    else:
        print(f".env file NOT found at {env_path}")
    
    # Still no API key - show instructions
    print("\n" + "="*60)
    print("ERROR: GOOGLE_AI_API_KEY not found!")
    print("="*60)
    print(f"\nPlease create a .env file at:")
    print(f"{application_path}")
    print("\nWith the content:")
    print("GOOGLE_AI_API_KEY=your_api_key_here")
    print("\nOr set the GOOGLE_AI_API_KEY environment variable.")
    print("="*60 + "\n")
    return None

def setup_api_key():
    """Initialize and configure the API key."""
    api_key = get_api_key()
    
    if not api_key:
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        return model
    except Exception as e:
        print(f"Error initializing Google AI: {e}")
        return None

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

def format_system_specs(specs):
    """Format system specs into readable text."""
    formatted = "USER'S PC SPECIFICATIONS:\n"
    formatted += "=" * 50 + "\n"
    formatted += f"OS: {specs.get('os', 'Unknown')}\n"
    formatted += f"Monitor Resolution: {specs.get('resolution', 'Unknown')}\n"
    formatted += f"CPU: {specs.get('cpu', 'Unknown')}\n"
    formatted += f"CPU Cores/Threads: {specs.get('cpu_cores', '?')}/{specs.get('cpu_threads', '?')}\n"
    formatted += f"GPU: {specs.get('gpu', 'Unknown')}\n"
    formatted += f"RAM: {specs.get('ram_total_gb', '?')} GB\n"
    formatted += f"Free Storage: {specs.get('storage_free_gb', '?')} GB\n"
    return formatted

def analyze_game_compatibility(game_name, system_specs, model):
    """Use Gemini to analyze game compatibility."""
    specs_text = format_system_specs(system_specs)
    
    prompt = f"""You are a PC gaming expert. A user wants to know if their PC can run "{game_name}".

{specs_text}

Please do the following:
1. Research and provide the ACTUAL system requirements for "{game_name}" (both minimum and recommended)
2. Compare their PC specs against these requirements
3. Provide a detailed compatibility analysis including:
   - Whether they can run the game (Yes/No/Maybe)
   - Expected performance at their resolution ({system_specs.get('resolution', 'unknown')})
   - Recommended graphics settings (Low/Medium/High/Ultra)
   - Estimated FPS range
   - Any bottlenecks or concerns
   - Specific recommendations for their hardware

Be specific and technical. Use actual game requirements if you know them. If the game doesn't exist or you're unsure, say so clearly."""
    
    try:
        response = model.generate_content(prompt)
        return {
            "success": True,
            "analysis": response.text
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI Analysis Error: {str(e)}"
        }

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
        system_specs = get_system_specs()
        
        # Use Gemini to analyze everything
        result = analyze_game_compatibility(game_name, system_specs, ai_model)
        
        if result["success"]:
            return {
                "success": True,
                "game_name": game_name,
                "system_specs": system_specs,
                "ai_analysis": result["analysis"]
            }
        else:
            return {
                "success": False,
                "error": result["error"]
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
    global ai_model
    
    # Setup API key
    ai_model = setup_api_key()
    
    if not ai_model:
        print("\nERROR: Cannot start without a valid API key!")
        print("Please set the GOOGLE_AI_API_KEY environment variable.\n")
        
        # Offer to create .env file
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            env_path = os.path.join(exe_dir, '.env')
            
            print(f"Would you like to create a .env file at:")
            print(f"{env_path}")
            print("\nPress Enter to create it, or close this window to exit...")
            input()
            
            api_key = input("Please enter your Google AI API key: ").strip()
            if api_key:
                try:
                    with open(env_path, 'w') as f:
                        f.write(f"GOOGLE_AI_API_KEY={api_key}\n")
                    print("\n.env file created successfully!")
                    print("Please restart the application.")
                except Exception as e:
                    print(f"\nError creating .env file: {e}")
        
        input("\nPress Enter to exit...")
        return
    
    print("\n" + "="*60)
    print("Game Compatibility Checker - Starting...")
    print("="*60)
    print("\nAPI key loaded successfully!")
    print("Opening web interface...\n")
    
    # Get the correct path for the web folder
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = sys._MEIPASS
    else:
        # Running as script
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    web_folder = os.path.join(application_path, 'web')
    
    print(f"Looking for web folder at: {web_folder}")
    print(f"Web folder exists: {os.path.exists(web_folder)}")
    
    if os.path.exists(web_folder):
        print(f"Files in web folder: {os.listdir(web_folder)}")
    
    # Initialize Eel with the web folder
    eel.init(web_folder)
    
    try:
        # Start the application
        eel.start('index.html', size=(1400, 900), port=8080)
    except Exception as e:
        print(f"\nError starting application: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()