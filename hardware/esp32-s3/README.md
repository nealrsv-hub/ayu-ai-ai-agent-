# ESP32-S3 hardware integration

The current repository includes the validated serial telemetry helper, not a claim of a complete production firmware image.

## Confirmed project pin map

| Function | ESP32-S3 GPIO |
|---|---:|
| HC-SR04 TRIG | 4 |
| HC-SR04 ECHO | 5, through the existing 10 kΩ / 15 kΩ divider |
| DHT11 DATA | 6 |
| Digital LDR DO | 7 |
| OLED SDA | 8 |
| OLED SCL/SCK | 9 |
| LED | 10 |

OLED address used during the hackathon was `0x3C`.

## Telemetry contract

The Python backend expects newline-delimited JSON over USB serial at 115200 baud, for example:

```json
{"distance_cm":82.4,"temperature_c":27.1,"humidity_pct":58.0,"light_state":"bright","led_on":false}
```

Use JSON `null` for failed numeric measurements. Do not send medical conclusions from firmware.

`firmware/telemetry_snippet.h` can be included in the working Arduino sketch to emit this contract.

## Important

`backend/data/calibration.json` deliberately starts with empty posture bands. Measure your actual ceiling/model geometry before entering standing/sitting/lying ranges; do not copy demo thresholds into a real installation.
