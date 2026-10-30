# Dual-axis solar tracker — integration plan

This document records the solar-tracking extension shown in the updated AyuSaarthi AI hackathon review material.

## 1. Purpose

The solar subsystem demonstrates renewable-energy awareness by automatically orienting a small photovoltaic panel toward stronger incident light while the main AyuSaarthi prototype continues room sensing, local automation, caregiver monitoring and voice/AI assistance.

This is currently a **tracking demonstration**, not a validated solar charger or primary power source for the system.

## 2. Hardware shown in the updated concept

- ESP32-S3 controller
- Small photovoltaic panel
- 2 LDR/light sensors used for light-intensity comparison
- 2 servo motors
  - horizontal/pan axis
  - vertical/tilt axis
- Mechanical two-axis panel mount
- Regulated power for controller/sensors and a suitable servo supply
- Common electrical ground

The existing room-monitoring hardware remains HC-SR04, DHT11, digital LDR, OLED and LED, with optional local actuator demonstrations such as fan/buzzer depending on the build.

## 3. Engineering issue to validate before calling it fully dual-axis

The review concept shows **two** light sensors and **two** servo axes. Two sensor readings provide a single differential light error unless the mechanical arrangement or sensing method creates independent horizontal and vertical information.

Before the final build, validate one of these approaches:

1. **Keep two LDRs** and use them for one active tracking axis while the second axis follows a separate rule/schedule; or
2. **Upgrade to four LDRs** arranged as a quadrant around a small shade/cross so left-right and top-bottom errors can be calculated independently.

For a robust dual-axis prototype, option 2 is the cleaner architecture.

## 4. Recommended local control loop

The tracking loop should run entirely on the ESP32-S3.

### Single-axis differential logic

```text
error = left_light - right_light

if abs(error) <= deadband:
    hold servo
elif error > 0:
    move a small step toward left
else:
    move a small step toward right
```

For a four-LDR revision, compute two errors:

```text
horizontal_error = average(left pair) - average(right pair)
vertical_error   = average(top pair)  - average(bottom pair)
```

Then update pan and tilt independently.

## 5. Control requirements

- Use a calibrated deadband so the servos do not continuously hunt around equal light.
- Move only a few degrees per update.
- Add a delay or rate limit between moves.
- Clamp pan/tilt commands to tested mechanical limits.
- On invalid sensor data, hold the last safe position rather than moving blindly.
- Consider a low-light threshold that parks/disables tracking when meaningful direction cannot be determined.
- Keep all servo decisions deterministic and local; do not depend on an LLM or network request.

## 6. Electrical integration

### Servo power

Do not power the servos from the ESP32-S3 3.3 V output. Use a regulated supply appropriate for the selected servos, with enough current for startup/stall transients.

Connect grounds together:

```text
ESP32-S3 GND --------+
LDR circuit GND -----+---- common ground
Servo supply GND ----+
```

Add local bulk capacitance near the servo supply and check that movement does not reset or brown out the ESP32-S3.

### Solar panel

The panel may be mechanically tracked without being electrically connected to the AyuSaarthi power rail. If the project later uses the panel to charge a battery or power electronics, add a separate validated charging/power-path design suitable for the panel and battery chemistry.

Do not connect an uncontrolled panel output directly to the ESP32-S3 or battery.

## 7. GPIO assignment

The updated review material does not define the final tracker pins. Keep them configurable until the exact ESP32-S3 board and selected sensors/servos are confirmed.

Pin selection must avoid conflicts with the currently documented room-monitoring connections:

| Existing function | GPIO |
|---|---:|
| HC-SR04 TRIG | 4 |
| HC-SR04 ECHO | 5 |
| DHT11 DATA | 6 |
| Digital room LDR | 7 |
| OLED SDA | 8 |
| OLED SCL/SCK | 9 |
| LED | 10 |

For analog LDR sensing, choose ADC-capable GPIOs compatible with the exact ESP32-S3 board. For servos, choose suitable free output pins and verify the servo library/timer configuration used by the final firmware.

## 8. Suggested implementation phases

### Phase A — bench sensor experiment

- Read the two solar light sensors.
- Print raw readings to Serial.
- Move a lamp left/right and verify the differential sign and useful deadband.

### Phase B — one servo

- Mount the panel on the horizontal axis only.
- Implement small-step tracking.
- Verify correct direction, no jitter and safe mechanical endpoints.

### Phase C — second axis

- Add the vertical servo.
- Validate whether the two-LDR arrangement provides enough information.
- If not, move to four-quadrant sensing before claiming autonomous dual-axis tracking.

### Phase D — AyuSaarthi integration

- Run room sensing and solar tracking together.
- Verify servo motion does not corrupt HC-SR04/DHT11/OLED operation or reset the ESP32-S3.
- Keep solar control local.
- Add optional tracker telemetry only after the local loop is stable.

## 9. Acceptance tests

The subsystem is ready for the hackathon demo when all of the following pass:

- Panel moves toward a brighter light source in the intended direction.
- No movement occurs inside the calibrated deadband.
- Servo commands never exceed tested mechanical limits.
- Blocking/disconnecting a light sensor causes a safe hold/fault behavior.
- Repeated servo movement does not reset the ESP32-S3.
- Room monitoring continues while tracking is active.
- The presentation describes the system as light/solar tracking rather than making unmeasured energy-efficiency claims.

## 10. Future upgrade path

A stronger second revision could add:

- four-quadrant LDR sensing;
- measured panel voltage/current using a suitable sensing circuit;
- power and energy logging;
- comparison between fixed-panel and tracked-panel energy yield;
- a proper solar charger / battery-management stage;
- dashboard visualization of panel angle and generated power.

Those upgrades would turn the solar feature from a visual tracking demonstration into a measurable energy experiment.
