# /main.py
from utils.agent import create_stella_agent
from utils.prompt import prompt
from utils.contants import *
from utils.system_check import check_system_permissions

import time
import pyautogui as pg
import argparse
from tkinter import *
from tkinter import ttk, messagebox
import json
import os

pg.PAUSE = 2

class StellaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stella")
        self.load_config()
        self.setup_ui()
        self.check_permissions()

    def load_config(self):
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    'system': CURRENT_SYSTEM,
                    'model': 'openai',
                    'float_ui': True
                }
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = {
                'system': CURRENT_SYSTEM,
                'model': 'openai',
                'float_ui': True
            }

    def save_config(self):
        try:
            with open('config.json', 'w') as f:
                json.dump(self.config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def check_permissions(self):
        missing_permissions = check_system_permissions(self.config['system'])
        if missing_permissions:
            messagebox.showwarning(
                "Permissions Required",
                f"The following permissions are required:\n\n{missing_permissions}\n\nPlease enable them to use Stella."
            )

    def setup_ui(self):
        # Set window size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.3)
        window_height = screen_height - 150
        self.root.geometry(f"{window_width}x{window_height}")

        # Create top frame for settings
        settings_frame = Frame(self.root, bg=BG_COLOR)
        settings_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        # System selection dropdown
        Label(settings_frame, text="System:", bg=BG_COLOR).pack(side=LEFT, padx=5)
        self.system_var = StringVar(value=self.config['system'].capitalize())
        system_dropdown = ttk.Combobox(
            settings_frame, 
            textvariable=self.system_var,
            values=list(SUPPORTED_SYSTEMS.keys()),
            state="readonly",
            width=10
        )
        system_dropdown.pack(side=LEFT, padx=5)
        system_dropdown.bind('<<ComboboxSelected>>', self.on_system_change)

        # Float UI toggle
        self.float_var = BooleanVar(value=self.config['float_ui'])
        float_check = Checkbutton(
            settings_frame,
            text="Float Window",
            variable=self.float_var,
            bg=BG_COLOR,
            command=self.on_float_change
        )
        float_check.pack(side=RIGHT, padx=5)

        # Welcome label
        Label(
            self.root,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            text="Welcome to Stella",
            font=FONT_BOLD,
            pady=10,
            width=30,
            height=2
        ).grid(row=1, column=0, columnspan=2)

        # Chat area
        self.txt = Text(
            self.root,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=FONT,
            width=40,
            height=30
        )
        self.txt.grid(row=2, column=0, columnspan=2)

        # Scrollbar
        scrollbar = Scrollbar(self.txt)
        scrollbar.place(relheight=1, relx=0.974)

        # Input area
        self.input_entry = Entry(
            self.root,
            bg="#FCFCFC",
            fg=TEXT_COLOR,
            font=FONT,
            width=30
        )
        self.input_entry.grid(row=3, column=0, pady=5)
        self.input_entry.bind('<Return>', lambda e: self.send())

        # Send button
        Button(
            self.root,
            text="Send",
            font=FONT_BOLD,
            bg=BG_GRAY,
            command=self.send
        ).grid(row=3, column=1)

        # Initialize agent
        self.agent_executor = create_stella_agent(MODELS[self.config['model']], prompt)
        
        # Set window attributes
        self.root.attributes('-topmost', self.config['float_ui'])

    def on_system_change(self, event):
        selected = self.system_var.get().lower()
        if selected != self.config['system']:
            self.config['system'] = selected
            self.save_config()
            self.check_permissions()

    def on_float_change(self):
        self.config['float_ui'] = self.float_var.get()
        self.root.attributes('-topmost', self.config['float_ui'])
        self.save_config()

    def send(self):
        user_input = self.input_entry.get().lower()
        if user_input.strip():
            self.txt.insert(END, f"\nYou -> {user_input}")
            self.input_entry.delete(0, END)
            try:
                time.sleep(1.5)
                response = self.agent_executor.invoke({
                    "input": user_input,
                    "system": self.config['system']
                })
                self.txt.insert(END, f"\nBot -> {response.get('output')}")
            except Exception as e:
                self.txt.insert(END, f"\nBot -> Error: {str(e)}")
            self.txt.see(END)

def main():
    parser = argparse.ArgumentParser(description="Launch Stella with optional settings.")
    parser.add_argument('--model', type=str, default='openai', choices=['openai'],
                    help="Choose the model to use. Default is 'openai'.")
    args = parser.parse_args()

    root = Tk()
    app = StellaApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()