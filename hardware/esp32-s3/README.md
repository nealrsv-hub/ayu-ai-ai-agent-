# ESP32-S3 telemetry integration

This directory contains a telemetry helper for an existing Arduino sketch. It does not include complete firmware or measured hardware-validation results.

## Recorded project pin map

| Function | ESP32-S3 GPIO |
|---|---:|
| HC-SR04 TRIG | 4 |
| HC-SR04 ECHO | 5, through the recorded 10 kΩ / 15 kΩ divider |
| DHT11 DATA | 6 |
| Digital LDR DO | 7 |
| OLED SDA | 8 |
| OLED SCL/SCK | 9 |
| LED | 10 |

The recorded OLED address is `0x3C`. Check the actual board, wiring, and input levels before using this map; the helper itself does not configure or validate them.

## Serial contract

The backend expects newline-delimited JSON over USB serial at 115200 baud:

```json
{"distance_cm":82.4,"temperature_c":27.1,"humidity_pct":58.0,"light_state":"bright","led_on":false}
```

Use JSON `null` for failed numeric measurements. `firmware/telemetry_snippet.h` emits this format when called from a working sketch.

Telemetry is one-way. The Python LED decision does not send a command to this firmware, and a reported LED field is not an acknowledgement of a Python action.

`backend/data/calibration.json` starts with empty posture bands. Measure the actual sensor geometry before entering standing, sitting, and lying ranges. Demo ranges are not a substitute for calibration.
