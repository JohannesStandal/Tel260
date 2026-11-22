// ***************************************************************************************************
// Title:        TEL260_02_LM35CZ
// Author:       Alex Mason
// Date:         25.10.2026
// Board:        Arduino Nano R4 (Renesas RA4M1)
// Description:  Reads LM35CZ temperature sensor on A0. Displays raw ADC counts and current temp.
//               There is a companion version TEL260_02_LM35CZ_STUDENT which does not have the
//               transfer function for the sensor in "readLM35CZ()" prepopulated.
//               Serial data format: "ADC: "<rawADC>"\tCurrent: "<currentTemp>" °C"
// CHANGELOG:
// 25.10.2026:   First revision.
// 28.10.2026:   In response to some inclass confusion, updated code here to match with lecture notes
//               in regard to terminology. Also, verified the functionality of AR_INTERNAL vs using
//               USB VCC as VREF. The important issue is that the VREF value must be updated when
//               switching.
// 15.11.2026:   Adjusted min/max value that would be output to the display to 0-60degC and rotated
//               the display for better visibility.
// 17.11.2026:   Removed transfer function and any filtering: by default the code outputs only the
//               ADC counts value and currentTemp = 1. It is possible to set "enableTFT" to turn  
//               deactivate the screen.
// ***************************************************************************************************

// Libraries
#include <Arduino_GFX_Library.h>

// TFT Display Pin Definitions & Enable Flag
#define TFT_CS   10
#define TFT_DC   8
#define TFT_RST  7
#define TFT_PWR  A2
bool enableTFT = true;

// Color Definitions (16-bit RGB565)
#define BLACK   0x0000
#define WHITE   0xFFFF
#define YELLOW  0xFFE0
#define GREEN   0x07E0
#define CYAN    0x07FF
#define RED     0xF800
#define GRAY    0x4208

// Display Constructor (ILI9488 18-bit SPI)
// Rotation: 0 & 2 = Portrait (320x480), 1 & 3 = Landscape (480x320)
Arduino_DataBus *bus = new Arduino_HWSPI(TFT_DC, TFT_CS);
Arduino_GFX *tft = new Arduino_ILI9488_18bit(bus, TFT_RST, 3 /* rotation */, false /* IPS */);

// Sensor Pin Definitions 
const int lm35czPin = A0;
const int sensorPowerPin = A7;
const int sensorPowerUpDelay = 200;
bool powerDownSensor = true;

// Sensor Measurements
int ADCReading = 0;
float currentTemp = 0.0;

// Chart Configuration (5 minutes = 300 points @ 1 sec sampling)
#define CHART_POINTS 300 
float chartCurrentHistory[CHART_POINTS];
int chartHead = 0;

// Dynamic Chart Layout Dimensions (updated in setup based on rotation)
int chartX = 35;
int chartY = 90;
int chartWidth = 435;
int chartHeight = 205;

uint16_t screenWidth = 0;
uint16_t screenHeight = 0;

// Temperature Y-axis scale range (°C)
const float tempMin = 0.0;
const float tempMax = 60.0;
const int gridDivisions = 5;
 
int res = 14;

// Function Declarations
void printText(const String &text, int x, int y, uint16_t color, uint8_t size, bool centerText = false);
void readLM35CZ();
void drawChartFrame();
void updateSweepPlot();

// ***************************************************************************************************
// SETUP
// ***************************************************************************************************

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 3000);  

  // Set ADC resolution. Ensure that any transfer function uses the correct number of bits (2^n).
  // See https://docs.arduino.cc/language-reference/en/functions/analog-io/analogReadResolution/ for 
  // more information regarding analog read resolution.
  //analogReadResolution(8);
  //analogReadResolution(10);
  //analogReadResolution(12);
  analogReadResolution(14);
  //analogReadResolution(16);
  //analogReadResolution(res);

  // Select reference voltage
  // See https://docs.arduino.cc/language-reference/en/functions/analog-io/analogReference/ for more
  // information regarding the analog reference value.
  analogReference(AR_DEFAULT);
  // analogReference(AR_INTERNAL);
  //analogReference(AR_INTERNAL_1_5V);
  //analogReference(AR_INTERNAL_2_0V);
  //analogReference(AR_INTERNAL_2_5V);
 
  // 1. Initialize Display
  pinMode(TFT_PWR, OUTPUT);
  digitalWrite(TFT_PWR, LOW);
  delay(500);

  if (!tft->begin(20000000)) {
    Serial.println("TFT Initialization failed!");
    while (1);
  }

  tft->fillScreen(BLACK);

  // Query actual dimensions after rotation (480x320 in landscape)
  screenWidth = tft->width();
  screenHeight = tft->height();

  // 2. Power on LM35CZ sensor, but only if the power saving
  // option is not enabled.
  pinMode(sensorPowerPin, OUTPUT);
  if (powerDownSensor == false) {
    digitalWrite(sensorPowerPin, HIGH);
    delay(sensorPowerUpDelay);
  }

  // 3. Configure Display UI (or show disabled notice)
  if (enableTFT) {
    // Dynamically scale chart to fill remainder of screen width and height
    chartWidth = screenWidth - chartX - 10;
    chartHeight = screenHeight - chartY - 25;

    // Initialize Chart Buffer
    for (int i = 0; i < CHART_POINTS; i++) {
      chartCurrentHistory[i] = 0.0;
    }

    // Draw Header & Static UI Labels
    printText("TEL260: LM35CZ", 0, 8, CYAN, 2, true);

    printText("Counts:", 10, 35, WHITE, 2, false);
    printText("Current:", 10, 60, WHITE, 2, false);

    // Legend (shifted right for 480px landscape layout)
    printText("- Inst", 370, 60, YELLOW, 2, false);

    drawChartFrame();
  } else {
    printText("TFT disabled", 0, (screenHeight / 2) - 8, WHITE, 2, true);
  }

  // Initial dummy read to settle ADC
  readLM35CZ();
}

// ***************************************************************************************************
// LOOP
// ***************************************************************************************************

void loop() {
  readLM35CZ();

  // Print values to Serial Monitor
  Serial.print("ADC: ");
  Serial.print(ADCReading);
  Serial.print("\tCurrent: ");
  Serial.print(currentTemp, 1);
  Serial.println(" °C");  

  if (enableTFT) {
    // Store reading
    chartCurrentHistory[chartHead] = currentTemp;

    // Display raw counts and calculated temperature
    printText(String(ADCReading) + "    ", 110, 35, CYAN, 2, false);
    printText(String(currentTemp, 1) + " C   ", 110, 60, YELLOW, 2, false);

    // Perform ultra-fast incremental sweep update
    updateSweepPlot();

    // Advance cursor
    chartHead = (chartHead + 1) % CHART_POINTS;
  }

  if (powerDownSensor == false) { delay(1000); }
  else { delay(1000 - sensorPowerUpDelay); }
}

// ***************************************************************************************************
// SENSOR ROUTINES
// ***************************************************************************************************

void readLM35CZ() {
  // Turn the sensor back on if necessary
  if (powerDownSensor == true) {
    digitalWrite(sensorPowerPin, HIGH);
    delay(sensorPowerUpDelay);

  }

  // Collect the raw ADC reading
  ADCReading = analogRead(lm35czPin);

  // Turn sensor off if necessary
  if (powerDownSensor == true) { digitalWrite(sensorPowerPin, LOW); }

  // Transfer function placeholder
  const float Vinput = (ADCReading / 16383.0) * AR_DEFAULT;
  
  // Convert voltage to temperature
  currentTemp = Vinput / 0.010;
  
}

// ***************************************************************************************************
// DRAWING ROUTINES
// ***************************************************************************************************

void drawChartFrame() {
  tft->drawRect(chartX, chartY, chartWidth, chartHeight, WHITE);
  tft->setTextSize(1);
  tft->setTextColor(GRAY);

  for (int i = 0; i <= gridDivisions; i++) {
    int yVal = chartY + (chartHeight * i / gridDivisions);
    float tempVal = tempMax - (i * (tempMax - tempMin) / (float)gridDivisions);

    tft->drawFastHLine(chartX + 1, yVal, chartWidth - 2, GRAY);
    tft->setCursor(chartX - 28, yVal - 3);
    tft->print((int)tempVal);
    tft->print("C");
  }

  printText("5 Minutes Sweep", chartX + (chartWidth / 2) - 45, chartY + chartHeight + 8, WHITE, 1, false);
}

void updateSweepPlot() {
  int prevHead = (chartHead == 0) ? (CHART_POINTS - 1) : (chartHead - 1);

  // Map 300 data points across the chart width
  int x1 = chartX + 1 + map(prevHead, 0, CHART_POINTS - 1, 0, chartWidth - 3);
  int x2 = chartX + 1 + map(chartHead, 0, CHART_POINTS - 1, 0, chartWidth - 3);

  // 1. Erase thin 8-pixel slice starting right after x1 so the previous cursor is always cleared
  int eraseW = 8;
  int eraseX = (chartHead == 0) ? (chartX + 1) : (x1 + 1);
  if (eraseX + eraseW > chartX + chartWidth - 1) {
    eraseW = (chartX + chartWidth - 1) - eraseX;
  }
  if (eraseW > 0) {
    tft->fillRect(eraseX, chartY + 1, eraseW, chartHeight - 2, BLACK);

    // 2. Redraw grid lines in erased slice
    for (int i = 1; i < gridDivisions; i++) {
      int yVal = chartY + (chartHeight * i / gridDivisions);
      tft->drawFastHLine(eraseX, yVal, eraseW, GRAY);
    }
  }

  // Skip line drawing across wrap-around boundary (from right edge back to left)
  if (chartHead == 0) return;

  // 3. Map temperature values to Y coordinates
  int yCurr1 = chartY + chartHeight - map(constrain(chartCurrentHistory[prevHead], tempMin, tempMax) * 10, tempMin * 10, tempMax * 10, 2, chartHeight - 2);
  int yCurr2 = chartY + chartHeight - map(constrain(chartCurrentHistory[chartHead], tempMin, tempMax) * 10, tempMin * 10, tempMax * 10, 2, chartHeight - 2);

  // 4. Draw new single line segment
  tft->drawLine(x1, yCurr1, x2, yCurr2, YELLOW);

  // 5. Draw vertical cursor line showing active write position
  // (Comment out this block if you prefer no leading white cursor line at all)
  if (x2 + 1 < chartX + chartWidth - 1) {
    tft->drawFastVLine(x2 + 1, chartY + 1, chartHeight - 2, WHITE);
  }
}

void printText(const String &text, int x, int y, uint16_t color, uint8_t size, bool centerText) {
  tft->setTextSize(size);
  tft->setTextColor(color, BLACK); 

  int targetX = x;
  if (centerText) {
    int16_t x1, y1;
    uint16_t text_width, text_height;
    tft->getTextBounds(text, 0, y, &x1, &y1, &text_width, &text_height);

    targetX = (screenWidth - text_width) / 2;
    if (targetX < 0) targetX = 0; 
  }

  tft->setCursor(targetX, y);
  tft->print(text);
}
