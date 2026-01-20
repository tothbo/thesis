# Local server

On-premise gateway of the system. Performs authentication-related tasks (facial recognition, ALPR, QR codes) and bridging tasks for IoT controllers, while maintaining full offline capability.

## Key Features

- **Facial Recognition**: Pre-made DeepFace based user verification and enrollment
- **ALPR**: Custom YOLOv8 model + EasyOCR for license plate recognition
- **Multi-Camera Support**: RTSP stream monitoring and processing
- **Offline-First**: Local PostgreSQL database ensures functionality during network outages
- **Secure Communication**: AMQP (RabbitMQ) RPC and certificate storage
- **Socket Server**: Low-level TCP server (port 25961) for Raspberry Pi Pico W door controllers

## Main components:

- `app/main.py` - RPC server handling authentication requests and user management
- `app/camhandler.py` - Camera monitoring with YOLO-based plate detection
- `app/ddrpc/DDRPC.py` - RPC helper classes for AMQP-based communication
- `app/conn.py` - TCP socket server for door controller communication (QR/face auth)
- `app/db/*` - SQLAlchemy ORM layer with PostgreSQL backend

## License

Licensed under the same terms as the main repository.
