
#include <Arduino.h>

// ==========================================
// PART 4.3 - LDR DYNAMIC RESPONSE
// ==========================================

// Pins
const int ledPin = 3;
const int ldrPin = A0;
const int powerPin = A7;

// Sampling configuration
const unsigned long SAMPLE_PERIOD_US = 100; // 10 kHz
unsigned long lastSampleMicros = 0;

// LED pulsing configuration
const unsigned long CYCLE_TIME = 2000;

// Current duty cycle
uint16_t dutyCycle = 0;

// ==========================================
// LED CONTROL
// ==========================================

void setLED(int duty) {

    duty = constrain(duty, 0, 100);

    dutyCycle = duty;

    int pwmValue = map(duty, 0, 100, 0, 255);

    analogWrite(ledPin, pwmValue);
}

// ==========================================
// LED PULSING
// ==========================================

void updatePulsing() {

    unsigned long t = millis() % CYCLE_TIME;

    int duty;

    if (t < 1000) {

        // Increase brightness from 0% to 100%
        duty = map(t, 0, 1000, 0, 100);

    } else {

        // Decrease brightness from 100% to 0%
        duty = map(t, 1000, 2000, 100, 0);

    }

    setLED(duty);
}

// ==========================================
// SETUP
// ==========================================

void setup() {

    pinMode(powerPin, OUTPUT);
    digitalWrite(powerPin, HIGH);

    pinMode(ledPin, OUTPUT);

    analogReadResolution(10);

    Serial.begin(921600);

    setLED(0);
}

// ==========================================
// MAIN LOOP
// ==========================================

void loop() {

    // Update LED brightness
    updatePulsing();

    unsigned long now = micros();

    // Sample at approximately 10 kHz
    if ((unsigned long)(now - lastSampleMicros)
        >= SAMPLE_PERIOD_US) {

        lastSampleMicros = now;

        // Read LDR
        uint16_t adcValue = analogRead(ldrPin);

        // Create binary packet
        // First uint16_t: ADC value
        // Second uint16_t: LED duty cycle

        uint16_t packet[2];

        packet[0] = adcValue;
        packet[1] = dutyCycle;

        // Send 4 bytes
        Serial.write((uint8_t*)packet, sizeof(packet));
    }
}
