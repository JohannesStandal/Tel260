
import pandas as pd
import numpy as np
from scipy.signal import medfilt

# Parameters
THRESHOLD = 600
FS = 5000

UNIT_TIME_MS = 50
SAMPLES_PER_UNIT = 250


# Timing thresholds
LONG_PULSE_THRESHOLD = 125 # signal on for more than 100ms 

NEW_LETTER_THRESHOLD = 120 # signal off for more than 100ms is a new character 
NEW_WORD_THRESHOLD   = 200 # signal off for more than 400ms is a new word


# Morse code dictionary
MORSE = {
    ".-": "A", 
    "-...": "B", 
    "-.-.": "C",
    "-..": "D", 
    ".": "E", 
    "..-.": "F",
    "--.": "G", 
    "....": "H", 
    "..": "I",
    ".---": "J", 
    "-.-": "K", 
    ".-..": "L",
    "--": "M",
    "-.": "N",
    "---": "O",
    ".--.": "P", 
    "--.-": "Q", 
    ".-.": "R",
    "...": "S", 
    "-": "T", 
    "..-": "U",
    "...-": "V", 
    ".--": "W", 
    "-..-": "X",
    "-.--": "Y", 
    "--..": "Z",

    # Numbers
    "-----": "0", 
    ".----": "1", 
    "..---": "2",
    "...--": "3", 
    "....-": "4", 
    ".....": "5",
    "-....": "6", 
    "--...": "7", 
    "---..": "8",
    "----.": "9",

    # Special chars
    "--..--": ",",
    ".-.-.-": ".",
    ".----.": "'",
}

# Filter 
def filter(array):
    for i in range(len(array)):
        v0 = array[i]
        v1 = array[i+1]

        avg = (v0 + v1) / 2

        array[i] = avg

    return array

# Load data
df = pd.read_csv("LDR_5.1_data.csv")

# Apply median filter
adc = df["ADC"].to_numpy()
filtered = medfilt(adc, kernel_size=51)

# Binary classification
binary = filtered >= THRESHOLD

# Find transitions
transitions = np.diff(binary.astype(int))
change_indices = np.where(transitions != 0)[0] + 1

# Construct intervals
boundaries = np.concatenate(([0], change_indices, [len(binary)]))

runs = []
for start, end in zip(boundaries[:-1], boundaries[1:]):
    state = binary[start]
    duration = end - start

    runs.append({
        "state": "ON" if state else "OFF",
        "start_sample": start,
        "end_sample": end,
        "duration_samples": duration,
        "duration_ms": duration / FS * 1000,
        "units": duration / SAMPLES_PER_UNIT
    })

runs_df = pd.DataFrame(runs)
runs = np.array(runs)

# Find the start and end of the quote
df_off = runs_df[runs_df["state"] == "OFF"]
df_off = df_off.sort_values(by="duration_ms", ascending=False)

top_2_indices = df_off["duration_ms"].nlargest(2).index
start = 0 # min(top_2_indices)
stop  = max(top_2_indices)

runs = runs[start:stop]


letters = []
current_letter = ""

# Loop over message data
for run in runs:
    duration = run["duration_ms"]

    # If the signal is high it is either a dot or a dash
    if run["state"] == "ON":

        # Short pulse
        if duration < LONG_PULSE_THRESHOLD:
            current_letter += "."

        # Long pulse  
        else:
            current_letter += "-"

    # Signal is low
    else:
        # 
        if NEW_LETTER_THRESHOLD <= duration :
            
            letters.append(current_letter)
            current_letter = ""

            if duration >= NEW_WORD_THRESHOLD:
                letters.append(" ")

# Handle final letter
if current_letter:
    letters.append(current_letter)

# Decode
decoded = []

for letter in letters:
    if letter == " ":
        decoded.append(" ")
    else:
        decoded.append(MORSE.get(letter, "?"))

message = "".join(decoded)

print(message)

