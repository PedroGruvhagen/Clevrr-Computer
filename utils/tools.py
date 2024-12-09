# /utils/tools.py
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.tools import tool

from utils.contants import MODELS, SYSTEM_FONTS
from utils.system_check import get_system_specific_commands

from PIL import Image, ImageDraw, ImageFont
import pyautogui as pg
import base64
import platform
import os

pg.PAUSE = 2

def get_system_font():
    """Get the appropriate system font based on the operating system."""
    system = platform.system().lower()
    try:
        # Try system-specific font first
        system_commands = get_system_specific_commands(system)
        font_path = system_commands["font_path"]
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, 25)
        
        # Try system font name
        system_font = SYSTEM_FONTS.get(system, "arial")
        return ImageFont.truetype(system_font, 25)
    except Exception:
        # Fallback to default font if nothing else works
        return ImageFont.load_default()

def get_ruled_screenshot():
    """Take and annotate a screenshot with coordinates, handling different OS requirements."""
    # Ensure we have permission to take screenshots
    try:
        image = pg.screenshot()
    except pg.FailSafeException:
        raise Exception("Failed to take screenshot. Please check permissions.")

    # Get the image dimensions
    width, height = image.size

    # Create a new image for the semi-transparent layer
    overlay = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # Set the line color and opacity
    line_color = (200, 200, 0, 128)

    # Get appropriate font for the system
    font = get_system_font()

    # Draw vertical and horizontal lines with labels
    for x in range(0, width, 50):
        draw.line([(x, 0), (x, height)], fill=line_color, width=1)
        if x % 100 == 0:
            draw.text((x + 5, 5), str(x), font=font, fill=(250, 250, 0, 128))
            draw.text((x, height - 25), str(x), font=font, fill=(250, 250, 0, 128))

    for y in range(0, height, 50):
        draw.line([(0, y), (width, y)], fill=line_color, width=1)
        if y % 100 == 0:
            draw.text((5, y + 5), str(y), font=font, fill=(0, 250, 250, 128))
            text_width = 35  # Approximate width for the coordinate text
            draw.text((width - text_width - 5, y + 5), str(y), font=font, fill=(0, 250, 250, 128))

    # Convert screenshot to RGBA for proper merging
    image = image.convert("RGBA")

    # Merge the overlay with the original image
    combined = Image.alpha_composite(image, overlay)
    
    # Ensure the screenshots directory exists
    os.makedirs('screenshots', exist_ok=True)
    screenshot_path = os.path.join('screenshots', 'current_screenshot.png')
    
    try:
        combined.save(screenshot_path)
        return screenshot_path
    except Exception as e:
        raise Exception(f"Failed to save screenshot: {str(e)}")

class ScreenInfo(BaseModel):
    query: str = Field(description="should be a question about the screenshot of the current screen. Should always be in text.")

@tool(args_schema=ScreenInfo)
def get_screen_info(question: str) -> dict:
    """Tool to get the information about the current screen based on the user's question."""
    try:
        screenshot_path = get_ruled_screenshot()
        with open(screenshot_path, "rb") as image:
            image_data = base64.b64encode(image.read()).decode("utf-8")
            
            messages = [
                SystemMessage(
                content=f"""You are a Computer agent that is responsible for answering questions based on the input provided to you. 
                        You will have access to the screenshot of the current screen of the user along with a grid marked with true coordinates of the screen. 
                        The size of the screen is {pg.size()[0]} x {pg.size()[1]} px.
                        ONLY rely on the coordinates marked in the screen. DO NOT create an assumption of the coordinates. 
                        Here's how you can help:
                        1. Find out coordinates of a specific thing. You have to be super specific about the coordinates. 
                        2. Give information on the contents of the screen.
                        3. Analyse the screen to give instructions to perform further steps.
                        
                        Note: Coordinate system might be different based on the operating system:
                        - Windows: Top-left origin (0,0)
                        - macOS: Bottom-left origin (0,0)
                        - Linux: Top-left origin (0,0)
                        
                        Always specify coordinates relative to the visible grid."""
                ),
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": f"{question}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        }
                    ]
                )
            ]
            
            image_model = MODELS["openai"]
            response = image_model.invoke(messages)
            return response.content
            
    except Exception as e:
        return {"error": f"Screen info error: {str(e)}"}