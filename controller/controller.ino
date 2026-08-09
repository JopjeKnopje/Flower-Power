#include <Controllino.h>
#include <SPI.h>
#include <Ethernet.h>

// --- Pin assignments ---
#define RELAY_EXTEND    CONTROLLINO_R0
#define RELAY_RETRACT   CONTROLLINO_R1
#define BUTTON_EXTEND   CONTROLLINO_A1
#define BUTTON_RETRACT  CONTROLLINO_A2
#define POT_INPUT       CONTROLLINO_A0

#define FIRE_0          CONTROLLINO_R5
#define FIRE_1          CONTROLLINO_R6
#define FIRE_2          CONTROLLINO_R7
#define FIRE_3          CONTROLLINO_R8
#define FIRE_4          CONTROLLINO_R9

// --- Remote button mapping ---
void btnRetract(bool pressed);
void btnExtend(bool pressed);
void btnBloom(bool pressed);
void btnSwirl(bool pressed);
void btnFireAll(bool pressed);
void btnFire0(bool pressed);
void btnFire1(bool pressed);
void btnFire2(bool pressed);
void btnFire3(bool pressed);
void btnFire4(bool pressed);
void btnBand0(bool pressed);
void btnBand3(bool pressed);
void btnBand6(bool pressed);
void btnBand9(bool pressed);

struct RemoteButton {
  uint8_t pin;
  void (*handler)(bool pressed);
};

const RemoteButton remoteButtons[] = {
  { CONTROLLINO_A4,  btnRetract    },
  { CONTROLLINO_A5,  btnExtend     },
  { CONTROLLINO_A6,  btnBloom      },
  { CONTROLLINO_A7,  btnSwirl      },
  { CONTROLLINO_A8,  btnFireAll    },
  { CONTROLLINO_A9,  btnFire4      },
  { CONTROLLINO_A10, btnBand9      },
  { CONTROLLINO_A11, btnFire3      },
  { CONTROLLINO_A12, btnBand6      },
  { CONTROLLINO_A13, btnFire2      },
  { CONTROLLINO_A14, btnBand3      },
  { CONTROLLINO_A15, btnFire1      },
  { CONTROLLINO_I16, btnBand0      },
  { CONTROLLINO_I17, btnFire0      },
};

const uint8_t REMOTE_COUNT = sizeof(remoteButtons) / sizeof(remoteButtons[0]);
bool remotePressed[REMOTE_COUNT];

// --- Pattern tuning ---
const unsigned long SWIRL_PULSE_MS     = 150;
const unsigned long SWIRL_GAP_START_MS = 2000;
const unsigned long SWIRL_GAP_STEP_MS  = 500;
const unsigned long SWIRL_RECHARGE_MS  = 6000;
const unsigned long SWIRL_FINALE_MS    = 2000;

const unsigned long BLOOM_PULSE_MS = 250;
const float BLOOM_HYST_MM = 25.0;

// --- Network configuration ---
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0x42 };
IPAddress ip(192, 168, 0, 42);
EthernetServer server(80);

// --- Calibration parameters ---
// Raw ADC value when cylinder is fully retracted (0 mm)
int calADC_0mm = 807;
// Raw ADC value when cylinder is fully extended (1000 mm)
int calADC_1000mm = 761;

// --- Cylinder parameters ---
const float MAX_STROKE_MM = 1000.0;
const float DEADBAND_MM = 25.0;

// --- Auto-positioning ---
bool autoMode = false;
float targetMM = 0.0;

// --- Remote drive requests ---
bool remoteExtend = false;
bool remoteRetract = false;

// --- Timing ---
const unsigned long PRINT_INTERVAL_MS = 250;
unsigned long lastPrintTime = 0;

// --- Fire relays ---
const uint8_t firePins[] = { FIRE_0, FIRE_1, FIRE_2, FIRE_3, FIRE_4 };
const uint8_t FIRE_COUNT = sizeof(firePins);
const unsigned long FIRE_HOLD = 0xFFFFFFFFUL;  // "on until switched off"

// Requested state per relay: FIRE_OFF, FIRE_HOLD, or the millis() at which it goes off again.
// Remote buttons and the HTTP API only write here; updateFire() owns the outputs.
const unsigned long FIRE_OFF = 0;
unsigned long fireUntil[FIRE_COUNT];
bool fireOn[FIRE_COUNT];

void setup() {
  Serial.begin(115200);

  pinMode(RELAY_EXTEND, OUTPUT);
  pinMode(RELAY_RETRACT, OUTPUT);

  pinMode(BUTTON_EXTEND, INPUT);
  pinMode(BUTTON_RETRACT, INPUT);
  initRemote();

  digitalWrite(RELAY_EXTEND, LOW);
  digitalWrite(RELAY_RETRACT, LOW);

  for (uint8_t i = 0; i < FIRE_COUNT; i++) {
    pinMode(firePins[i], OUTPUT);
    digitalWrite(firePins[i], LOW);
  }

  Ethernet.begin(mac, ip);
  server.begin();

  Serial.println("=== Hydraulic Cylinder Controller ===");
  Serial.print("Calibration: ADC at 0mm = ");
  Serial.print(calADC_0mm);
  Serial.print("  ADC at 1000mm = ");
  Serial.println(calADC_1000mm);
  Serial.println("Buttons: A1=extend, A2=retract");
  Serial.println("Serial: 0-9 = go to 50,150,..,950 mm");
  Serial.println("        s   = stop auto-positioning");
  Serial.print("HTTP API: http://");
  Serial.println(Ethernet.localIP());
  Serial.println("=====================================");
}

void loop() {
  handleSerial();
  handleHTTP();
  readRemote();
  updateSwirl();
  updateFire();

  float currentMM = adcToStroke(analogRead(POT_INPUT));
  updateBloom(currentMM);

  bool wantExtend  = digitalRead(BUTTON_EXTEND) == HIGH || remoteExtend;
  bool wantRetract = digitalRead(BUTTON_RETRACT) == HIGH || remoteRetract;

  if (wantExtend || wantRetract) {
    autoMode = false;
  }

  if (wantExtend && !wantRetract) {
    driveExtend();
  } else if (wantRetract && !wantExtend) {
    driveRetract();
  } else if (autoMode) {
    float error = targetMM - currentMM;
    if (error > DEADBAND_MM) {
      driveExtend();
    } else if (error < -DEADBAND_MM) {
      driveRetract();
    } else {
      driveStop();
      autoMode = false;
      Serial.print(">>> Reached target: ");
      Serial.print(targetMM, 0);
      Serial.println(" mm");
    }
  } else {
    driveStop();
  }

  unsigned long now = millis();
  if (now - lastPrintTime >= PRINT_INTERVAL_MS) {
    lastPrintTime = now;
    int rawADC = analogRead(POT_INPUT);
    float strokeMM = adcToStroke(rawADC);
    Serial.print("ADC: ");
    Serial.print(rawADC);
    Serial.print("  Stroke: ");
    Serial.print(strokeMM, 1);
    Serial.print(" mm");
    if (autoMode) {
      Serial.print("  -> ");
      Serial.print(targetMM, 0);
      Serial.print(" mm");
    }
    Serial.println();
  }
}

// --- HTTP API ---
// GET /status         -> JSON with current position
// GET /move?band=N    -> move to band N (0-9), target = N*100+50 mm
// GET /stop           -> stop auto-positioning

void handleHTTP() {
  EthernetClient client = server.available();
  if (!client) return;

  char request[128];
  int reqLen = 0;
  bool lineBlank = false;
  unsigned long timeout = millis() + 500;

  while (client.connected() && millis() < timeout) {
    if (!client.available()) continue;
    char c = client.read();

    if (reqLen < (int)sizeof(request) - 1 && reqLen >= 0) {
      // Capture first line only
      if (c == '\r' || c == '\n') {
        if (reqLen > 0 && request[reqLen - 1] != '\0') {
          request[reqLen] = '\0';
        }
      } else if (request[reqLen > 0 ? reqLen - 1 : 0] != '\0' || reqLen == 0) {
        request[reqLen++] = c;
      }
    }

    if (c == '\n' && lineBlank) break;
    lineBlank = (c == '\n') ? true : (c != '\r') ? false : lineBlank;
  }
  request[reqLen] = '\0';

  int rawADC = analogRead(POT_INPUT);
  float strokeMM = adcToStroke(rawADC);

  if (strstr(request, "GET /move")) {
    char *p = strstr(request, "band=");
    if (p) {
      int band = p[5] - '0';
      if (band >= 0 && band <= 9) {
        moveToBand(band);
        sendJSON(client, 200, strokeMM, rawADC, targetMM, true);
      } else {
        sendError(client, 400, "band must be 0-9");
      }
    } else {
      sendError(client, 400, "missing band parameter");
    }
  } else if (strstr(request, "GET /stop")) {
    autoMode = false;
    driveStop();
    Serial.println(">>> HTTP: Stopped");
    sendJSON(client, 200, strokeMM, rawADC, 0, false);
  } else if (strstr(request, "GET /status")) {
    sendJSON(client, 200, strokeMM, rawADC, targetMM, autoMode);
  } else {
    sendError(client, 404, "not found");
  }

  delay(1);
  client.stop();
}

void sendJSON(EthernetClient &client, int code, float strokeMM, int rawADC, float target, bool moving) {
  client.print("HTTP/1.1 ");
  client.print(code);
  client.println(" OK");
  client.println("Content-Type: application/json");
  client.println("Connection: close");
  client.println();
  client.print("{\"stroke_mm\":");
  client.print(strokeMM, 1);
  client.print(",\"adc\":");
  client.print(rawADC);
  client.print(",\"auto\":");
  client.print(moving ? "true" : "false");
  if (moving) {
    client.print(",\"target_mm\":");
    client.print(target, 0);
  }
  client.println("}");
}

void sendError(EthernetClient &client, int code, const char *msg) {
  client.print("HTTP/1.1 ");
  client.print(code);
  client.println(code == 400 ? " Bad Request" : " Not Found");
  client.println("Content-Type: application/json");
  client.println("Connection: close");
  client.println();
  client.print("{\"error\":\"");
  client.print(msg);
  client.println("\"}");
}

void moveToBand(int band) {
  targetMM = band * 100.0 + 50.0;
  autoMode = true;
  Serial.print(">>> Moving to band ");
  Serial.print(band);
  Serial.print(", ");
  Serial.print(targetMM, 0);
  Serial.println(" mm");
}

void handleSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c >= '0' && c <= '9') {
      moveToBand(c - '0');
    } else if (c == 's' || c == 'S') {
      autoMode = false;
      driveStop();
      Serial.println(">>> Stopped");
    }
  }
}

void driveExtend() {
  digitalWrite(RELAY_EXTEND, HIGH);
  digitalWrite(RELAY_RETRACT, LOW);
}

void driveRetract() {
  digitalWrite(RELAY_EXTEND, LOW);
  digitalWrite(RELAY_RETRACT, HIGH);
}

void driveStop() {
  digitalWrite(RELAY_EXTEND, LOW);
  digitalWrite(RELAY_RETRACT, LOW);
}

// --- Fire relays ---
// Switch fire relay i on for ms milliseconds. Never blocks, calling it again extends the pulse.
void fire(uint8_t i, unsigned long ms) {
  if (i < FIRE_COUNT) fireUntil[i] = (ms == FIRE_HOLD) ? FIRE_HOLD : millis() + ms;
}

void fire(uint8_t i) {
  fire(i, FIRE_HOLD);
}

void stopFire(uint8_t i) {
  if (i < FIRE_COUNT) fireUntil[i] = FIRE_OFF;
}

void fireAll(unsigned long ms) {
  for (uint8_t i = 0; i < FIRE_COUNT; i++) fire(i, ms);
}

void fireAll() {
  fireAll(FIRE_HOLD);
}

void fireAllOff() {
  stopPatterns();
  for (uint8_t i = 0; i < FIRE_COUNT; i++) fireUntil[i] = FIRE_OFF;
}

// The only place the fire relay outputs are written
void updateFire() {
  unsigned long now = millis();
  for (uint8_t i = 0; i < FIRE_COUNT; i++) {
    if (fireUntil[i] != FIRE_OFF && fireUntil[i] != FIRE_HOLD &&
        (long)(now - fireUntil[i]) >= 0) {  // signed compare survives millis() rollover
      fireUntil[i] = FIRE_OFF;
    }

    bool on = fireUntil[i] != FIRE_OFF;
    if (on == fireOn[i]) continue;
    fireOn[i] = on;
    digitalWrite(firePins[i], on ? HIGH : LOW);

    Serial.print(">>> Fire ");
    Serial.print(i);
    Serial.println(on ? " on" : " off");
  }
}

// --- Swirl ---
bool swirlRunning = false;
bool swirlReverse = false;
bool swirlFinale = false;
uint8_t swirlStep = 0;
unsigned long swirlGap = 0;
unsigned long swirlNextAt = 0;

void swirlStart() {
  swirlRunning = true;
  swirlFinale = false;
  swirlStep = 0;
  swirlGap = SWIRL_GAP_START_MS;
  swirlNextAt = millis();
  Serial.print(">>> Swirl start, ");
  Serial.println(swirlReverse ? "reverse" : "forward");
}

void swirlStop() {
  swirlRunning = false;
  swirlFinale = false;
  swirlReverse = !swirlReverse;
  Serial.println(">>> Swirl stop");
}

void updateSwirl() {
  if (!swirlRunning || (long)(millis() - swirlNextAt) < 0) return;

  if (swirlFinale) {
    Serial.println(">>> Swirl finale");
    fireAll(SWIRL_FINALE_MS);
    swirlStop();
    return;
  }

  if (swirlStep >= FIRE_COUNT) {
    if (swirlGap <= SWIRL_GAP_STEP_MS) {
      swirlFinale = true;
      swirlNextAt = millis() + SWIRL_RECHARGE_MS;
      Serial.println(">>> Swirl recharging");
      return;
    }
    swirlGap -= SWIRL_GAP_STEP_MS;
    swirlStep = 0;
    Serial.print(">>> Swirl round, gap ");
    Serial.println(swirlGap);
  }

  // Hop 2 of 5 nodes = 144 deg, the closest this ring gets to the golden angle
  uint8_t stride = swirlReverse ? FIRE_COUNT - 2 : 2;
  fire((swirlStep * stride) % FIRE_COUNT, SWIRL_PULSE_MS);
  swirlNextAt = millis() + SWIRL_PULSE_MS + swirlGap;
  swirlStep++;
}

// --- Bloom ---
const uint8_t bloomRings[][2] = { { 2, 2 }, { 1, 3 }, { 0, 4 } };
const uint8_t BLOOM_RINGS = sizeof(bloomRings) / sizeof(bloomRings[0]);

bool bloomActive = false;
int8_t bloomRing = -1;

int8_t bloomRingAt(float mm, int8_t from) {
  const float width = MAX_STROKE_MM / BLOOM_RINGS;
  int8_t r = from < 0 ? 0 : from;
  while (r < BLOOM_RINGS - 1 && mm > (r + 1) * width + BLOOM_HYST_MM) r++;
  while (r > 0 && mm < r * width - BLOOM_HYST_MM) r--;
  return r;
}

void bloomStart() {
  bloomActive = true;
  bloomRing = -1;
  Serial.println(">>> Bloom on");
}

void bloomStop() {
  bloomActive = false;
  Serial.println(">>> Bloom off");
}

void updateBloom(float mm) {
  if (!bloomActive) return;

  int8_t ring = bloomRingAt(mm, bloomRing);
  if (ring == bloomRing) return;
  bloomRing = ring;

  fire(bloomRings[ring][0], BLOOM_PULSE_MS);
  fire(bloomRings[ring][1], BLOOM_PULSE_MS);

  Serial.print(">>> Bloom ring ");
  Serial.print(ring);
  Serial.print(" at ");
  Serial.print(mm, 0);
  Serial.println(" mm");
}

void stopPatterns() {
  if (swirlRunning) swirlStop();
  if (bloomActive) bloomStop();
}

// --- Remote buttons ---
void btnBloom(bool pressed) {
  if (!pressed) return;
  bloomActive ? bloomStop() : bloomStart();
}

void btnSwirl(bool pressed) {
  if (!pressed) return;
  if (swirlRunning) {
    swirlStop();
    fireAll(SWIRL_PULSE_MS);
  } else {
    swirlStart();
  }
}

void btnRetract(bool pressed) { remoteRetract = pressed; }
void btnExtend(bool pressed)  { remoteExtend = pressed; }

void btnBand0(bool pressed)   { if (pressed) moveToBand(0); }
void btnBand3(bool pressed)   { if (pressed) moveToBand(3); }
void btnBand6(bool pressed)   { if (pressed) moveToBand(6); }
void btnBand9(bool pressed)   { if (pressed) moveToBand(9); }

void btnFire0(bool pressed)   { pressed ? fire(0) : stopFire(0); }
void btnFire1(bool pressed)   { pressed ? fire(1) : stopFire(1); }
void btnFire2(bool pressed)   { pressed ? fire(2) : stopFire(2); }
void btnFire3(bool pressed)   { pressed ? fire(3) : stopFire(3); }
void btnFire4(bool pressed)   { pressed ? fire(4) : stopFire(4); }
void btnFireAll(bool pressed)    { pressed ? fireAll() : fireAllOff(); }
void btnFireAllOff(bool pressed) { if (pressed) fireAllOff(); }

void btn7(bool pressed)  {}
void btn8(bool pressed)  {}
void btn9(bool pressed)  {}
void btn10(bool pressed) {}
void btn11(bool pressed) {}
void btn12(bool pressed) {}
void btn13(bool pressed) {}
void btn14(bool pressed) {}

void initRemote() {
  for (uint8_t i = 0; i < REMOTE_COUNT; i++) pinMode(remoteButtons[i].pin, INPUT);
}

void readRemote() {
  for (uint8_t i = 0; i < REMOTE_COUNT; i++) {
    bool pressed = digitalRead(remoteButtons[i].pin) == HIGH;
    if (pressed == remotePressed[i]) continue;
    remotePressed[i] = pressed;

    Serial.print(">>> Btn ");
    Serial.print(i);
    Serial.println(pressed ? " pressed" : " released");

    remoteButtons[i].handler(pressed);
  }
}

float adcToStroke(int rawADC) {
  float stroke = (float)(rawADC - calADC_0mm) / (float)(calADC_1000mm - calADC_0mm) * MAX_STROKE_MM;
  if (stroke < 0.0) stroke = 0.0;
  if (stroke > MAX_STROKE_MM) stroke = MAX_STROKE_MM;
  return stroke;
}
