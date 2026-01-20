# Door Controller

MicroPython firmware for Raspberry Pi Pico W controlling physical door hardware. Handles NFC card reading, QR/face recognition via camera, and relay control with TCP socket communication to the local server.

## Key Features

- **NFC Reading**: PN532 module for NFC card support
- **Camera Integration**: Arducam MEGA 5MP for QR codes and facial recognition
- **Relay Control**: Direct GPIO control for electronic door locks
- **TCP Client**: Socket connection to local server (port 25961) for authentication
- **Fallback Hotspot**: Creates a WiFi access point with custom HTML page for initial configuration

## Main components:

- `main.py` - Main loop handling NFC, camera, relay, and server communication
- `NFC_PN532.py` - PN532 NFC reader driver for SPI interface
- `camera.py` - Arducam MEGA driver and image capture
- `internal_hotspot.py` - WiFi hotspot mode for offline setup
- `config.json` - Hardware pin configuration and feature flags
- `settings.json` - Network credentials and server connection details

## License

Licensed under the same terms as the main repository.
