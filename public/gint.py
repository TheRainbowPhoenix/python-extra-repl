from js import document, Math, ImageData, Uint8Array, Uint8ClampedArray, Date, setTimeout
from pyodide.ffi import create_proxy, to_js, JsPromise
import pyodide.webloop as webloop
from collections import deque
import asyncio
import js
import pyodide
import time

loop = webloop.WebLoop()

# Constants
DWIDTH = 320
DHEIGHT = 512
C_WHITE = 0xFFFFFF
C_BLACK = 0x000000
C_RED = 0xFF0000
C_GREEN = 0x00FF00
C_BLUE = 0x0000FF
C_NONE = -1

# Image Constants
IMAGE_MONO = 0
IMAGE_P4_RGB565 = 1
IMAGE_RGB565 = 2

# Text alignment constants
DTEXT_LEFT = 'left'
DTEXT_CENTER = 'center'
DTEXT_RIGHT = 'right'
DTEXT_TOP = 'top'
DTEXT_MIDDLE = 'middle'
DTEXT_BOTTOM = 'bottom'

# Canvas setup
_canvas = document.getElementById("mainCanvas")
_ctx = _canvas.getContext("2d")
_offscreen = document.createElement("canvas")
_ctx_offscreen = _offscreen.getContext("2d")

# Initialize canvases
_canvas.width = _offscreen.width = DWIDTH
_canvas.height = _offscreen.height = DHEIGHT
_canvas.style.width = f"{DWIDTH}px"
_canvas.style.height = f"{DHEIGHT}px"
_ctx_offscreen.font = "12px monospace"

def C_RGB(r: int, g: int, b: int) -> int:
    """Create RGB888 from RGB555"""
    # return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    r8 = (r << 3) | (r >> 2)
    g8 = (g << 3) | (g >> 2)
    b8 = (b << 3) | (b >> 2)

    # Pack into 24-bit RGB888 format (0xRRGGBB)
    return (r8 << 16) | (g8 << 8) | b8



def dclear(color: int):
    if color == C_NONE: return
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    _ctx_offscreen.fillStyle = f"rgb({r},{g},{b})"
    _ctx_offscreen.fillRect(0, 0, DWIDTH, DHEIGHT)

def dupdate():
    """Update display with VRAM changes"""
    _ctx.drawImage(_offscreen, 0, 0)


def dpixel(x: int, y: int, color: int):
    if color == C_NONE: return
    if not (0 <= x < DWIDTH and 0 <= y < DHEIGHT):
        return
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    _ctx_offscreen.fillStyle = f"rgb({r},{g},{b})"
    _ctx_offscreen.fillRect(x, y, 1, 1)

def dgetpixel(x: int, y: int) -> int:
    if not (0 <= x < DWIDTH and 0 <= y < DHEIGHT):
        return -1
    img_data = _ctx_offscreen.getImageData(x, y, 1, 1).data
    return (img_data[0] << 16) | (img_data[1] << 8) | img_data[2]

def drect(x1: int, y1: int, x2: int, y2: int, color: int):
    if color == C_NONE: return
    x = min(x1, x2)
    y = min(y1, y2)
    w = abs(x2 - x1)
    h = abs(y2 - y1)
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    _ctx_offscreen.fillStyle = f"rgb({r},{g},{b})"
    _ctx_offscreen.fillRect(x, y, w, h)

def drect_border(x1: int, y1: int, x2: int, y2: int, 
               fill: int, border_width: int, border: int):
    if fill != C_NONE:
        drect(x1, y1, x2, y2, fill)
    
    if border != C_NONE and border_width > 0:
        r = (border >> 16) & 0xFF
        g = (border >> 8) & 0xFF
        b = border & 0xFF
        _ctx_offscreen.strokeStyle = f"rgb({r},{g},{b})"
        _ctx_offscreen.lineWidth = border_width
        _ctx_offscreen.strokeRect(
            min(x1, x2) + border_width/2,
            min(y1, y2) + border_width/2,
            abs(x2 - x1) - border_width,
            abs(y2 - y1) - border_width
        )

def dline(x1: int, y1: int, x2: int, y2: int, color: int):
    if color == C_NONE: return
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    _ctx_offscreen.beginPath()
    _ctx_offscreen.moveTo(x1, y1)
    _ctx_offscreen.lineTo(x2, y2)
    _ctx_offscreen.strokeStyle = f"rgb({r},{g},{b})"
    _ctx_offscreen.stroke()

def dhline(y: int, color: int):
    dline(0, y, DWIDTH-1, y, color)

def dvline(x: int, color: int):
    dline(x, 0, x, DHEIGHT-1, color)

def dcircle(x: int, y: int, r: int, fill: int, border: int):
    _ctx_offscreen.beginPath()
    _ctx_offscreen.arc(x, y, r, 0, 2 * Math.PI)
    
    if fill != None and fill != C_NONE:
        r_fill = (fill >> 16) & 0xFF
        g_fill = (fill >> 8) & 0xFF
        b_fill = fill & 0xFF
        _ctx_offscreen.fillStyle = f"rgb({r_fill},{g_fill},{b_fill})"
        _ctx_offscreen.fill()
    
    if border != None and border != C_NONE:
        r_border = (border >> 16) & 0xFF
        g_border = (border >> 8) & 0xFF
        b_border = border & 0xFF
        _ctx_offscreen.strokeStyle = f"rgb({r_border},{g_border},{b_border})"
        _ctx_offscreen.stroke()

def dellipse(x1: int, y1: int, x2: int, y2: int, fill: int, border: int):
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    rx = abs(x2 - x1) / 2
    ry = abs(y2 - y1) / 2
    
    _ctx_offscreen.beginPath()
    _ctx_offscreen.ellipse(cx, cy, rx, ry, 0, 0, 2 * Math.PI)
    
    if fill != None and fill != C_NONE:
        r_fill = (fill >> 16) & 0xFF
        g_fill = (fill >> 8) & 0xFF
        b_fill = fill & 0xFF
        _ctx_offscreen.fillStyle = f"rgb({r_fill},{g_fill},{b_fill})"
        _ctx_offscreen.fill()
    
    if border != None and border != C_NONE:
        r_border = (border >> 16) & 0xFF
        g_border = (border >> 8) & 0xFF
        b_border = border & 0xFF
        _ctx_offscreen.strokeStyle = f"rgb({r_border},{g_border},{b_border})"
        _ctx_offscreen.stroke()

def dpoly(vertices: list[int], fill: int, border: int):
    if len(vertices) % 2 != 0:
        raise ValueError("Vertices must contain even number of coordinates")
        
    points = [(vertices[i], vertices[i+1]) for i in range(0, len(vertices), 2)]
    
    _ctx_offscreen.beginPath()
    _ctx_offscreen.moveTo(points[0][0], points[0][1])
    for x, y in points[1:]:
        _ctx_offscreen.lineTo(x, y)
    _ctx_offscreen.closePath()

    if fill != C_NONE:
        r = (fill >> 16) & 0xFF
        g = (fill >> 8) & 0xFF
        b = fill & 0xFF
        _ctx_offscreen.fillStyle = f"rgb({r},{g},{b})"
        _ctx_offscreen.fill()

    if border != C_NONE:
        r = (border >> 16) & 0xFF
        g = (border >> 8) & 0xFF
        b = border & 0xFF
        _ctx_offscreen.strokeStyle = f"rgb({r},{g},{b})"
        _ctx_offscreen.stroke()

def dtext(x: int, y: int, fg: int, text: str):
    if fg == C_NONE: return
    r = (fg >> 16) & 0xFF
    g = (fg >> 8) & 0xFF
    b = fg & 0xFF
    _ctx_offscreen.fillStyle = f"rgb({r},{g},{b})"
    _ctx_offscreen.fillText(text, x, y)

def dtext_opt(x: int, y: int, fg: int, bg: int, 
            halign: str, valign: str, text: str, size: int = -1):
    # Set up text properties
    _ctx_offscreen.textAlign = halign
    _ctx_offscreen.textBaseline = valign
    
    # Calculate text metrics
    metrics = _ctx_offscreen.measureText(text)
    text_width = metrics.width
    text_height = 12  # Approximate based on font size
    
    # Draw background
    if bg != C_NONE:
        r = (bg >> 16) & 0xFF
        g = (bg >> 8) & 0xFF
        b = bg & 0xFF
        _ctx_offscreen.fillStyle = f"rgb({r},{g},{b})"
        
        # Calculate background position
        bg_x = x
        bg_y = y - text_height  # Adjust for baseline
        
        if halign == DTEXT_CENTER:
            bg_x -= text_width / 2
        elif halign == DTEXT_RIGHT:
            bg_x -= text_width
            
        _ctx_offscreen.fillRect(
            bg_x, bg_y, 
            text_width, text_height
        )

    # Draw text
    if fg != C_NONE:
        r = (fg >> 16) & 0xFF
        g = (fg >> 8) & 0xFF
        b = fg & 0xFF
        _ctx_offscreen.fillStyle = f"rgb({r},{g},{b})"
        _ctx_offscreen.fillText(text, x, y)


# ---- Image

class image:
    """Represents a graphical image in VRAM"""
    def __init__(self, profile: int, width: int, height: int,
                stride: int, color_count: int,
                data: bytes, palette: bytes):
        self.profile = profile
        self.width = width
        self.height = height
        self.stride = stride
        self.color_count = color_count
        self.data = data
        self.palette = palette
        self.js_image_data = self._decode_image()

    def _decode_image(self):
        js_data = Uint8Array.new(to_js(self.data))
        js_palette = Uint8Array.new(to_js(self.palette))
        image_data = ImageData.new(self.width, self.height)
        pixels = image_data.data

        if self.profile == IMAGE_P4_RGB565:
            # Decode 4bpp palette-based image
            palette_rgba = []
            for i in range(0, len(js_palette), 2):
                rgb565 = (js_palette[i] << 8) | js_palette[i+1]
                r = (rgb565 >> 11) * 255 // 31
                g = ((rgb565 >> 5) & 0x3F) * 255 // 63
                b = (rgb565 & 0x1F) * 255 // 31
                palette_rgba.extend([r, g, b, 255])

            for y in range(self.height):
                for x in range(self.width):
                    byte_idx = y * self.stride + (x // 2)
                    byte = js_data[byte_idx]
                    nibble = (byte >> 4) if x % 2 == 0 else (byte & 0x0F)
                    px_idx = (y * self.width + x) * 4
                    for i in range(4):

                        pixels[px_idx+i] = palette_rgba[nibble*4+i]

        elif self.profile == IMAGE_RGB565:
            # Decode 16bpp direct color
            for y in range(self.height):
                for x in range(self.width):
                    px_idx = (y * self.width + x) * 2
                    rgb565 = (js_data[px_idx] << 8) | js_data[px_idx+1]
                    r = (rgb565 >> 11) * 255 // 31
                    g = ((rgb565 >> 5) & 0x3F) * 255 // 63
                    b = (rgb565 & 0x1F) * 255 // 31
                    pixels[(y * self.width + x) * 4] = r
                    pixels[(y * self.width + x) * 4 + 1] = g
                    pixels[(y * self.width + x) * 4 + 2] = b
                    pixels[(y * self.width + x) * 4 + 3] = 255
        else:
            raise ValueError(f"Unsupported image profile: {self.profile}")

        return image_data

def dimage(x: int, y: int, img: image):
    """Draw entire image at specified coordinates"""
    _ctx_offscreen.putImageData(img.js_image_data, x, y)

def dsubimage(x: int, y: int, img: image,
             left: int, top: int, width: int, height: int):
    """Draw subregion of image"""
    _ctx_offscreen.putImageData(
        img.js_image_data,
        x, y,
        left, top,
        width, height
    )

# --- key

# Key event queue and state
_key_queue = asyncio.Queue() # deque()
_key_state = {
    'shift': False,
    'alpha': False,
    'last_key': None,
    'last_time': 0,
    'current_resolve': None
}

KEY_F1		= 0x91
KEY_F2		= 0x92
KEY_F3		= 0x93
KEY_F4		= 0x94
KEY_F5		= 0x95
KEY_F6		= 0x96

KEY_SHIFT	= 0x81
KEY_OPTN	= 0x82
KEY_VARS	= 0x83
KEY_MENU	= 0x84
KEY_LEFT	= 0x85
KEY_UP		= 0x86

KEY_ALPHA	= 0x71
KEY_SQUARE	= 0x72
KEY_POWER	= 0x73
KEY_EXIT	= 0x74
KEY_DOWN	= 0x75
KEY_RIGHT	= 0x76

KEY_XOT		= 0x61
KEY_LOG		= 0x62
KEY_LN		= 0x63
KEY_SIN		= 0x64
KEY_COS		= 0x65
KEY_TAN		= 0x66

KEY_FRAC	= 0x51
KEY_FD		= 0x52
KEY_LEFTP	= 0x53
KEY_RIGHTP	= 0x54
KEY_COMMA	= 0x55
KEY_ARROW	= 0x56

KEY_7		= 0x41
KEY_8		= 0x42
KEY_9		= 0x43
KEY_DEL		= 0x44
# AC/ON has keycode 0x07 instead of 0x45

KEY_4		= 0x31
KEY_5		= 0x32
KEY_6		= 0x33
KEY_MUL		= 0x34
KEY_DIV		= 0x35

KEY_1		= 0x21
KEY_2		= 0x22
KEY_3		= 0x23
KEY_ADD		= 0x24
KEY_SUB		= 0x25

KEY_0		= 0x11
KEY_DOT		= 0x12
KEY_EXP		= 0x13
KEY_NEG		= 0x14
KEY_EXE		= 0x15

# Why is AC/ON not 0x45? Because it must be on a row/column of its
#   own. It's used to power up the calculator; if it were in the middle
#   of the matrix one could use a ghosting effect to boot the calc.
KEY_ACON	= 0x07

# Virtual key codes
KEY_HELP	= 0x20 # fx-9860G Slim: 0x75 */
KEY_LIGHT	= 0x10 # fx-9860G Slim: 0x76 */

# Key codes for the CP-400
KEY_KBD		= 0xa1
KEY_X		= 0xa2
KEY_Y		= 0xa3
KEY_Z		= 0xa4
KEY_EQUALS	= 0xa5
KEY_CLEAR   = KEY_EXIT

# Key aliases (handle with care =D)
KEY_X2		= KEY_SQUARE
KEY_CARET	= KEY_POWER
KEY_SWITCH	= KEY_FD
KEY_LEFTPAR	= KEY_LEFTP
KEY_RIGHTPAR	= KEY_RIGHTP
KEY_STORE	= KEY_ARROW
KEY_TIMES	= KEY_MUL
KEY_PLUS	= KEY_ADD
KEY_MINUS	= KEY_SUB


KEYEV_NONE: int = 0
KEYEV_DOWN: int = 1
KEYEV_UP: int = 2
KEYEV_HOLD: int = 3
KEY_NONE = None

_key_map = {
    'Enter': KEY_EXE,
    'ArrowUp': KEY_UP,
    'ArrowDown': KEY_DOWN,
    'ArrowLeft': KEY_LEFT,
    'ArrowRight': KEY_RIGHT,
    'ShiftLeft': KEY_SHIFT,
    'KeyA': KEY_ALPHA
    # ...
}

def _create_key_promise():
    """Create a new promise that resolves on next key event"""
    promise = js.Promise.new(create_proxy(lambda resolve, reject: None))
    _key_state['current_promise'] = promise
    _key_state['current_resolve'] = resolve = lambda ev: None
    return promise

# Keyboard event handlers
def _handle_keydown(event):
    """Handle physical keyboard events"""

    print("_handle_keydown", event.code)

    key = _key_map.get(event.code, None)
    if not key:
        return

    print(key)

    # Update modifiers
    if key == 'KEY_SHIFT':
        _key_state['shift'] = True
    elif key == 'KEY_ALPHA':
        _key_state['alpha'] = True

    # Create event
    ev = KeyEvent(
        time=Date.now(),
        mod=False,
        shift=_key_state['shift'],
        alpha=_key_state['alpha'],
        type=KEYEV_DOWN,
        key=key # globals().get(key, KEY_NONE)
    )

    # Resolve pending promise
    # if _key_state['current_resolve']:
    #     _key_state['current_resolve'](ev)
    #     _key_state['current_resolve'] = None

    _key_queue.put_nowait(ev)
    _key_state['last_key'] = key
    _key_state['last_time'] = Date.now()

def _handle_keyup(event):
    
    print("_handle_keyup", event.code)

    key = _key_map.get(event.code, None)
    if not key:
        return
    
    print(key)

    # Update modifiers
    if key == 'KEY_SHIFT':
        _key_state['shift'] = False
    elif key == 'KEY_ALPHA':
        _key_state['alpha'] = False

    # Create event
    ev = KeyEvent(
        time=Date.now(),
        mod=False,
        shift=_key_state['shift'],
        alpha=_key_state['alpha'],
        type=KEYEV_UP,
        key=key # if string : globals()[key]
    )
    # _key_queue.append(ev)
    _key_queue.put_nowait(ev)
    # print(len(_key_queue))
    _key_state['last_key'] = None

# Register handlers
document.addEventListener("keydown", create_proxy(_handle_keydown))
document.addEventListener("keyup", create_proxy(_handle_keyup))

# Key event class
class KeyEvent:
    def __init__(self, time, mod, shift, alpha, type, key):
        self.time = time
        self.mod = mod
        self.shift = shift
        self.alpha = alpha
        self.type = type
        self.key = key

def _int_get_key():
    def check_queue(resolve):
        # Check queue or repeat events
        if _key_queue:
            item = _key_queue.popleft()
            resolve(item)
            return

        # Check for repeat key events
        now = Date.now()
        if (_key_state['last_key'] in ['KEY_UP', 'KEY_DOWN', 'KEY_LEFT', 'KEY_RIGHT'] and 
            now - _key_state['last_time'] > 400):
            ev = KeyEvent(
                time=now,
                mod=False,
                shift=_key_state['shift'],
                alpha=_key_state['alpha'],
                type=KEYEV_HOLD,
                key=globals().get(_key_state['last_key'], KEY_NONE)
            )
            _key_state['last_time'] = now
            resolve(ev)
            return

        # Schedule next check
        setTimeout(create_proxy(lambda: check_queue(resolve)), 100)

    return js.Promise.new(create_proxy(lambda resolve, reject: check_queue(resolve)))

def getkey():
    time.sleep(.5)
    print("OK")
    return True

async def _getkey():
    """Blocking key wait with repeat simulation"""
    while True:
        try:
            # Check for repeat
            if _key_state['last_key'] and (Date.now() - _key_state['last_time']) > 400:
                ev = KeyEvent(
                    time=Date.now(),
                    mod=False,
                    shift=_key_state['shift'],
                    alpha=_key_state['alpha'],
                    type=KEYEV_HOLD,
                    key=globals()[_key_state['last_key']]
                )
                _key_state['last_time'] = Date.now()
                return ev

            # Wait for new event with timeout
            ev = await asyncio.wait_for(_key_queue.get(), timeout=0.1)
            return ev
        except asyncio.TimeoutError:
            continue

def getkey_opt(options: int, timeout_ms: int | None):
    """Configurable key wait"""
    pass
    # try:
    #     return await asyncio.wait_for(getkey(), timeout=timeout_ms / 1000 if timeout_ms else None)
    # except asyncio.TimeoutError:
    #     return KeyEvent(time=Date.now(), mod=False, shift=False, alpha=False,
    #                    type=KEYEV_NONE, key=KEY_NONE)

def keycode_function(keycode: int):
    """Get F-key number from keycode"""
    f_keys = [KEY_F1, KEY_F2, KEY_F3, KEY_F4, KEY_F5, KEY_F6]
    try:
        return f_keys.index(keycode) + 1
    except ValueError:
        return -1

def keycode_digit(keycode: int):
    """Get digit from keycode"""
    digit_map = {
        KEY_0: 0, KEY_1: 1, KEY_2: 2, KEY_3: 3, KEY_4: 4,
        KEY_5: 5, KEY_6: 6, KEY_7: 7, KEY_8: 8, KEY_9: 9
    }
    return digit_map.get(keycode, -1)
