// ***************************************************************************************************
// Title:         TEL260_Ass2_Pt1_Light_Sensor_Student_Demo
// Author:        Alex Mason
// Date:          09.11.2026
// Board:         Arduino Nano R4 (Renesas RA4M1)
// Description:   Demonstration of LDR sensor. Toggles LED on and off at a fixed interval, with 
//                synchronised 10 Hz ADC sampling, TFT screen updates, and ASCII string serial output.
//               
// CHANGELOG:
// 09.11.2026:    First revision. 
// ***************************************************************************************************

// Libraries
#include <Arduino_GFX_Library.h>

// Set to true to enable TFT hardware and live sweep plotting 
// Set to false for max throughput over serial interface. Note
// at 10 Hz ADC, this will not make a performance difference!
const bool enableTFT = true;

// TFT Display Pin Definitions
#define TFT_CS   10
#define TFT_DC   8
#define TFT_RST  7
#define TFT_PWR  A2

// Color Definitions (16-bit RGB565)
#define BLACK   0x0000
#define WHITE   0xFFFF
#define YELLOW  0xFFE0
#define GREEN   0x07E0
#define CYAN    0x07FF
#define RED     0xF800
#define GRAY    0x4208

// Display Constructor (ILI9488 18-bit SPI)
Arduino_DataBus *bus = new Arduino_HWSPI(TFT_DC, TFT_CS);
Arduino_GFX *tft = new Arduino_ILI9488_18bit(bus, TFT_RST, 3 /* rotation */, false /* IPS */);

const int ledPin = 3;       
const int ldrPin = A0;      
const int powerPin = A7;    

// --- Unified 10 Hz Timing Configuration ---
const int TARGET_RATE_HZ = 1000;  
const unsigned long intervalMs = 1000 / TARGET_RATE_HZ; // Exactly 100 ms per tick
unsigned long lastTickMillis = 0;

const unsigned long ledIntervalMs = 500;
unsigned long lastLedToggleMillis = 0;
bool ledState = LOW;

// Chart Configuration (600 sweep points)
#define CHART_POINTS 600 
float chartRawHistory[CHART_POINTS];
int chartHead = 0;

// Dynamic Chart Layout Dimensions
int chartX = 45;
int chartY = 58;
int chartWidth = 425;
int chartHeight = 240;

uint16_t screenWidth = 0;
uint16_t screenHeight = 0;

const float adcMin = 0.0;
const float adcMax = 1023.0;
const int gridDivisions = 4;

int currentLDRValue = 0;

// Function Declarations
void printText(const String &text, int x, int y, uint16_t color, uint8_t size, bool centerText = false);
void drawChartFrame();
void updateSweepPlot();

// ***************************************************************************************************
// SETUP
// ***************************************************************************************************

void setup() 
{
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, ledState);
  
  pinMode(powerPin, OUTPUT);
  digitalWrite(powerPin, HIGH);

  Serial.begin(115200); 
  while (!Serial && millis() < 3000);

  // 1. Initialise display if enabled
  if (enableTFT)  {
    pinMode(TFT_PWR, OUTPUT);
    digitalWrite(TFT_PWR, LOW); // Power on backlight
    delay(500);

    if (!tft->begin(20000000))  
    {
      Serial.println("TFT Initialisation failed!");
      while (1);
    }

    tft->fillScreen(BLACK);

    screenWidth = tft->width();   // 480 in Landscape mode
    screenHeight = tft->height(); // 320 in Landscape mode

    chartWidth = screenWidth - chartX - 10;
    chartHeight = screenHeight - chartY - 20;

    printText("LDR Sensor Waveform (10Hz Synced)", 0, 6, WHITE, 2, true);
    printText("Raw:", 10, 28, CYAN, 2, false);
    drawChartFrame();
  } 
  else 
  {
    // Powered on, but displaying "TFT Disabled" message
    pinMode(TFT_PWR, OUTPUT);
    digitalWrite(TFT_PWR, LOW); // Power on backlight
    delay(500);

    if (!tft->begin(20000000))  
    {
      Serial.println("TFT Initialisation failed!");
      while (1);
    }

    tft->fillScreen(BLACK);
    
    // Display status text centered on screen
    tft->setTextSize(3);
    tft->setTextColor(RED, BLACK);
    tft->setCursor(110, 140);
    tft->print("TFT Disabled");

    tft->setTextSize(1);
    tft->setTextColor(WHITE, BLACK);
    tft->setCursor(120, 180);
    tft->print("Running 10Hz Serial/ADC Mode");

    Serial.println("TFT disabled");
  }

  // 2. Buffer Seeding
  int initialADC = analogRead(ldrPin);
  currentLDRValue = initialADC;
  
  for (int i = 0; i < CHART_POINTS; i++) 
  {
    chartRawHistory[i] = (float)initialADC;
  }

  unsigned long nowMillis = millis();
  lastTickMillis = nowMillis;
  lastLedToggleMillis = nowMillis;
}


// ***************************************************************************************************
// LOOP
// ***************************************************************************************************

void loop() 
{
  unsigned long currentMillis = millis();

  // 1. Unified 10 Hz Synchronized Tick (ADC Sample + TFT Update + String Serial Output)
  if (currentMillis - lastTickMillis >= intervalMs) 
  {
    lastTickMillis += intervalMs;

    // Sample the ADC
    currentLDRValue = analogRead(ldrPin);

    // Output human-readable string over Serial
    Serial.print("ADC_Val:");
    Serial.println(currentLDRValue);

    // Update TFT Screen & Sweep Refresh (if enabled)
    if (enableTFT)  
    {
      chartRawHistory[chartHead] = (float)currentLDRValue;

      printText(String(currentLDRValue) + "    ", 65, 28, CYAN, 2, false);

      updateSweepPlot();

      chartHead = (chartHead + 1) % CHART_POINTS;
    }
  }

  // 2. LED Toggle (500ms)
  if (currentMillis - lastLedToggleMillis >= ledIntervalMs) 
  {
    lastLedToggleMillis += ledIntervalMs;
    ledState = !ledState;
    digitalWrite(ledPin, ledState);
  }
}

// ***************************************************************************************************
// DRAWING ROUTINES
// ***************************************************************************************************

void drawChartFrame()  
{
  if (!enableTFT) return;

  tft->drawRect(chartX, chartY, chartWidth, chartHeight, WHITE);
  tft->setTextSize(1);

  for (int i = 0; i <= gridDivisions; i++)  {
    int yVal = chartY + (chartHeight * i / gridDivisions);
    float adcVal = adcMax - (i * (adcMax - adcMin) / (float)gridDivisions);

    tft->drawFastHLine(chartX + 1, yVal, chartWidth - 2, GRAY);
    tft->setCursor(chartX - 38, yVal - 3);
    tft->setTextColor(WHITE, BLACK);
    tft->print((int)adcVal);
  }

  printText("600 Points Live Sweep Plot", chartX + (chartWidth / 2) - 80, chartY + chartHeight + 6, WHITE, 1, false);
}

void updateSweepPlot()  
{
  if (!enableTFT) return;

  int prevHead = (chartHead == 0) ? (CHART_POINTS - 1) : (chartHead - 1);

  int x1 = chartX + 1 + map(prevHead, 0, CHART_POINTS - 1, 0, chartWidth - 3);
  int x2 = chartX + 1 + map(chartHead, 0, CHART_POINTS - 1, 0, chartWidth - 3);

  int eraseW = 8;
  int eraseX = x2;
  if (eraseX + eraseW > chartX + chartWidth - 1) { eraseW = (chartX + chartWidth - 1) - eraseX; }
  if (eraseW > 0)  {
    tft->fillRect(eraseX, chartY + 1, eraseW, chartHeight - 2, BLACK);

    for (int i = 1; i < gridDivisions; i++)  
    {
      int yVal = chartY + (chartHeight * i / gridDivisions);
      tft->drawFastHLine(eraseX, yVal, eraseW, GRAY);
    }
  }

  if (chartHead == 0) { return; }

  int yRaw1 = chartY + chartHeight - map((long)constrain(chartRawHistory[prevHead], adcMin, adcMax), (long)adcMin, (long)adcMax, 2, chartHeight - 2);
  int yRaw2 = chartY + chartHeight - map((long)constrain(chartRawHistory[chartHead], adcMin, adcMax), (long)adcMin, (long)adcMax, 2, chartHeight - 2);

  tft->drawLine(x1, yRaw1, x2, yRaw2, CYAN);

  if (x2 + 1 < chartX + chartWidth - 1) 
  {
    tft->drawFastVLine(x2 + 1, chartY + 1, chartHeight - 2, WHITE);
  }
}

void printText(const String &text, int x, int y, uint16_t color, uint8_t size, bool centerText)  
{
  if (!enableTFT) { return; }

  tft->setTextSize(size);
  tft->setTextColor(color, BLACK); 

  int targetX = x;
  if (centerText)  
  {
    int16_t x1, y1;
    uint16_t text_width, text_height;
    tft->getTextBounds(text, 0, y, &x1, &y1, &text_width, &text_height);

    targetX = (screenWidth - text_width) / 2;
    if (targetX < 0) { targetX = 0; } 
  }

  tft->setCursor(targetX, y);
  tft->print(text);
}
