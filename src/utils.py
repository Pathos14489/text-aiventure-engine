import os
from uuid import uuid4


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

class bcolors:
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    GREY = '\033[90m'
    BOLD = '\033[1m'
    ITALICS = '\033[3m'
    UNDERLINE = '\033[4m'
    MAGENTA = '\033[35m'
    ENDC = '\033[00m'
    
valid_hex = '0123456789ABCDEF'.__contains__
def cleanhex(data):
    return ''.join(filter(valid_hex, data.upper()))

def fore_fromhex(hexcode):
    """print in a hex defined color"""
    hexint = int(cleanhex(hexcode), 16)
    return f"\x1B[38;2;{hexint>>16};{hexint>>8&0xFF};{hexint&0xFF}m"

def format_colored_text(text, color:str):
    """format text in a hex defined color"""
    color = color.upper()
    if color in bcolors.__dict__:
        color_code = getattr(bcolors, color)
        return f"{color_code}{text}{bcolors.ENDC}"
    else:
        return text
    
def format_italic_text(text):
    """format text in italics"""
    return f"{bcolors.ITALICS}{text}{bcolors.ENDC}"

def format_bold_text(text):
    """format text in bold"""
    return f"{bcolors.BOLD}{text}{bcolors.ENDC}"

def split_at_nearest_space(text: str, max_length: int) -> list[str]:
    """Split text into a list of strings, each no longer than max_length, at the nearest space."""
    lines = []
    current_line = ""
    words = text.split(' ')
    for word in words:
        if len(current_line) + len(word) + 1 <= max_length:
            if current_line:
                current_line += ' '
            current_line += word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def print_colored(text, color:str):
    color = color.upper()
    if color in bcolors.__dict__:
        color_code = getattr(bcolors, color)
        print(f"{color_code}{text}{bcolors.ENDC}")
    else:
        print(text)
    
def print_in_box(texts, color:str="GREEN", text_color:str="GREEN", first_line_color:str="GREEN", color_text: bool = False, max_length: int = -1):
    color = color.upper()
    if color in bcolors.__dict__:
        color_code = getattr(bcolors, color)
    else:
        color_code = ""
    # local import to avoid changing top-level imports
    import re
    if isinstance(texts, str):
        texts = [texts]
    for text in texts:
        if max_length > 0:
            lines = split_at_nearest_space(text, max_length)
            text = '\n'.join(lines)
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        lines = text.split('\n')

        def visible_len(s: str) -> int:
            return len(ansi_escape.sub('', s))

        max_length = max(visible_len(line) for line in lines)
        border = '+' + '-' * (max_length + 2) + '+'
        print(f"{color_code}{border}{bcolors.ENDC}")
        index = 0
        for line in lines:
            pad = max_length - visible_len(line)
            # pad using visible length so ANSI codes don't break alignment
            if color_text and index == 0:
                print(f"{color_code}|{bcolors.ENDC} {first_line_color}{line}{bcolors.ENDC}{' ' * pad} {color_code}|{bcolors.ENDC}")
            elif color_text:
                print(f"{color_code}|{bcolors.ENDC} {text_color}{line}{bcolors.ENDC}{' ' * pad} {color_code}|{bcolors.ENDC}")
            else:
                print(f"{color_code}|{bcolors.ENDC} {line}{' ' * pad} {color_code}|{bcolors.ENDC}")
            index += 1
        print(f"{color_code}{border}{bcolors.ENDC}")

def print_chatbox(speaker: str, message: str, speaker_color: str="CYAN", message_color: str="GREEN", box_color: str="GREEN"):
    speaker_text = format_colored_text(speaker, speaker_color)
    message_text = format_colored_text(message, message_color)
    print_in_box([f"{speaker_text}\n{message_text}"], color=box_color, first_line_color=speaker_color, color_text=False)

def preprocess(data, base_ten_field_names = [], base_one_hundred_field_names = []):
    for field in data:
        if isinstance(data[field], int):
            data[field] = max(0, data[field])
            if field in base_ten_field_names:
                data[field] = min(10, data[field])
            elif field in base_one_hundred_field_names:
                data[field] = min(100, data[field])
        elif isinstance(data[field], dict):
            data[field] = preprocess(data[field])
    return data

def generate_id():
    return str(uuid4())