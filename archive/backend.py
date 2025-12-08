import requests
import platform
import psutil
import screeninfo
import json
import subprocess
import re


def get_cpu_info():
    """Get CPU information across different platforms."""
    system = platform.system()
    cpu_name = "Unknown CPU"
    
    if system == "Windows":
        try:
            # Use WMIC to get CPU name on Windows
            result = subprocess.check_output(
                ['wmic', 'cpu', 'get', 'name'],
                encoding='utf-8',
                errors='ignore'
            )
            lines = [line.strip() for line in result.split('\n') if line.strip()]
            if len(lines) > 1:
                cpu_name = lines[1].strip()
        except:
            # Fallback to platform.processor()
            cpu_name = platform.processor()
    
    elif system == "Linux":
        try:
            # Read from /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        cpu_name = line.split(':', 1)[1].strip()
                        break
        except:
            cpu_name = platform.processor()
    
    elif system == "Darwin":  # macOS
        try:
            result = subprocess.check_output(
                ['sysctl', '-n', 'machdep.cpu.brand_string'],
                encoding='utf-8'
            )
            cpu_name = result.strip()
        except:
            cpu_name = platform.processor()
    
    return cpu_name


def get_gpu_info():
    """Get GPU information for AMD, NVIDIA, and Intel GPUs."""
    system = platform.system()
    
    if system == "Windows":
        try:
            # Use WMIC to get GPU info on Windows
            result = subprocess.check_output(
                ['wmic', 'path', 'win32_VideoController', 'get', 'name,AdapterRAM'],
                encoding='utf-8',
                errors='ignore'
            )
            
            lines = [line.strip() for line in result.split('\n') if line.strip()]
            
            # Filter out virtual/remote display adapters
            virtual_keywords = ['parsec', 'virtual', 'remote', 'microsoft basic', 'vnc', 'teamviewer']
            real_gpus = []
            
            for line in lines[1:]:  # Skip header
                line_lower = line.lower()
                # Skip if it contains virtual adapter keywords
                if any(keyword in line_lower for keyword in virtual_keywords):
                    continue
                
                parts = line.rsplit(None, 1)  # Split from right to get RAM
                
                if len(parts) == 2:
                    gpu_name = parts[0].strip()
                    try:
                        vram_bytes = int(parts[1])
                        vram_gb = round(vram_bytes / (1024**3), 2)
                    except:
                        vram_gb = 'Unknown'
                else:
                    gpu_name = line.strip()
                    vram_gb = 'Unknown'
                
                # Only add if it looks like a real GPU (AMD, NVIDIA, Intel, or has significant VRAM)
                if gpu_name and (
                    'amd' in gpu_name.lower() or 
                    'radeon' in gpu_name.lower() or
                    'nvidia' in gpu_name.lower() or 
                    'geforce' in gpu_name.lower() or
                    'intel' in gpu_name.lower() or
                    'arc' in gpu_name.lower() or
                    (isinstance(vram_gb, (int, float)) and vram_gb > 0.5)
                ):
                    real_gpus.append({'name': gpu_name, 'vram_gb': vram_gb})
            
            # Return the first real GPU found
            if real_gpus:
                return real_gpus[0]
        except:
            pass
    
    elif system == "Linux":
        try:
            # Try lspci for Linux
            result = subprocess.check_output(['lspci'], encoding='utf-8')
            for line in result.split('\n'):
                if 'VGA' in line or 'Display' in line or '3D' in line:
                    # Extract GPU name
                    match = re.search(r':\s*(.+?)(?:\(|$)', line)
                    if match:
                        gpu_name = match.group(1).strip()
                        return {'name': gpu_name, 'vram_gb': 'Unknown'}
        except:
            pass
    
    elif system == "Darwin":  # macOS
        try:
            result = subprocess.check_output(
                ['system_profiler', 'SPDisplaysDataType'],
                encoding='utf-8'
            )
            # Parse macOS system profiler output
            lines = result.split('\n')
            for i, line in enumerate(lines):
                if 'Chipset Model:' in line:
                    gpu_name = line.split(':', 1)[1].strip()
                    # Look for VRAM in next few lines
                    vram_gb = 'Unknown'
                    for j in range(i, min(i+5, len(lines))):
                        if 'VRAM' in lines[j] or 'Memory' in lines[j]:
                            vram_match = re.search(r'(\d+)\s*(MB|GB)', lines[j])
                            if vram_match:
                                vram_value = int(vram_match.group(1))
                                unit = vram_match.group(2)
                                vram_gb = vram_value if unit == 'GB' else round(vram_value / 1024, 2)
                            break
                    return {'name': gpu_name, 'vram_gb': vram_gb}
        except:
            pass
    
    return {'name': 'Unable to detect GPU', 'vram_gb': 'Unknown'}


def get_system_specs():
    """Gather comprehensive system specifications."""
    specs = {}
    
    # CPU Information
    cpu_name = get_cpu_info()
    specs['cpu'] = {
        'model': cpu_name,
        'cores': psutil.cpu_count(logical=False),
        'threads': psutil.cpu_count(logical=True),
        'frequency_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else 'Unknown'
    }
    
    # RAM Information
    ram = psutil.virtual_memory()
    specs['ram'] = {
        'total_gb': round(ram.total / (1024**3), 2),
        'available_gb': round(ram.available / (1024**3), 2)
    }
    
    # GPU Information (works with AMD, NVIDIA, Intel)
    specs['gpu'] = get_gpu_info()
    
    # Monitor Resolution
    try:
        monitors = screeninfo.get_monitors()
        specs['monitors'] = []
        for m in monitors:
            specs['monitors'].append({
                'width': m.width,
                'height': m.height,
                'resolution': f"{m.width}x{m.height}"
            })
        specs['primary_resolution'] = f"{monitors[0].width}x{monitors[0].height}" if monitors else "Unknown"
    except:
        specs['primary_resolution'] = "1920x1080"  # Default fallback
        specs['monitors'] = [{'width': 1920, 'height': 1080, 'resolution': '1920x1080'}]
    
    # OS Information
    specs['os'] = {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version()
    }
    
    return specs


def get_steam_game_requirements(game_name):
    """
    Fetch game requirements from Steam API.
    Note: Steam's official API has limited data. This uses the store page scraping approach.
    """
    # First, search for the game to get its App ID
    search_url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&cc=US"
    
    try:
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('items'):
            return None
        
        app_id = data['items'][0]['id']
        game_title = data['items'][0]['name']
        
        # Get game details
        details_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        details_response = requests.get(details_url, timeout=10)
        details_data = details_response.json()
        
        if str(app_id) in details_data and details_data[str(app_id)]['success']:
            game_data = details_data[str(app_id)]['data']
            
            requirements = {
                'game_name': game_title,
                'app_id': app_id,
                'minimum': game_data.get('pc_requirements', {}).get('minimum', 'Not available'),
                'recommended': game_data.get('pc_requirements', {}).get('recommended', 'Not available')
            }
            
            return requirements
        
        return None
        
    except Exception as e:
        print(f"Error fetching Steam data: {e}")
        return None


def query_lmstudio(system_specs, game_requirements, model_endpoint="http://localhost:1234/v1/chat/completions"):
    """
    Query the local LM Studio model to analyze game compatibility.
    Default LM Studio endpoint is http://localhost:1234/v1/chat/completions
    """
    
    # Format system specs nicely
    specs_text = f"""
System Specifications:
- CPU: {system_specs['cpu']['model']} ({system_specs['cpu']['cores']} cores, {system_specs['cpu']['threads']} threads)
- RAM: {system_specs['ram']['total_gb']} GB
- GPU: {system_specs['gpu']['name']} ({system_specs['gpu']['vram_gb']} GB VRAM)
- Primary Monitor Resolution: {system_specs['primary_resolution']}
- OS: {system_specs['os']['system']} {system_specs['os']['release']}
"""
    
    # Format game requirements
    game_text = f"""
Game: {game_requirements['game_name']}

Minimum Requirements:
{game_requirements['minimum']}

Recommended Requirements:
{game_requirements['recommended']}
"""
    
    prompt = f"""You are a PC gaming expert. Analyze whether this game will run on the given system and provide detailed performance predictions.

{specs_text}

{game_text}

Based on the system specs and game requirements above, please provide:
1. Will the game run? (Yes/No)
2. Expected FPS at different settings (Low, Medium, High, Ultra) at {system_specs['primary_resolution']}
3. Recommended graphics settings for optimal performance
4. Any bottlenecks or concerns
5. Overall compatibility rating (1-10)

Be specific with FPS estimates and explain your reasoning."""

    try:
        response = requests.post(
            model_endpoint,
            json={
                "model": "local-model",  # LM Studio typically uses this
                "messages": [
                    {"role": "system", "content": "You are a knowledgeable PC gaming hardware expert who provides accurate performance estimates for games based on system specifications."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            },
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        return result['choices'][0]['message']['content']
        
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to LM Studio. Make sure it's running on http://localhost:1234"
    except Exception as e:
        return f"Error querying LM Studio: {e}"


def main():
    print("=" * 60)
    print("Game Compatibility Checker with AI Analysis")
    print("=" * 60)
    print()
    
    # Get game name from user
    game_name = input("Enter the game name to check: ").strip()
    
    if not game_name:
        print("No game name provided. Exiting.")
        return
    
    print("\n[1/3] Gathering system specifications...")
    system_specs = get_system_specs()
    
    print("\n📊 Your System:")
    print(f"  CPU: {system_specs['cpu']['model']}")
    print(f"  RAM: {system_specs['ram']['total_gb']} GB")
    print(f"  GPU: {system_specs['gpu']['name']}")
    print(f"  Resolution: {system_specs['primary_resolution']}")
    
    print(f"\n[2/3] Fetching game requirements from Steam for '{game_name}'...")
    game_requirements = get_steam_game_requirements(game_name)
    
    if not game_requirements:
        print("❌ Could not find the game on Steam. Please check the spelling and try again.")
        return
    
    print(f"\n✅ Found: {game_requirements['game_name']} (App ID: {game_requirements['app_id']})")
    
    print("\n[3/3] Querying AI model for compatibility analysis...")
    print("(This may take a moment...)\n")
    
    analysis = query_lmstudio(system_specs, game_requirements)
    
    print("=" * 60)
    print("AI ANALYSIS RESULTS")
    print("=" * 60)
    print()
    print(analysis)
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()