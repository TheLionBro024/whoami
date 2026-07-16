#include <Arduino.h>
#include <U8g2lib.h>
#include <ModbusMaster.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// --- Pin Definitions ---
#define RX_PIN 26
#define TX_PIN 25
#define SCL_PIN 33
#define SDA_PIN 27

// --- Configuration ---
const char* ssid = "Berglund IoT";
const char* password = "InternetOfThingsBerglund";
const char* serverUrl = "https://aqua.evolvplatform.com/api/sensor_data/add";

// Non-blocking timing intervals
const unsigned long uploadInterval = 10000;    // Post to API every 10 seconds
const unsigned long sensorPollInterval = 2000;  // Read sensor every 2 seconds
unsigned long lastUploadTime = 0;
unsigned long lastPollTime = 0;

// Screen and Modbus Instances
// Optimized: Hardware I2C prevents processor-blocking during Modbus transactions
U8G2_SSD1306_128X64_NONAME_1_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE, SCL_PIN, SDA_PIN);
ModbusMaster node;

// Global variables to hold data, network status, and remote debug state
float dissolved_oxygen = 0.0;
float temperature = 0.0;
String apiStatusStr = "Waiting...";
bool remoteDebugActive = false; // Controlled remotely by your website's API response

// Helper function to update the OLED layout safely
void updateDisplay(bool modbusSuccess, uint8_t errCode, String doStr, String tempStr) {
  // 1. If remote debug is OFF, clear the screen and exit immediately
  if (!remoteDebugActive) {
    u8g2.firstPage();
    do {
      // Drawing nothing leaves the display entirely blank
    } while (u8g2.nextPage());
    return; 
  }

  // 2. If remote debug is ON, proceed with drawing the UI
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

  // Create JSON document to send to server
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
    String response = http.getString(); // Retrieve server reply
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    
    // --- Parse incoming commands from the server's response ---
    StaticJsonDocument<256> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error) {
      // If the server includes "debug_mode" in its response, update our local flag
      if (responseDoc.containsKey("debug_mode")) {
        bool previousState = remoteDebugActive;
        remoteDebugActive = responseDoc["debug_mode"].as<bool>();
        
        if (remoteDebugActive != previousState) {
          Serial.printf(">>> Remote Debug State Changed to: %s <<<\n", remoteDebugActive ? "ON" : "OFF");
        }
      }
    } else {
      Serial.print("Failed to parse API response JSON: ");
      Serial.println(error.c_str());
    }
    
    apiStatusStr = "Sent (" + String(httpResponseCode) + ")";
  } else {
    Serial.print("HTTP Error code: ");
    Serial.println(httpResponseCode);
    apiStatusStr = "Err (" + String(httpResponseCode) + ")";
  }

  http.end(); // Clear connection buffers and sockets to avoid memory leaks
}

void setup(void) {
  Serial.begin(115200);
  while (!Serial) {}

  // Initialize display
  u8g2.begin();

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

void loop(void) {
  unsigned long currentMillis = millis();
  static bool lastReadSuccessful = false;
  static uint8_t lastResultCode = 0;
  static String displayDo = "0.00";
  static String displayTemp = "0.0";

  // --- Task 1: Modbus Sensor Polling (Every 2 Seconds) ---
  if (currentMillis - lastPollTime >= sensorPollInterval) {
    lastPollTime = currentMillis;

    // SELF-HEALING: Clear out any garbage/leftover bytes in the UART buffer 
    // right before transmitting to prevent 0xE0 stuck loops.
    while (Serial2.available() > 0) {
      Serial2.read(); 
    }
    delay(5); // Let hardware lines settle

    // Request 4 registers starting at 0x02
    uint8_t result = node.readHoldingRegisters(0x02, 4);
    lastResultCode = result;
    lastReadSuccessful = (result == node.ku8MBSuccess);

    if (lastReadSuccessful) {
      // Parse Dissolved Oxygen (mg/L)
      uint32_t do_raw = (node.getResponseBuffer(0) << 16) | node.getResponseBuffer(1);
      memcpy(&dissolved_oxygen, &do_raw, sizeof(dissolved_oxygen));

      // Parse Temperature (°C)
      uint32_t temp_raw = (node.getResponseBuffer(2) << 16) | node.getResponseBuffer(3);
      memcpy(&temperature, &temp_raw, sizeof(temperature));

      // Convert variables to strings
      displayDo = String(dissolved_oxygen, 2);
      displayTemp = String(temperature, 1);

      // Standard Log
      Serial.printf("Oxygen: %s mg/L | Temp: %s °C\n", displayDo.c_str(), displayTemp.c_str());
      
      // --- Verbose Remote Debugging ---
      if (remoteDebugActive) {
        Serial.println("------------------------------------");
        Serial.println("[REMOTE DEBUG] Diagnostics Active:");
        Serial.printf("  - Raw Reg[0]: 0x%04X | Reg[1]: 0x%04X\n", node.getResponseBuffer(0), node.getResponseBuffer(1));
        Serial.printf("  - Raw Reg[2]: 0x%04X | Reg[3]: 0x%04X\n", node.getResponseBuffer(2), node.getResponseBuffer(3));
        Serial.printf("  - Wi-Fi RSSI (Signal): %d dBm\n", WiFi.RSSI());
        Serial.printf("  - ESP32 Free Heap RAM: %u bytes\n", ESP.getFreeHeap());
        Serial.println("------------------------------------");
      }
    } else {
      Serial.print("Modbus Error Code: 0x");
      Serial.println(result, HEX);
    }

    // Refresh screen on every reading update
    updateDisplay(lastReadSuccessful, lastResultCode, displayDo, displayTemp);
  }

  // --- Task 2: API Data Upload (Every 10 Seconds) ---
  if (currentMillis - lastUploadTime >= uploadInterval) {
    lastUploadTime = currentMillis;
    
    if (lastReadSuccessful) {
      sendDataToAPI(temperature, dissolved_oxygen);
    } else {
      apiStatusStr = "Skip (Sensor Err)";
    }
    
    // Refresh screen to quickly show the API's latest HTTP response code
    updateDisplay(lastReadSuccessful, lastResultCode, displayDo, displayTemp);
  }
}