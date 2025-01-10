import psutil
import os
import subprocess
import sys

def hide_process_by_name(process_name):
    # Sprawdzamy, na jakim systemie działamy
    platform = sys.platform

    if platform == "darwin":
        # Użycie AppleScript do ukrycia aplikacji na macOS
        script = f'''
        tell application "{process_name}"
            set visible to false
        end tell
        '''
        try:
            subprocess.run(["osascript", "-e", script])
            print(f"Proces {process_name} został ukryty (macOS).")
        except Exception as e:
            print(f"Błąd podczas ukrywania procesu: {e}")
        return

    # Inne platformy (Windows/Linux) można obsługiwać dalej jak wcześniej
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        try:
            # Sprawdzamy, czy proces ma taką samą nazwę
            if process_name.lower() in proc.info['name'].lower():
                pid = proc.info['pid']
                print(f"Znaleziono proces: {process_name} (PID: {pid})")
                # Dla Windows
                if platform == "win32":
                    os.system(f"start /B {process_name} >nul 2>&1")
                    print(f"Proces {process_name} został uruchomiony w tle (Windows).")

                # Dla Linux/macOS
                elif platform in ["linux", "darwin"]:
                    os.system(f"nohup {process_name} > /dev/null 2>&1 &")
                    print(f"Proces {process_name} został uruchomiony w tle (Linux/macOS).")
                    
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    else:
        print(f"Proces o nazwie {process_name} nie został znaleziony.")

# Przykład użycia
hide_process_by_name("Safari")  # MacOS

