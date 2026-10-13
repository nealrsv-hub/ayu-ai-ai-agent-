// Add this helper to your EXISTING working ESP32-S3 sketch.
// This is not standalone firmware. It assigns no GPIO pins and controls no motor.
// In setup(): Serial.begin(115200);
// Call with your measured values, roughly twice per second.
// Pass NAN on a failed reading. Keep the DHT11 read interval >= 2 seconds.
#pragma once
#include <Arduino.h>
#include <math.h>

inline void printJsonNumber(float value) {
  if (isfinite(value)) Serial.print(value, 2);
  else Serial.print("null");
}

inline void sendTelemetry(float distanceCm, float temperatureC, float humidityPct,
                           const char* lightState = nullptr, bool ledOn = false) {
  Serial.print("{\"distance_cm\":");
  // A timed-out ultrasonic reading must be null, not 0 = standing.
  printJsonNumber(distanceCm > 0 ? distanceCm : NAN);
  Serial.print(",\"temperature_c\":");
  printJsonNumber(temperatureC);
  Serial.print(",\"humidity_pct\":");
  printJsonNumber(humidityPct);
  if (lightState != nullptr) {
    Serial.print(",\"light_state\":\"");
    Serial.print(lightState);
    Serial.print("\"");
  }
  Serial.print(",\"led_on\":");
  Serial.print(ledOn ? "true" : "false");
  Serial.println("}");
}
