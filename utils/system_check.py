# /utils/system_check.py
import platform
import subprocess
import shutil
from typing import Optional

def check_system_permissions(system: str) -> Optional[str]:
    """
    Check if the system has the necessary permissions and dependencies for Stella to run.
    Returns a string of missing permissions/requirements, or None if everything is okay.
    """
    missing = []
    
    if system == "darwin":  # macOS
        # Check screen recording permission
        try:
            result = subprocess.run(
                ['tccutil', 'check', 'Screen Recording', 'com.apple.Terminal'],
                capture_output=True,
                text=True
            )
            if "denied" in result.stdout.lower():
                missing.append("- Screen Recording permission (System Preferences -> Security & Privacy -> Privacy -> Screen Recording)")
        except Exception:
            missing.append("- Screen Recording permission check failed")
            
        # Check accessibility permission
        try:
            result = subprocess.run(
                ['tccutil', 'check', 'Accessibility', 'com.apple.Terminal'],
                capture_output=True,
                text=True
            )
            if "denied" in result.stdout.lower():
                missing.append("- Accessibility permission (System Preferences -> Security & Privacy -> Privacy -> Accessibility)")
        except Exception:
            missing.append("- Accessibility permission check failed")
            
    elif system == "linux":
        # Check for X11 or Wayland
        if not shutil.which('xdg-open'):
            missing.append("- xdg-utils package is required")
            
        # Check for required X11 packages
        if not shutil.which('xdotool'):
            missing.append("- xdotool package is required")
            
        # Check for screenshot capabilities
        if not any(shutil.which(x) for x in ['gnome-screenshot', 'scrot']):
            missing.append("- Screenshot tool (gnome-screenshot or scrot) is required")
            
    elif system == "windows":
        # Check if running with admin privileges might be needed for some operations
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                missing.append("- Some features might require running as administrator")
        except Exception:
            pass
        
        # Check for required Windows dependencies
        try:
            import win32gui
            import win32con
        except ImportError:
            missing.append("- pywin32 package is required (pip install pywin32)")

    # Common checks for all platforms
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        missing.append("- Pillow package is required (pip install Pillow)")

    # Check Python version
    if platform.python_version_tuple()[0] < "3" or \
       (platform.python_version_tuple()[0] == "3" and platform.python_version_tuple()[1] < "8"):
        missing.append("- Python 3.8 or higher is required")

    return "\n".join(missing) if missing else None

def get_system_specific_commands(system: str) -> dict:
    """
    Returns a dictionary of system-specific commands and configurations.
    """
    commands = {
        "darwin": {
            "menu_key": "command",
            "screenshot_key": "shift+command+3",
            "window_capture": "shift+command+4",
            "close_window": "command+w",
            "new_window": "command+n",
            "font_path": "/System/Library/Fonts/SFPro.ttf"
        },
        "linux": {
            "menu_key": "super",
            "screenshot_key": "print",
            "window_capture": "alt+print",
            "close_window": "alt+f4",
            "new_window": "ctrl+n",
            "font_path": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        },
        "windows": {
            "menu_key": "win",
            "screenshot_key": "print",
            "window_capture": "alt+print",
            "close_window": "alt+f4",
            "new_window": "ctrl+n",
            "font_path": "C:\\Windows\\Fonts\\arial.ttf"
        }
    }
    
    return commands.get(system, commands["windows"])