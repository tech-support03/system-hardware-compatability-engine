import psutil
import platform
import subprocess

def get_size(bytes):
    """Convert bytes to human readable format"""
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if bytes < 1024:
            return f"{bytes:.2f}{unit}B"
        bytes /= 1024

# System Information
print("=" * 40, "System Info", "=" * 40)
print(f"System: {platform.system()}")
print(f"Node Name: {platform.node()}")
print(f"Release: {platform.release()}")
print(f"Version: {platform.version()}")
print(f"Machine: {platform.machine()}")

# CPU Name and Information
print("\n" + "=" * 40, "CPU Info", "=" * 40)
print(f"Processor: {platform.processor()}")

# Get detailed CPU name
try:
    if platform.system() == "Windows":
        cpu_name = subprocess.check_output(["wmic", "cpu", "get", "name"], 
                                          encoding='utf-8').strip().split('\n')[1]
        print(f"CPU Name: {cpu_name}")
    elif platform.system() == "Linux":
        cpu_name = subprocess.check_output(["cat", "/proc/cpuinfo"], 
                                          encoding='utf-8')
        for line in cpu_name.split('\n'):
            if "model name" in line:
                print(f"CPU Name: {line.split(':')[1].strip()}")
                break
    elif platform.system() == "Darwin":  # macOS
        cpu_name = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], 
                                          encoding='utf-8').strip()
        print(f"CPU Name: {cpu_name}")
except:
    print("Could not retrieve detailed CPU name")

print(f"Physical cores: {psutil.cpu_count(logical=False)}")
print(f"Total cores: {psutil.cpu_count(logical=True)}")

cpufreq = psutil.cpu_freq()
if cpufreq:
    print(f"Max Frequency: {cpufreq.max:.2f}Mhz")
    print(f"Current Frequency: {cpufreq.current:.2f}Mhz")

print(f"CPU Usage: {psutil.cpu_percent(interval=1)}%")

# GPU Information
print("\n" + "=" * 40, "GPU Info", "=" * 40)

# Try GPUtil first (best for NVIDIA)
try:
    import GPUtil
    gpus = GPUtil.getGPUs()
    if gpus:
        for i, gpu in enumerate(gpus):
            print(f"GPU {i}: {gpu.name}")
            print(f"  Memory Total: {gpu.memoryTotal}MB")
            print(f"  Memory Free: {gpu.memoryFree}MB")
            print(f"  Memory Used: {gpu.memoryUsed}MB")
            print(f"  GPU Load: {gpu.load * 100:.1f}%")
            print(f"  Temperature: {gpu.temperature}°C")
    else:
        print("No NVIDIA GPU detected via GPUtil")
except ImportError:
    print("GPUtil not installed (pip install gputil)")
except Exception as e:
    print(f"GPUtil error: {e}")

# Platform-specific GPU detection
try:
    if platform.system() == "Windows":
        gpu_info = subprocess.check_output(["wmic", "path", "win32_VideoController", 
                                           "get", "name"], encoding='utf-8')
        gpus = [line.strip() for line in gpu_info.split('\n') 
                if line.strip() and line.strip() != 'Name']
        for gpu in gpus:
            print(f"Detected GPU: {gpu}")
    elif platform.system() == "Linux":
        # Try nvidia-smi
        try:
            nvidia_info = subprocess.check_output(["nvidia-smi", "--query-gpu=name", 
                                                  "--format=csv,noheader"], 
                                                 encoding='utf-8')
            print(f"NVIDIA GPU: {nvidia_info.strip()}")
        except:
            pass
        
        # Try lspci for all GPUs
        try:
            lspci_info = subprocess.check_output(["lspci"], encoding='utf-8')
            for line in lspci_info.split('\n'):
                if 'VGA' in line or 'Display' in line or '3D' in line:
                    print(f"Detected GPU: {line.split(':')[-1].strip()}")
        except:
            pass
    elif platform.system() == "Darwin":  # macOS
        gpu_info = subprocess.check_output(["system_profiler", "SPDisplaysDataType"], 
                                          encoding='utf-8')
        for line in gpu_info.split('\n'):
            if 'Chipset Model:' in line:
                print(f"Detected GPU: {line.split(':')[1].strip()}")
except Exception as e:
    print(f"Error detecting GPU: {e}")

# Memory Information
print("\n" + "=" * 40, "Memory Info", "=" * 40)
svmem = psutil.virtual_memory()
print(f"Total: {get_size(svmem.total)}")
print(f"Available: {get_size(svmem.available)}")
print(f"Used: {get_size(svmem.used)}")
print(f"Percentage: {svmem.percent}%")

# Disk Information
print("\n" + "=" * 40, "Disk Info", "=" * 40)
partitions = psutil.disk_partitions()
for partition in partitions:
    print(f"Device: {partition.device}")
    print(f"  Mountpoint: {partition.mountpoint}")
    print(f"  File system type: {partition.fstype}")
    try:
        partition_usage = psutil.disk_usage(partition.mountpoint)
        print(f"  Total Size: {get_size(partition_usage.total)}")
        print(f"  Used: {get_size(partition_usage.used)}")
        print(f"  Free: {get_size(partition_usage.free)}")
        print(f"  Percentage: {partition_usage.percent}%")
    except PermissionError:
        continue
    print()

# Network Information
print("=" * 40, "Network Info", "=" * 40)
if_addrs = psutil.net_if_addrs()
for interface_name, interface_addresses in if_addrs.items():
    print(f"Interface: {interface_name}")
    for address in interface_addresses:
        if address.address:
            print(f"  Address: {address.address}")
        if address.netmask:
            print(f"  Netmask: {address.netmask}")
        if address.broadcast:
            print(f"  Broadcast: {address.broadcast}")
    print()
