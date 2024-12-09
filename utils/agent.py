# /utils/agent.py
from langchain.agents import AgentExecutor, create_react_agent
from langchain_experimental.tools import PythonAstREPLTool

from utils.contants import MODELS
from utils.tools import get_screen_info
from utils.system_check import get_system_specific_commands

import pyautogui as pg
import platform
import time

class SystemSpecificPyAutoGUI:
    def __init__(self, system):
        self.system = system
        self.commands = get_system_specific_commands(system)
        self.pg = pg
        self.pg.PAUSE = 2
        
        # Set up system-specific configurations
        if system == "darwin":  # macOS
            self.pg.FAILSAFE = True
            # macOS might need a longer pause for some operations
            self.pg.PAUSE = 2.5
        elif system == "linux":
            # Linux might need different screenshot backend
            self.pg.FAILSAFE = True
            self.pg.PAUSE = 2
        else:  # windows
            self.pg.FAILSAFE = True
            self.pg.PAUSE = 2

    def press(self, key):
        """Handle system-specific key press translations"""
        key_mapping = {
            "win": self.commands["menu_key"],
            "windows": self.commands["menu_key"],
            "super": self.commands["menu_key"],
            "command": self.commands["menu_key"],
            "print_screen": self.commands["screenshot_key"],
            "printscreen": self.commands["screenshot_key"]
        }
        
        actual_key = key_mapping.get(key.lower(), key)
        return self.pg.press(actual_key)

    def hotkey(self, *args):
        """Handle system-specific hotkey translations"""
        translated_args = []
        for arg in args:
            if arg.lower() in ["win", "windows", "super", "command"]:
                translated_args.append(self.commands["menu_key"])
            else:
                translated_args.append(arg)
        return self.pg.hotkey(*translated_args)

    def __getattr__(self, name):
        """Delegate all other attributes to the original pyautogui"""
        return getattr(self.pg, name)

def create_stella_agent(model, prompt):
    """Create an agent with system-specific PyAutoGUI handling"""
    print("============================================")
    print("Initialising Stella Agent")
    print(f"Operating System: {platform.system()}")
    print("============================================")
    
    def create_system_specific_locals(system):
        system_pg = SystemSpecificPyAutoGUI(system)
        return {
            "pg": system_pg,
            "time": time,
            "get_commands": lambda: get_system_specific_commands(system)
        }

    def create_tool_with_system(system):
        locals_dict = create_system_specific_locals(system)
        return PythonAstREPLTool(locals=locals_dict)

    tools = [
        create_tool_with_system(platform.system().lower()),
        get_screen_info
    ]

    agent = create_react_agent(model, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )

    return agent_executor