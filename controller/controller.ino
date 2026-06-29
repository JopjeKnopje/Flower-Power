#include <Controllino.h>
#include <SPI.h>
#include <Ethernet.h>

// --- Pin assignments ---
#define RELAY_EXTEND    CONTROLLINO_R0
#define RELAY_RETRACT   CONTROLLINO_R1
#define BUTTON_EXTEND   CONTROLLINO_A1
#define BUTTON_RETRACT  CONTROLLINO_A2
#define POT_INPUT       CONTROLLINO_A0

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

// --- Timing ---
const unsigned long PRINT_INTERVAL_MS = 250;
unsigned long lastPrintTime = 0;

void setup() {
  Serial.begin(115200);

  pinMode(RELAY_EXTEND, OUTPUT);
  pinMode(RELAY_RETRACT, OUTPUT);
  pinMode(BUTTON_EXTEND, INPUT);
  pinMode(BUTTON_RETRACT, INPUT);

  digitalWrite(RELAY_EXTEND, LOW);
  digitalWrite(RELAY_RETRACT, LOW);

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

  float currentMM = adcToStroke(analogRead(POT_INPUT));

  bool btnExtend  = digitalRead(BUTTON_EXTEND) == HIGH;
  bool btnRetract = digitalRead(BUTTON_RETRACT) == HIGH;

  if (btnExtend || btnRetract) {
    autoMode = false;
  }

  if (btnExtend && !btnRetract) {
    driveExtend();
  } else if (btnRetract && !btnExtend) {
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
        targetMM = band * 100.0 + 50.0;
        autoMode = true;
        Serial.print(">>> HTTP: Moving to ");
        Serial.print(targetMM, 0);
        Serial.println(" mm");
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

void handleSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c >= '0' && c <= '9') {
      int band = c - '0';
      targetMM = band * 100.0 + 50.0;
      autoMode = true;
      Serial.print(">>> Moving to ");
      Serial.print(targetMM, 0);
      Serial.println(" mm");
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

float adcToStroke(int rawADC) {
  float stroke = (float)(rawADC - calADC_0mm) / (float)(calADC_1000mm - calADC_0mm) * MAX_STROKE_MM;
  if (stroke < 0.0) stroke = 0.0;
  if (stroke > MAX_STROKE_MM) stroke = MAX_STROKE_MM;
  return stroke;
}
