#include <WiFi.h>
#include <HTTPClient.h>

// ====== CHANGE THESE ======
const char* ssid = "Sanjay's A35";
const char* password = "Sanjay@2007";
const char* testUrl = "http://172.18.231.181:5000/api/update"; 
// ==========================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("Starting ESP32 WiFi Test...");

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  int retry = 0;
  while (WiFi.status() != WL_CONNECTED && retry < 20) {
    delay(500);
    Serial.print(".");
    retry++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected!");
    Serial.print("ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ WiFi Connection Failed");
    return;
  }

  // Test HTTP connection
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    Serial.println("Sending test request to server...");
    http.begin(testUrl);
    http.addHeader("Content-Type", "application/json");

    // Dummy JSON
    String body = "{\"test\":\"esp32\"}";

    int code = http.POST(body);

    if (code > 0) {
      Serial.print("✅ Server reachable. HTTP Code: ");
      Serial.println(code);
      Serial.println(http.getString());
    } else {
      Serial.print("❌ Server not reachable. Error: ");
      Serial.println(code);
    }

    http.end();
  }
}

void loop() {
  // Nothing needed here
}
