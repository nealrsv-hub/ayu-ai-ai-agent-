# Initial milestones

Keep each step small enough to demonstrate before expanding it.

## 1. Run and understand the starter

- [ ] Create a virtual environment and install the base package.
- [ ] Run hello, help, time, sensors, and exit.
- [ ] Run the automated tests.
- [ ] Trace one command through the entry point, handler, and output.

Done when a fresh setup runs successfully and sensors reports not connected.

## 2. Validate spoken replies on the development computer

- [ ] Install the optional voice extra and test two consecutive spoken replies.
- [ ] Confirm text-only mode and recovery from unavailable audio.
- [ ] Record OS, Python version, installed voice dependency versions, and outcome.
- [ ] Decide whether microphone input is needed next; select its recognition backend
      only after agreeing offline/cloud use, language, and privacy requirements.

Done when two replies are audible on the actual computer and text remains usable
without speech. Microphone capture is a separate future change, not completed by
installing the voice extra.

## 3. Integrate one real sensor reading

Scope: ESP32-S3 and DHT11 only, from the confirmed project components.

- [ ] Confirm the actual board, wiring, and working firmware separately.
- [ ] Choose one transport (serial or HTTP); do not implement both initially.
- [ ] Agree a versioned message with device ID, units, reading time, and explicit
      invalid-reading status before writing the adapter.
- [ ] Implement and inject a SensorSource adapter; keep disconnected mode available.
- [ ] Test a valid reading, invalid payload, disconnect, timeout, and stale data.
- [ ] Label simulated data as simulated and keep it out of live status.

Done when one actual temperature/humidity reading is displayed and missing,
invalid, or stale data cannot appear as a normal current reading.

## Later, only after these checks

Choose an LLM provider and verified model/API contract if open-ended conversation
is needed. Add microphone input with visible recording control. Consider ultrasonic
and LDR inputs individually after confirming their message contracts. OLED, LCD,
and motor behavior need separate firmware and validation.

Fall detection, emergency escalation, and health recommendations are not starter
milestones. They require their own requirements, failure analysis, and validation;
a threshold demo is not a validated safety system.
