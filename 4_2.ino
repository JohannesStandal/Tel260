
#include <Arduino.h>

// ==========================================
// PART 4.2 - LDR SATURATION EXPERIMENT
// ==========================================

// Pins
const int ledPin = 3;
const int ldrPin = A0;
const int powerPin = A7;    


// Sampling configuration
const unsigned long SAMPLE_PERIOD_US = 100; // 10 kHz

// Duty cycle sweep configuration
const unsigned long STEP_DURATION_MS = 3000; // 3 seconds
const int DUTY_STEP = 5;                      // 5% increments
const int NUMBER_OF_STEPS = 21;               // 0% to 100%

// Sampling timer
unsigned long lastSampleMicros = 0;

// Current LED duty cycle
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
// DUTY CYCLE SWEEP
// ==========================================

void updateDutySweep() {

    // Determine current step
    unsigned long step = (millis() / STEP_DURATION_MS) % NUMBER_OF_STEPS;

    // Convert step to duty cycle
    int duty = step * DUTY_STEP;

    setLED(duty);
}

// ==========================================
// SETUP
// ==========================================

void setup() {

    pinMode(powerPin, OUTPUT);
    digitalWrite(powerPin, HIGH);

    pinMode(ledPin, OUTPUT);

    
    // Start serial communication
    Serial.begin(921600);

    // Start with LED off
    setLED(0);
}

// ==========================================
// MAIN LOOP
// ==========================================

void loop() {

    // Update LED brightness
    updateDutySweep();

    // Check if it is time to sample
    unsigned long now = micros();

    if ((unsigned long)(now - lastSampleMicros) >= SAMPLE_PERIOD_US) {

        lastSampleMicros = now;

        // Read LDR
        uint16_t adcValue = analogRead(ldrPin);

        // Create binary packet:
        // First uint16_t = ADC value
        // Second uint16_t = LED duty cycle
        uint16_t packet[2];

        packet[0] = adcValue;
        packet[1] = dutyCycle;

        // Send 4 bytes
        Serial.write((uint8_t*)packet, sizeof(packet));
        // Serial.println(adcValue);
        // Serial.println(dutyCycle);
    }
}
