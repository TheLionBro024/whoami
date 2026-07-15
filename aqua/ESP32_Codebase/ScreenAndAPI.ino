#include <Arduino.h>
#include <U8g2lib.h>
#include <ModbusMaster.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// --- Pin Definitions ---
#define RX_PIN 15
#define TX_PIN 2
#define SCL 26
#define SDA 27

// --- Configuration ---
const char* ssid = "Berglund IoT";
const char* password = "InternetOfThingsBerglund";
const char* serverUrl = "https://aqua.evolvplatform.com/api/sensor_data/add";

// Timing settings
unsigned long uploadInterval = 10000; // Post to API every 10 seconds
unsigned long lastUploadTime = 0;

// Screen and Modbus Instances
U8G2_SSD1306_128X64_NONAME_1_SW_I2C u8g2(U8G2_R0, SCL, SDA, /* reset=*/ U8X8_PIN_NONE);
ModbusMaster node;

// Global variables to hold the latest parsed data and status
float dissolved_oxygen = 0.0;
float temperature = 0.0;
String apiStatusStr = "Waiting...";

void setup(void) {
  u8g2.begin();
  Serial.begin(115200);
  while (!Serial) {}

  // Initialize Modbus Serial
  Serial2.begin(4800, SERIAL_8N1, RX_PIN, TX_PIN);
  node.begin(1, Serial2); // Slave ID 1

  // Connect to Wi-Fi and display status on screen
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  u8g2.firstPage();
  do {
    u8g2.setFontMode(1);
    u8g2.setBitmapMode(1);
    u8g2.setFont(u8g2_font_profont12_tr);
    u8g2.drawStr(1, 11, "Connecting to WiFi...");
  } while (u8g2.nextPage());

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nConnected to WiFi!");
  apiStatusStr = "WiFi Connected";
}

// Helper function to update the OLED layout
void updateDisplay(bool modbusSuccess, uint8_t errCode, String doStr, String tempStr) {
  u8g2.firstPage();
  do {
    u8g2.setFontMode(1);
    u8g2.setBitmapMode(1);
    u8g2.setFont(u8g2_font_profont12_tr);

    if (modbusSuccess) {
      // Line 1: Oxygen
      u8g2.drawStr(1, 11, "Oxygen:");
      u8g2.drawStr(50, 11, doStr.c_str());
      u8g2.drawStr(85, 11, "mg/L");

      // Line 2: Temperature
      u8g2.drawStr(1, 24, "Temp:");
      u8g2.drawStr(50, 24, tempStr.c_str());
      u8g2.drawUTF8(85, 24, "°C");
    } else {
      String errStr = "Code: 0x" + String(errCode, HEX);
      u8g2.drawStr(1, 11, "Modbus Error:");
      u8g2.drawStr(1, 24, errStr.c_str());
    }

    // Line 4: API upload network status tracker
    u8g2.drawStr(1, 55, "API:");
    u8g2.drawStr(30, 55, apiStatusStr.c_str());

  } while (u8g2.nextPage());
}

void sendDataToAPI(float temp, float oxy) {
  if (WiFi.status() != WL_CONNECTED) {
    apiStatusStr = "No WiFi Link";
    return;
  }

  // Create JSON document
  StaticJsonDocument<128> doc;
  doc["temperature"] = temp;
  doc["oxygen"] = oxy;

  String jsonPayload;
  serializeJson(doc, jsonPayload);

  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", "Evolv.IoTBerglund2026");

  Serial.print("Sending API payload: ");
  Serial.println(jsonPayload);

  int httpResponseCode = http.POST(jsonPayload);

  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    
    // Display HTTP status code (e.g., "API: OK (200)")
    apiStatusStr = "Sent (" + String(httpResponseCode) + ")";
  } else {
    Serial.print("HTTP Error code: ");
    Serial.println(httpResponseCode);
    apiStatusStr = "Err (" + String(httpResponseCode) + ")";
  }

  http.end();
}

void loop(void) {
  uint8_t result = node.readHoldingRegisters(0x02, 4);
  bool modbusSuccess = (result == node.ku8MBSuccess);

  String doStr = "0.00";
  String tempStr = "0.0";

  if (modbusSuccess) {
    // Parse Dissolved Oxygen (mg/L)
    uint32_t do_raw = (node.getResponseBuffer(0) << 16) | node.getResponseBuffer(1);
    memcpy(&dissolved_oxygen, &do_raw, sizeof(dissolved_oxygen));

    // Parse Temperature (°C)
    uint32_t temp_raw = (node.getResponseBuffer(2) << 16) | node.getResponseBuffer(3);
    memcpy(&temperature, &temp_raw, sizeof(temperature));

    // Convert to strings for display
    doStr = String(dissolved_oxygen, 2);
    tempStr = String(temperature, 1);

    // Print values to local Serial Monitor
    Serial.printf("Oxygen: %s mg/L | Temp: %s °C\n", doStr.c_str(), tempStr.c_str());
  } else {
    Serial.print("Modbus Error Code: 0x");
    Serial.println(result, HEX);
  }

  // Check if it's time to trigger an API data post
  if (millis() - lastUploadTime >= uploadInterval) {
    lastUploadTime = millis();
    
    if (modbusSuccess) {
      sendDataToAPI(temperature, dissolved_oxygen);
    } else {
      apiStatusStr = "Skip (Sensor Err)";
    }
  }

  // Refresh display components
  updateDisplay(modbusSuccess, result, doStr, tempStr);

  // Small delay to prevent hammering Modbus lines unnecessarily
  delay(500); 
}