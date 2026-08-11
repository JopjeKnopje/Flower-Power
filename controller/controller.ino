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

// --- Count display ---
// Numbers above 31 do not fit five stamens, so they are pulsed additively:
// 32 = 31 + 1 (all five, then fire0), 75 = 31 + 31 + 13, and so on.
const unsigned long COUNT_GAP_MS = 700;  // dark gap between rounds

// --- Main mode ---
// Ten stages, one per band. Stage 0 is always 0 people, the last is the running
// record, the eight in between are random distinct counts in no particular order.
const uint8_t MAIN_STAGES = 10;
const uint8_t MAIN_MAX_FLOOR = 11;             // never decays below this
const uint8_t MAIN_MAX_HEADROOM = 5;           // new record = count + this, so a
                                               // busy night stops retriggering
// One timer, reset by every move. When it expires nothing has matched for a
// while, so the range is pulled towards the crowd actually being seen: the max
// halves and the min rises to the smallest count observed.
const unsigned long MAIN_REDRAW_MS = 480000UL;  // 8 min
const unsigned long MAIN_SEED = 42;            // fixed, so a reset redraws the same stages

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
int lastPrintedADC = -1;
bool lastPrintedAuto = false;

// --- Fire relays ---
const uint8_t firePins[] = { FIRE_0, FIRE_1, FIRE_2, FIRE_3, FIRE_4 };
const uint8_t FIRE_COUNT = sizeof(firePins) / sizeof(firePins[0]);
const unsigned long FIRE_HOLD = 0xFFFFFFFFUL;  // "on until switched off"

// Requested state per relay: FIRE_OFF, FIRE_HOLD, or the millis() at which it goes off again.
// Remote buttons and the HTTP API only write here; updateFire() owns the outputs.
const unsigned long FIRE_OFF = 0;
unsigned long fireUntil[FIRE_COUNT];
bool fireOn[FIRE_COUNT];

void setup() {
  Serial.begin(115200);
  randomSeed(MAIN_SEED);  // fixed, so the first stage draw after boot is reproducible

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

  // DHCP where a server exists, otherwise the fixed address above. Watch the
  // serial banner or scan for the MAC to find out which one you got.
  if (Ethernet.begin(mac) == 0) {
    Serial.println("DHCP failed, falling back to static IP");
    Ethernet.begin(mac, ip);
  }
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
  updateCount();
  updateMain();
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

    // Only publish when something actually changed; one ADC count is ~22 mm here
    if (rawADC != lastPrintedADC || autoMode != lastPrintedAuto) {
      lastPrintedADC = rawADC;
      lastPrintedAuto = autoMode;

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

// Apply to every relay in a bitmask (bit i = relay i)
void fireMask(uint8_t mask, unsigned long ms) {
  for (uint8_t i = 0; i < FIRE_COUNT; i++) if (mask & (1 << i)) fire(i, ms);
}

void stopFireMask(uint8_t mask) {
  for (uint8_t i = 0; i < FIRE_COUNT; i++) if (mask & (1 << i)) stopFire(i);
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

// --- Count display ---
// Pulses a number as binary, one round per 31, remainder last. Never blocks.
const uint8_t FIRE_MAX_COUNT = (1 << FIRE_COUNT) - 1;  // 31, all five stamens

bool countRunning = false;
uint8_t countLeft = 0;  // still to be shown
unsigned long countNextAt = 0;

void countStart(uint8_t n) {
  countRunning = true;
  countLeft = n;
  countNextAt = millis();  // first round on the next pass
  Serial.print(">>> Count ");
  Serial.println(n);
}

void countStop() {
  countRunning = false;
  countLeft = 0;
}

void updateCount() {
  if (!countRunning || (long)(millis() - countNextAt) < 0) return;

  if (countLeft == 0) {  // zero shows nothing, which is what zero people look like
    countRunning = false;
    return;
  }

  uint8_t round = countLeft > FIRE_MAX_COUNT ? FIRE_MAX_COUNT : countLeft;
  countLeft -= round;
  fireMask(round, SWIRL_PULSE_MS);
  countNextAt = millis() + SWIRL_PULSE_MS + COUNT_GAP_MS;
}

// Everything that drives the stamens on its own, silenced in one call
void stopPatterns() {
  if (swirlRunning) swirlStop();
  if (bloomActive) bloomStop();
  if (countRunning) countStop();
}

// --- Main mode ---
// A person count that matches a stage moves to that band and, on arrival, pulses
// the stamens as the binary of that number. Counts that match nothing hold position.
const uint8_t MAIN_MAX_LIMIT = 250;  // headroom must not overflow the uint8_t

bool mainMode = false;
bool mainFireNow = false;  // pulse the bits on match instead of waiting for arrival
uint8_t stageCount[MAIN_STAGES];
uint8_t mainMax = FIRE_MAX_COUNT;
uint8_t mainMin = 0;              // stage 0's count, lifted when nothing moves
uint8_t mainSeenMin = 255;        // smallest count since the last draw
unsigned long mainDrawnAt = 0;    // when the current stages were drawn
uint8_t mainPeople = 0;           // last count received
uint8_t mainPeak = 0;             // biggest count seen during a finale
int8_t mainStage = -1;            // stage being travelled to, -1 when idle
uint8_t mainShowValue = 0;        // number whose bits get pulsed on arrival
bool mainFinale = false;          // that stage was the record: swirl on arrival
bool mainAwaitCount = false;      // swirl once the record's number is fully shown
bool mainAwaitSwirl = false;      // re-randomize once the finale swirl finishes

// A record sits a little above the crowd that set it, so the next few arrivals
// do not immediately retrigger it
uint8_t withHeadroom(uint8_t people) {
  uint16_t raised = people + MAIN_MAX_HEADROOM;
  return raised > MAIN_MAX_LIMIT ? MAIN_MAX_LIMIT : raised;
}

// The eight interior stages need eight distinct counts strictly between min and
// max, so the range must never close up beyond that
void mainClampRange() {
  if (mainMax < MAIN_MAX_FLOOR) mainMax = MAIN_MAX_FLOOR;
  if (mainMin + MAIN_STAGES - 1 > mainMax) mainMin = mainMax - (MAIN_STAGES - 1);
}

void randomizeStages() {
  mainClampRange();
  stageCount[0] = mainMin;
  stageCount[MAIN_STAGES - 1] = mainMax;
  mainSeenMin = 255;
  mainDrawnAt = millis();

  for (uint8_t i = 1; i < MAIN_STAGES - 1; i++) {
    // Bounded retries: a duplicate beats a spin that never ends
    uint8_t v = mainMin + i;
    for (uint8_t tries = 0; tries < 50; tries++) {
      uint8_t candidate = random(mainMin + 1, mainMax);
      bool dup = false;
      for (uint8_t j = 1; j < i; j++) if (stageCount[j] == candidate) dup = true;
      if (!dup) { v = candidate; break; }
    }
    stageCount[i] = v;
  }

  Serial.print(">>> Stages:");
  for (uint8_t i = 0; i < MAIN_STAGES; i++) {
    Serial.print(' ');
    Serial.print(stageCount[i]);
  }
  Serial.println();
}

void mainStart() {
  mainMode = true;
  mainStage = -1;
  mainFinale = false;
  mainMin = 0;
  randomizeStages();
  Serial.print(">>> Main mode on, max ");
  Serial.println(mainMax);
}

void mainStop() {
  mainMode = false;
  mainStage = -1;
  mainFinale = false;
  Serial.println(">>> Main mode off");
}

// A new person count from the crowd tracker
void mainCount(uint16_t people) {
  if (!mainMode) return;
  mainPeople = people > 255 ? 255 : people;

  // A finale takes the best part of a minute. Counts arriving while it runs are
  // remembered, and the biggest one sets the max when the stages are re-drawn.
  if (mainAwaitCount || mainAwaitSwirl) {
    if (mainPeople > mainPeak) {
      mainPeak = mainPeople;
      Serial.print(">>> Crowd grew mid-finale to ");
      Serial.println(mainPeak);
    }
    return;
  }

  if (mainPeople < mainSeenMin) mainSeenMin = mainPeople;

  if (people > mainMax) {
    mainMax = withHeadroom(mainPeople);
    Serial.print(">>> New record ");
    Serial.print(people);
    Serial.print(", max ");
    Serial.println(mainMax);
    randomizeStages();  // band 9 holds the new record before we show anything
    mainGoTo(MAIN_STAGES - 1, mainPeople, true);
    return;
  }

  for (uint8_t i = 0; i < MAIN_STAGES; i++) {
    if (stageCount[i] != people) continue;
    mainGoTo(i, people, people == mainMax);
    return;
  }
  // No stage matches: hold position
}

void mainGoTo(uint8_t stage, uint8_t value, bool finale) {
  mainStage = stage;
  mainShowValue = value;
  mainFinale = finale;
  moveToBand(stage);
  Serial.print(">>> Main stage ");
  Serial.print(stage);
  Serial.print(" for ");
  Serial.print(value);
  Serial.println(finale ? " people (finale)" : " people");

  if (mainFireNow) mainShow();
}

// Pulse the stamens as the binary of the count, swirl if it was the record
void mainShow() {
  Serial.print(">>> Showing ");
  Serial.println(mainShowValue);
  countStart(mainShowValue);

  // The finale waits for the whole number to be shown before the swirl starts
  mainAwaitCount = mainFinale;
  if (mainFinale) mainPeak = mainShowValue;
  mainStage = -1;
  mainFinale = false;
}

void updateMain() {
  if (!mainMode) return;

  // Reaching the record re-draws the stages itself, so this timer expiring means
  // we never got there. Pull the range towards the crowd actually being seen.
  if (!mainAwaitCount && !mainAwaitSwirl &&
      (long)(millis() - mainDrawnAt) >= (long)MAIN_REDRAW_MS) {
    if (mainSeenMin == 255) {
      mainMax = mainMax / 2;  // nobody at all: walk the whole range back down
      mainMin = mainMin / 2;
    } else {
      mainMin = mainSeenMin;  // a crowd that never matches: lift the floor to it
    }
    Serial.print(">>> Nothing moving, range now ");
    Serial.print(mainMin);
    Serial.print("-");
    Serial.println(mainMax);
    randomizeStages();  // clamps the range and resets the timer
  }

  // The record's number is shown in full, then the swirl runs
  if (mainAwaitCount && !countRunning) {
    mainAwaitCount = false;
    mainAwaitSwirl = true;
    swirlStart();
  }

  // The finale swirl runs to completion before the stages are re-drawn, and the
  // biggest crowd seen during it becomes the new record
  if (mainAwaitSwirl && !swirlRunning) {
    mainAwaitSwirl = false;
    if (mainPeak > mainMax) {
      mainMax = withHeadroom(mainPeak);
      Serial.print(">>> Crowd peaked at ");
      Serial.print(mainPeak);
      Serial.print(", max ");
      Serial.println(mainMax);
    }
    Serial.println(">>> Swirl finished, new stages");
    randomizeStages();
  }

  // moveToBand() clears autoMode once the band is reached
  if (mainStage < 0 || autoMode) return;
  mainShow();
}

// --- HTTP API ---
// GET /status                  -> JSON with position, fire and pattern state
// GET /move?band=N             -> move to band N (0-9), target = N*100+50 mm
// GET /stop                    -> stop auto-positioning
// GET /fire?n=0,2,4[&ms=250]   -> pulse those relays, default SWIRL_PULSE_MS
// GET /fire?n=all&on           -> latch on
// GET /fire?n=all&off          -> latch off; n=all also stops the patterns
// GET /swirl?on | /swirl?off   -> start/stop the swirl sequence
// GET /bloom?on | /bloom?off   -> start/stop the bloom sequence
// GET /main?on[&now]           -> main mode; fires on arrival at the band, ?now
//                                 fires on match instead (testing). ?arrival reverts
// GET /main?off                -> main mode off
// GET /people?n=N              -> person count from the crowd tracker
// GET /count?n=N               -> pulse N as binary, additively above 31

// Value of query parameter `key`, or NULL. Matches whole keys only, so
// looking for "n" does not trip over "on".
const char *param(const char *req, const char *key) {
  const char *p = strchr(req, '?');
  size_t klen = strlen(key);
  for (; p; p = strchr(p + 1, '&')) {
    const char *k = p + 1;
    if (strncmp(k, key, klen) == 0 && k[klen] == '=') return k + klen + 1;
  }
  return NULL;
}

// True if a value-less flag like "&on" is present
bool flag(const char *req, const char *key) {
  const char *p = strchr(req, '?');
  size_t klen = strlen(key);
  for (; p; p = strchr(p + 1, '&')) {
    const char *k = p + 1;
    if (strncmp(k, key, klen) != 0) continue;
    char end = k[klen];
    if (end == '&' || end == ' ' || end == '\0') return true;
  }
  return false;
}

// Value of an integer parameter, or -1 when missing or not a number
long paramNumber(const char *req, const char *key) {
  const char *p = param(req, key);
  if (!p || *p < '0' || *p > '9') return -1;
  return strtoul(p, NULL, 10);
}

// "0,2,4" or "all" / "*" -> bitmask, -1 if unparsable
int parseFireMask(const char *v) {
  if (!v) return -1;
  if (*v == '*' || strncmp(v, "all", 3) == 0) return FIRE_MAX_COUNT;
  int mask = 0;
  while (*v >= '0' && *v <= '9') {
    uint8_t i = 0;
    while (*v >= '0' && *v <= '9') i = i * 10 + (*v++ - '0');
    if (i >= FIRE_COUNT) return -1;
    mask |= 1 << i;
    if (*v == ',' || *v == '+') v++;
  }
  return mask ? mask : -1;
}

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
    const char *p = param(request, "band");
    if (p) {
      int band = *p - '0';
      if (band >= 0 && band <= 9) {
        moveToBand(band);
        sendJSON(client, 200, strokeMM, rawADC);
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
    sendJSON(client, 200, strokeMM, rawADC);
  } else if (strstr(request, "GET /fire")) {
    int mask = parseFireMask(param(request, "n"));
    const char *ms = param(request, "ms");
    if (mask < 0) {
      sendError(client, 400, "n must be 0-4 list or all");
    } else {
      if (flag(request, "off")) {
        // clearing everything also clears the patterns feeding it
        mask == FIRE_MAX_COUNT ? fireAllOff() : stopFireMask(mask);
      } else if (flag(request, "on")) {
        fireMask(mask, FIRE_HOLD);
      } else {
        fireMask(mask, ms ? strtoul(ms, NULL, 10) : SWIRL_PULSE_MS);
      }
      sendJSON(client, 200, strokeMM, rawADC);
    }
  } else if (strstr(request, "GET /swirl")) {
    // swirlStop() flips the direction, so only call it when actually running
    if (flag(request, "on")) swirlStart();
    else if (swirlRunning) swirlStop();
    sendJSON(client, 200, strokeMM, rawADC);
  } else if (strstr(request, "GET /bloom")) {
    if (flag(request, "on")) bloomStart();
    else if (bloomActive) bloomStop();
    sendJSON(client, 200, strokeMM, rawADC);
  } else if (strstr(request, "GET /count")) {
    long n = paramNumber(request, "n");
    if (n < 0) {
      sendError(client, 400, "n must be a number");
    } else {
      countStart(n > 255 ? 255 : n);
      sendJSON(client, 200, strokeMM, rawADC);
    }
  } else if (strstr(request, "GET /main")) {
    // Testing aid: ?now pulses on match instead of on arrival, ?arrival reverts
    if (flag(request, "now")) mainFireNow = true;
    if (flag(request, "arrival")) mainFireNow = false;
    if (flag(request, "on")) mainStart();
    else if (flag(request, "off") && mainMode) mainStop();
    sendJSON(client, 200, strokeMM, rawADC);
  } else if (strstr(request, "GET /people")) {
    long n = paramNumber(request, "n");
    if (n < 0) {
      sendError(client, 400, "n must be a person count");
    } else if (!mainMode) {
      sendError(client, 400, "main mode is off");
    } else {
      mainCount(n);
      sendJSON(client, 200, strokeMM, rawADC);
    }
  } else if (strstr(request, "GET /status")) {
    sendJSON(client, 200, strokeMM, rawADC);
  } else {
    sendError(client, 404, "not found");
  }

  delay(1);
  client.stop();
}

void sendHeader(EthernetClient &client, int code, const char *reason) {
  client.print("HTTP/1.1 ");
  client.print(code);
  client.print(' ');
  client.println(reason);
  client.println("Content-Type: application/json");
  client.println("Connection: close");
  client.println();
}

// Both emit the leading comma, so every field after the first one composes
void jsonBool(EthernetClient &client, const char *key, bool value) {
  client.print(",\"");
  client.print(key);
  client.print("\":");
  client.print(value ? "true" : "false");
}

void jsonNum(EthernetClient &client, const char *key, long value) {
  client.print(",\"");
  client.print(key);
  client.print("\":");
  client.print(value);
}

void jsonArray(EthernetClient &client, const char *key, const uint8_t *values, uint8_t n) {
  client.print(",\"");
  client.print(key);
  client.print("\":[");
  for (uint8_t i = 0; i < n; i++) {
    if (i) client.print(',');
    client.print(values[i]);
  }
  client.print(']');
}

void sendJSON(EthernetClient &client, int code, float strokeMM, int rawADC) {
  // Push this request's changes out before reporting them, so the reply is not a
  // loop-iteration behind what it just asked for
  updateCount();
  updateFire();
  sendHeader(client, code, "OK");

  client.print("{\"up_ms\":");
  client.print(millis());  // jumps back to ~0 if the board reset under you
  client.print(",\"stroke_mm\":");
  client.print(strokeMM, 1);
  jsonNum(client, "adc", rawADC);
  jsonBool(client, "auto", autoMode);
  if (autoMode) jsonNum(client, "target_mm", (long)targetMM);

  uint8_t lit[FIRE_COUNT];
  for (uint8_t i = 0; i < FIRE_COUNT; i++) lit[i] = fireOn[i] ? 1 : 0;
  jsonArray(client, "fire", lit, FIRE_COUNT);

  jsonBool(client, "swirl", swirlRunning);
  jsonBool(client, "bloom", bloomActive);
  jsonBool(client, "counting", countRunning);
  if (countRunning) jsonNum(client, "count_left", countLeft);

  jsonBool(client, "main", mainMode);
  if (mainMode) {
    jsonBool(client, "fire_now", mainFireNow);
    jsonNum(client, "people", mainPeople);
    jsonNum(client, "min", mainMin);
    jsonNum(client, "max", mainMax);
    jsonNum(client, "seen_min", mainSeenMin);
    jsonArray(client, "stages", stageCount, MAIN_STAGES);
  }
  client.println("}");
}

void sendError(EthernetClient &client, int code, const char *msg) {
  sendHeader(client, code, code == 400 ? "Bad Request" : "Not Found");
  client.print("{\"error\":\"");
  client.print(msg);
  client.println("\"}");
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
void btnFireAll(bool pressed)  { pressed ? fireAll() : fireAllOff(); }

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
