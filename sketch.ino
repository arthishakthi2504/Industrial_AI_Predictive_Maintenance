#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <DHT.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <math.h>

// ==========================================
// WIFI
// ==========================================

const char* ssid = "Wokwi-GUEST";
const char* password = "";

// ==========================================
// PYTHON SERVER
// ==========================================

const char* serverURL =
  "http://host.wokwi.internal:5000/api/sensor";

// ==========================================
// SENSOR PINS
// ==========================================

#define DHT_PIN 4
#define DHT_TYPE DHT22

#define CURRENT_PIN 34

// ==========================================
// SENSOR OBJECTS
// ==========================================

DHT dht(DHT_PIN, DHT_TYPE);

Adafruit_MPU6050 mpu;

// ==========================================
// SETUP
// ==========================================

void setup()
{
  Serial.begin(115200);

  delay(1000);

  Serial.println();
  Serial.println("====================================");
  Serial.println("   INDUSTRIAL AI SENSOR NODE");
  Serial.println("====================================");

  // -----------------------------
  // DHT22
  // -----------------------------

  dht.begin();

  Serial.println("DHT22 initialized.");

  // -----------------------------
  // MPU6050
  // -----------------------------

  Wire.begin(21, 22);

  if (!mpu.begin())
  {
    Serial.println("MPU6050 not detected!");

    while (1)
    {
      delay(1000);
    }
  }

  Serial.println("MPU6050 initialized.");

  // -----------------------------
  // WiFi
  // -----------------------------

  WiFi.begin(
    ssid,
    password
  );

  Serial.print("Connecting to WiFi");

  while (
    WiFi.status() != WL_CONNECTED
  )
  {
    delay(500);

    Serial.print(".");
  }

  Serial.println();

  Serial.println(
    "WiFi connected!"
  );

  Serial.print(
    "ESP32 IP: "
  );

  Serial.println(
    WiFi.localIP()
  );

  Serial.println();

  Serial.println(
    "System ready."
  );
}

// ==========================================
// LOOP
// ==========================================

void loop()
{
  // ========================================
  // TEMPERATURE
  // ========================================

  float temperature =
    dht.readTemperature();

  if (isnan(temperature))
  {
    Serial.println(
      "Temperature reading failed!"
    );

    delay(2000);

    return;
  }

  // ========================================
  // MPU6050
  // ========================================

  sensors_event_t acceleration;
  sensors_event_t gyro;
  sensors_event_t temperatureEvent;

  mpu.getEvent(
    &acceleration,
    &gyro,
    &temperatureEvent
  );

  float ax =
    acceleration.acceleration.x;

  float ay =
    acceleration.acceleration.y;

  float az =
    acceleration.acceleration.z;

  // Calculate vibration magnitude

  float vibration =
    sqrt(
      ax * ax +
      ay * ay +
      az * az
    );

  // ========================================
  // CURRENT SIMULATION
  // ========================================

  int currentRaw =
    analogRead(CURRENT_PIN);

  float current =
    map(
      currentRaw,
      0,
      4095,
      15,
      35
    );

  current =
    current / 10.0;

  // ========================================
  // RPM SIMULATION
  // ========================================
  
  // For now we generate a realistic RPM
  // value because the IR RPM sensor
  // will be integrated later.

  int rpm =
    random(
      1350,
      1500
    );

  // ========================================
  // DISPLAY DATA
  // ========================================

  Serial.println();
  Serial.println("------------------------------------");

  Serial.print(
    "Temperature : "
  );

  Serial.print(
    temperature
  );

  Serial.println(
    " °C"
  );

  Serial.print(
    "Vibration   : "
  );

  Serial.println(
    vibration
  );

  Serial.print(
    "Current     : "
  );

  Serial.print(
    current
  );

  Serial.println(
    " A"
  );

  Serial.print(
    "RPM         : "
  );

  Serial.println(
    rpm
  );

  // ========================================
  // SEND TO PYTHON
  // ========================================

  if (
    WiFi.status() == WL_CONNECTED
  )
  {
    HTTPClient http;

    http.begin(
      serverURL
    );

    http.addHeader(
      "Content-Type",
      "application/json"
    );

    // -----------------------------
    // Create JSON
    // -----------------------------

    String jsonData =
      "{"
      "\"temperature\":" +
      String(temperature, 2) +
      ","
      "\"vibration\":" +
      String(vibration, 2) +
      ","
      "\"current\":" +
      String(current, 2) +
      ","
      "\"rpm\":" +
      String(rpm) +
      "}";

    Serial.println();

    Serial.println(
      "Sending data to Python..."
    );

    Serial.println(
      jsonData
    );

    // -----------------------------
    // POST request
    // -----------------------------

    int responseCode =
      http.POST(
        jsonData
      );

    Serial.print(
      "HTTP Response: "
    );

    Serial.println(
      responseCode
    );

    // -----------------------------
    // Server response
    // -----------------------------

    if (
      responseCode > 0
    )
    {
      String response =
        http.getString();

      Serial.println(
        "Python Response:"
      );

      Serial.println(
        response
      );
    }
    else
    {
      Serial.println(
        "Failed to contact Python server."
      );
    }

    http.end();
  }
  else
  {
    Serial.println(
      "WiFi disconnected!"
    );
  }

  Serial.println(
    "------------------------------------"
  );

  // Send every 5 seconds

  delay(5000);
}