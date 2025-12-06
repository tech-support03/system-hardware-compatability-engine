import tkinter as tk
from tkinter import scrolledtext
import requests
from bs4 import BeautifulSoup
import json
import psutil
import platform
import subprocess
import threading
import os

# Optional imports
try:
    import GPUtil
except Exception:
    GPUtil = None

try:
    import wmi
except Exception:
    wmi = None

# Optional Google AI integration. Configure via environment variable `GOOGLE_API_KEY`.
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
try:
    if GOOGLE_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        AI_MODEL = genai.GenerativeModel('gemini-pro')
    else:
        AI_MODEL = None
except Exception:
    AI_MODEL = None


def get_monitor_resolution():
    try:
        root = tk.Tk()
        root.withdraw()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return f"{width}x{height}"
    except Exception:
        return "Unknown"


def get_cpu_name():
    try:
        if platform.system() == 'Windows' and wmi:
            c = wmi.WMI()
            for proc in c.Win32_Processor():
                return proc.Name
        if platform.system() == 'Linux':
            with open('/proc/cpuinfo', 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if 'model name' in line:
                        return line.split(':', 1)[1].strip()
        if platform.system() == 'Darwin':
            return subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], encoding='utf-8').strip()
    except Exception:
        pass
    return platform.processor() or 'Unknown CPU'


def get_gpu_name():
    # Try GPUtil first
    try:
        if GPUtil:
            gpus = GPUtil.getGPUs()
            if gpus:
                return gpus[0].name, f"{gpus[0].memoryTotal}MB"
    except Exception:
        pass

    # Fallbacks per OS
    try:
        if platform.system() == 'Windows':
            out = subprocess.check_output(['wmic', 'path', 'win32_VideoController', 'get', 'name'], encoding='utf-8')
            lines = [l.strip() for l in out.splitlines() if l.strip() and 'Name' not in l]
            if lines:
                return lines[0], None
        elif platform.system() == 'Linux':
            try:
                out = subprocess.check_output(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], encoding='utf-8')
                if out.strip():
                    return out.strip(), None
            except Exception:
                out = subprocess.check_output(['lspci'], encoding='utf-8')
                for line in out.splitlines():
                    if 'VGA' in line or 'Display' in line:
                        return line.split(':')[-1].strip(), None
        elif platform.system() == 'Darwin':
            out = subprocess.check_output(['system_profiler', 'SPDisplaysDataType'], encoding='utf-8')
            for line in out.splitlines():
                if 'Chipset Model:' in line:
                    return line.split(':', 1)[1].strip(), None
    except Exception:
        pass
    return 'Unknown GPU', None


def get_system_specs():
    specs = {}
    specs['os'] = f"{platform.system()} {platform.release()}"
    specs['resolution'] = get_monitor_resolution()

    specs['cpu'] = get_cpu_name()
    specs['cpu_cores'] = psutil.cpu_count(logical=False) or 0
    specs['cpu_threads'] = psutil.cpu_count(logical=True) or 0

    gpu_name, gpu_mem = get_gpu_name()
    specs['gpu'] = gpu_name
    if gpu_mem:
        specs['gpu_memory'] = gpu_mem

    ram = psutil.virtual_memory()
    specs['ram_total_gb'] = round(ram.total / (1024 ** 3), 2)
    specs['ram_available_gb'] = round(ram.available / (1024 ** 3), 2)

    # Use platform-appropriate root for disk usage
    root_path = os.path.abspath(os.sep)
    try:
        disk = psutil.disk_usage(root_path)
        specs['storage_free_gb'] = round(disk.free / (1024 ** 3), 2)
    except Exception:
        specs['storage_free_gb'] = 'Unknown'

    return specs


def search_game_by_name(game_name):
    url = f"https://steamcommunity.com/actions/SearchApps/{game_name}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        results = r.json()
        return [{'app_id': g['appid'], 'name': g['name']} for g in results] if results else []
    except Exception:
        return []


def get_game_requirements(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        entry = data.get(str(app_id), {})
        if not entry.get('success'):
            return {'error': 'Game not found or data unavailable'}
        game_data = entry.get('data', {})
        pc_req = game_data.get('pc_requirements', {})
        return {
            'name': game_data.get('name', 'Unknown'),
            'app_id': app_id,
            'pc_requirements': {
                'minimum': pc_req.get('minimum', 'Not specified'),
                'recommended': pc_req.get('recommended', 'Not specified')
            }
        }
    except Exception:
        return {'error': 'Failed to fetch game data'}


def clean_html_requirements(html_text):
    if not html_text or html_text == 'Not specified':
        return html_text
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text(separator='\n', strip=True)


def format_requirements_for_ai(requirements):
    if 'error' in requirements:
        return f"Error: {requirements['error']}"
    out = f"GAME REQUIREMENTS FOR: {requirements.get('name','Unknown')}\n"
    out += '=' * 50 + '\n'
    pc = requirements.get('pc_requirements', {})
    if pc.get('minimum') and pc.get('minimum') != 'Not specified':
        out += '\nMinimum Requirements:\n'
        out += clean_html_requirements(pc['minimum']) + '\n'
    if pc.get('recommended') and pc.get('recommended') != 'Not specified':
        out += '\nRecommended Requirements:\n'
        out += clean_html_requirements(pc['recommended']) + '\n'
    return out


def format_system_specs(specs):
    out = 'YOUR PC SPECS:\n'
    out += '=' * 50 + '\n'
    out += f"OS: {specs.get('os','Unknown')}\n"
    out += f"Resolution: {specs.get('resolution','Unknown')}\n"
    out += f"CPU: {specs.get('cpu','Unknown')}\n"
    out += f"Cores/Threads: {specs.get('cpu_cores','?')}/{specs.get('cpu_threads','?')}\n"
    out += f"GPU: {specs.get('gpu','Unknown')}\n"
    if 'gpu_memory' in specs:
        out += f"GPU Memory: {specs['gpu_memory']}\n"
    out += f"RAM: {specs.get('ram_total_gb','?')} GB (Available: {specs.get('ram_available_gb','?')} GB)\n"
    out += f"Free Storage: {specs.get('storage_free_gb','?')} GB\n"
    return out


def ask_ai(prompt):
    if not AI_MODEL:
        return 'AI not configured. Set the GOOGLE_API_KEY environment variable to enable AI analysis.'
    try:
        resp = AI_MODEL.generate_content(prompt)
        return getattr(resp, 'text', str(resp))
    except Exception as e:
        return f'AI Error: {e}'


def compare_specs_with_ai(game_name, requirements_text, system_specs_text, system_specs):
    prompt = f"{system_specs_text}\n\n{requirements_text}\n\nQuestion: Can my PC run {game_name}?"
    return ask_ai(prompt)


# --- GUI and integration ---
game_entry = None
output_box = None


def thread_check(game_name):
    if not output_box:
        return
    try:
        output_box.insert(tk.END, 'Detecting system specifications...\n')
        output_box.see(tk.END)
        specs = get_system_specs()

        output_box.insert(tk.END, f"Searching Steam for '{game_name}'...\n")
        output_box.see(tk.END)
        results = search_game_by_name(game_name)
        if not results:
            output_box.insert(tk.END, '\nNo games found.\n\n')
            return

        game = results[0]
        output_box.insert(tk.END, f"Found: {game['name']}\n")
        output_box.insert(tk.END, 'Fetching requirements...\n')
        output_box.see(tk.END)

        req = get_game_requirements(game['app_id'])
        if 'error' in req:
            output_box.insert(tk.END, f"\nError: {req['error']}\n\n")
            return

        req_text = format_requirements_for_ai(req)
        specs_text = format_system_specs(specs)

        output_box.insert(tk.END, '\n' + req_text + '\n')
        output_box.see(tk.END)

        output_box.insert(tk.END, 'Analyzing compatibility with AI (if configured)...\n')
        output_box.insert(tk.END, '=' * 60 + '\n')
        output_box.see(tk.END)

        ai_resp = compare_specs_with_ai(game['name'], req_text, specs_text, specs)
        output_box.insert(tk.END, '\nAI COMPATIBILITY ANALYSIS:\n')
        output_box.insert(tk.END, '=' * 60 + '\n')
        output_box.insert(tk.END, ai_resp + '\n\n')
        output_box.see(tk.END)
    except Exception as e:
        output_box.insert(tk.END, f"\nError: {e}\n\n")


def on_run(event=None):
    game = game_entry.get().strip()
    if not game:
        output_box.insert(tk.END, 'Please enter a game name.\n\n')
        return
    output_box.delete(1.0, tk.END)
    output_box.insert(tk.END, f"Checking: {game}\n" + '=' * 60 + '\n\n')
    t = threading.Thread(target=thread_check, args=(game,))
    t.daemon = True
    t.start()


def show_specs_cmd():
    output_box.delete(1.0, tk.END)
    output_box.insert(tk.END, 'Detecting system specifications...\n\n')
    specs = get_system_specs()
    output_box.insert(tk.END, format_system_specs(specs) + '\n')


def main():
    global game_entry, output_box
    window = tk.Tk()
    window.title('System Hardware Compatibility Checker')
    window.geometry('900x600')
    window.configure(bg='black')

    title = tk.Label(window, text='System Hardware Compatibility Checker', font=('Arial', 18), fg='white', bg='black')
    title.pack(pady=10)

    input_frame = tk.Frame(window, bg='black')
    input_frame.pack(pady=10)

    tk.Label(input_frame, text='Enter Game Name:', fg='white', bg='black').grid(row=0, column=0, padx=5)
    game_entry = tk.Entry(input_frame, width=40)
    game_entry.grid(row=0, column=1, padx=5)
    game_entry.focus_set()

    window.bind('<Return>', lambda e: on_run())

    tk.Label(window, text='Press Enter to check compatibility', fg='white', bg='black').pack(pady=5)

    tk.Button(window, text='Show System Specs', command=show_specs_cmd, bg='#333333', fg='white').pack(pady=5)

    output_box = scrolledtext.ScrolledText(window, width=100, height=20, bg='black', fg='white', insertbackground='white', font=('Consolas', 9))
    output_box.pack(pady=10)

    window.mainloop()


if __name__ == '__main__':
    main()