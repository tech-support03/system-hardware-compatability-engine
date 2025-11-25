import requests
from bs4 import BeautifulSoup
import json
from openai import OpenAI
import psutil
import platform
import subprocess
import tkinter as tk

# Initialize LM Studio client
client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

def get_monitor_resolution():
    """
    Get the monitor resolution.
    
    Returns:
        str: Resolution in WIDTHxHEIGHT format (e.g., "1920x1080")
    """
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
    """
    Get relevant system specifications for gaming.
    
    Returns:
        dict: System specs including CPU, GPU, RAM, OS, and resolution
    """
    specs = {}
    
    # Operating System
    specs['os'] = f"{platform.system()} {platform.release()}"
    
    # Monitor Resolution
    specs['resolution'] = get_monitor_resolution()
    
    # CPU Information
    specs['cpu'] = platform.processor()
    try:
        if platform.system() == "Windows":
            cpu_name = subprocess.check_output(["wmic", "cpu", "get", "name"], 
                                              encoding='utf-8').strip().split('\n')[1]
            specs['cpu'] = cpu_name.strip()
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
        
    except requests.RequestException as e:
        print(f"Search failed: {str(e)}")
        return []
    except json.JSONDecodeError:
        print("Failed to parse search results")
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
        
    except requests.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except (KeyError, json.JSONDecodeError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}


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


def compare_specs_with_ai(game_name, requirements_text, system_specs_text, system_specs):
    """
    Send both game requirements and system specs to the AI for comparison.
    
    Args:
        game_name: Name of the game
        requirements_text: Formatted game requirements
        system_specs_text: Formatted system specifications
        system_specs: Dictionary of system specs (for resolution)
    
    Returns:
        str: AI's analysis
    """
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
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are a helpful PC gaming expert who compares system specifications against game requirements. Be honest and specific about performance expectations."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error querying AI: {str(e)}"


# Main execution
if __name__ == "__main__":
    print("=" * 60)
    print("STEAM GAME COMPATIBILITY CHECKER")
    print("=" * 60)
    
    # Get system specs
    print("\nDetecting your system specifications...")
    system_specs = get_system_specs()
    specs_text = format_system_specs(system_specs)
    print("\n" + specs_text)
    
    # Search for a game
    game_name = input("\nEnter game name to check: ").strip()
    
    if not game_name:
        game_name = "Cyberpunk 2077"
        print(f"Using default: {game_name}")
    
    print(f"\nSearching for '{game_name}'...")
    search_results = search_game_by_name(game_name)
    
    if not search_results:
        print("No games found!")
    else:
        print(f"\nFound {len(search_results)} results:")
        for i, game in enumerate(search_results[:5], 1):
            print(f"{i}. {game['name']} (App ID: {game['app_id']})")
        
        # Use the first result
        selected_game = search_results[0]
        print(f"\n{'='*60}")
        print(f"Analyzing: {selected_game['name']}")
        print('='*60)
        
        # Fetch requirements
        requirements = get_game_requirements(selected_game['app_id'])
        
        if "error" in requirements:
            print(f"Error: {requirements['error']}")
        else:
            # Format requirements
            req_text = format_requirements_for_ai(requirements)
            print("\n" + req_text)
            
            # Ask AI to compare
            print("\n" + "="*60)
            print("AI COMPATIBILITY ANALYSIS:")
            print("="*60 + "\n")
            
            ai_response = compare_specs_with_ai(
                selected_game['name'], 
                req_text,
                specs_text,
                system_specs
            )
            
            print(ai_response)
