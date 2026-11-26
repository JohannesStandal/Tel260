import sys
import time
from collections import deque
import pygame
import serial

# --- Configuration ---
SERIAL_PORT = "COM5"  
BAUD_RATE = 115200  # Matches Arduino Serial.begin(115200)
WINDOW_SIZE_SEC = 10.0  # 10 seconds display history window for 10 Hz data

# --- Pygame Setup ---
pygame.init()
WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LDR Real-Time Stream (10 Hz Synced)")
clock = pygame.time.Clock()

MARGIN_LEFT, MARGIN_RIGHT = 70, 30
MARGIN_TOP, MARGIN_BOTTOM = 40, 50
PLOT_W = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
PLOT_H = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

BG_COLOR = (18, 22, 28)
GRID_COLOR = (38, 44, 54)
AXIS_COLOR = (100, 110, 125)
LINE_COLOR = (0, 220, 255)
TEXT_COLOR = (220, 225, 230)

font_small = pygame.font.SysFont("Consolas", 14)
font_large = pygame.font.SysFont("Consolas", 18, bold=True)

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.01)
    time.sleep(1.5)
except serial.SerialException as e:
    print(f"Error opening serial port {SERIAL_PORT}: {e}")
    sys.exit(1)

data_points = deque()  
start_time = time.time()
current_val = 0

def value_to_screen_y(val):
    val = max(0, min(1023, val))
    return (MARGIN_TOP + PLOT_H) - int((val / 1023.0) * PLOT_H)

def time_to_screen_x(t, current_t):
    t_start = current_t - WINDOW_SIZE_SEC
    ratio = (t - t_start) / WINDOW_SIZE_SEC
    return MARGIN_LEFT + int(ratio * PLOT_W)

running = True
while running:
    current_time = time.time() - start_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        ):
            running = False

    # Read incoming ASCII serial lines ("ADC_Val:XXXX")
    while ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("ADC_Val:"):
                parts = line.split(":")
                val = float(parts[1])  # Fixed: index [1] extracts the numeric value string
                sample_t = time.time() - start_time
                data_points.append((sample_t, val))
                current_val = int(val)
        except Exception:
            pass

    # Purge data older than window size
    while data_points and (current_time - data_points[0][0] > WINDOW_SIZE_SEC):
        data_points.popleft()

    # Render Background & Grid
    screen.fill(BG_COLOR)

    for adc_step in range(0, 1024, 256):
        y = value_to_screen_y(adc_step)
        pygame.draw.line(screen, GRID_COLOR, (MARGIN_LEFT, y), (WIDTH - MARGIN_RIGHT, y), 1)
        lbl = font_small.render(str(adc_step), True, AXIS_COLOR)
        screen.blit(lbl, (MARGIN_LEFT - 40, y - 7))

    for sec_offset in range(0, int(WINDOW_SIZE_SEC) + 1, 2):
        x = MARGIN_LEFT + int((sec_offset / WINDOW_SIZE_SEC) * PLOT_W)
        pygame.draw.line(screen, GRID_COLOR, (x, MARGIN_TOP), (x, MARGIN_TOP + PLOT_H), 1)
        lbl = font_small.render(f"-{int(WINDOW_SIZE_SEC) - sec_offset}s", True, AXIS_COLOR)
        screen.blit(lbl, (x - 15, MARGIN_TOP + PLOT_H + 8))

    pygame.draw.rect(screen, AXIS_COLOR, (MARGIN_LEFT, MARGIN_TOP, PLOT_W, PLOT_H), width=1)

    # Render Line Plot
    if len(data_points) >= 2:
        screen_points = [
            (time_to_screen_x(t, current_time), value_to_screen_y(v))
            for t, v in data_points
        ]
        pygame.draw.lines(screen, LINE_COLOR, False, screen_points, 2)
    
    # Status Overlays
    title_surface = font_large.render("LDR Real-Time Stream (10 Hz Synced)", True, TEXT_COLOR)
    val_surface = font_large.render(f"ADC: {current_val:4d} / 1023", True, LINE_COLOR)

    screen.blit(title_surface, (MARGIN_LEFT, 10))
    screen.blit(val_surface, (WIDTH - MARGIN_RIGHT - 180, 10))

    # . : l  o
    t0, v0 = data_points[-2]
    t1, v1 = data_points[-1]

    vMax = max(v0, vMax)
    vMin = min(v0 + 10, vMin)

    change = v1-v0

    rising = False
    riseStartTime = 0
    
    falling = False
    fallStartTime = 0
    
    if 0 < change and not rising:
        # Rise detected
        rising = True
        riseStartTime = t0

    elif change < 0 and not falling:
        # Fall detected
        falling = True
        fallStartTime = t0

    
    # Check if rise is finished
    if rising and v1 >= vMax * 0.95:
        riseTime = t1 - riseStartTime
        print("Rise time:", riseTime)
        rising = False

    # Check if fall is finished
    if falling and v1 <= vMin:
        fallTime = t1 - fallStartTime
        print("Fall time:", fallTime)
        falling = False

    pygame.display.flip()
    clock.tick(60)

# Clean up resources on exit
ser.close()
pygame.quit()
sys.exit()
