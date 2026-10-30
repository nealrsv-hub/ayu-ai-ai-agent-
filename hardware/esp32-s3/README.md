# ESP32-S3 hardware integration

The current repository includes the validated serial telemetry helper and integration notes. It does not claim a complete production firmware image.

## Confirmed room-monitoring pin map

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

## Added dual-axis solar tracker

The updated integrated prototype adds a small photovoltaic panel mounted on two servo-controlled axes. Two light sensors are used to compare incident light and steer the panel toward the brighter direction.

### Solar-tracker hardware

- Small photovoltaic solar panel
- 2 LDR/light sensors for light-intensity comparison
- 2 servo motors: one horizontal/pan axis and one vertical/tilt axis
- Two-axis mounting bracket / panel frame
- Regulated servo supply sized for the selected servos
- Common ground between ESP32-S3, sensor circuit and servo supply

### GPIO status

The review design does **not** define final GPIO assignments for the two solar light sensors or two servos. Do not treat any guessed pin map as final. Assign pins only after checking the exact ESP32-S3 board, ADC-capable pins, PWM compatibility, and conflicts with the confirmed room-monitoring pins above.

### Control principle

A safe first implementation should use a simple local closed-loop controller:

1. Read the two solar light sensors.
2. Calculate the difference between their readings.
3. If the difference is smaller than a calibrated deadband, hold position.
4. If one side is brighter, move the relevant servo by a small step toward that side.
5. Clamp both servo commands to tested mechanical limits.
6. Repeat slowly enough to avoid servo hunting and unnecessary power consumption.

For a true two-axis tracker, the final mechanical/sensor arrangement must provide independent information for horizontal and vertical error. If only two LDRs are physically installed, verify that the mechanism can actually resolve both axes; otherwise use a four-quadrant light-sensing arrangement in a later revision.

### Power rules

- Do not power a servo motor from the ESP32-S3 3.3 V pin.
- Prefer a separate regulated servo supply appropriate for the selected servo voltage/current.
- Tie the servo-supply ground to ESP32-S3 ground.
- Add local decoupling near the servo supply and verify brownout/reset behavior under motion.
- Treat the PV panel as a tracking/renewable-energy demonstration unless a separate validated charging, battery-management and power-path circuit is added.

## Telemetry contract

The Python backend expects newline-delimited JSON over USB serial at 115200 baud, for example:

```json
{"distance_cm":82.4,"temperature_c":27.1,"humidity_pct":58.0,"light_state":"bright","led_on":false}
```

Use JSON `null` for failed numeric measurements. Do not send medical conclusions from firmware.

`firmware/telemetry_snippet.h` can be included in the working Arduino sketch to emit this contract. The current backend does not yet require solar-tracker telemetry fields, so the solar control loop can remain local during the first hardware demonstration.

## Important

`backend/data/calibration.json` deliberately starts with empty posture bands. Measure your actual ceiling/model geometry before entering standing/sitting/lying ranges; do not copy demo thresholds into a real installation.

See `../../docs/SOLAR_TRACKER.md` for the implementation and validation checklist for the new solar subsystem.
