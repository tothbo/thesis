# Thesis: Intelligent Access Control and Security System (Szakdolgozat: Intelligens beléptető- és biztonsági rendszer)

The thesis work is about a distributed system built using Raspberry Pi Picos and Python/JavaScript. The system supports entries using various methods: NFC cards, QR codes, ALPR and face recognition. The system was designed around a SOHO environment and offline-capability - while maintaining availability from anywhere.

_Note: The thesis documentation is in Hungarian, but the user interface and system logic are in English. Some legacy code comments or variables may still contain Hungarian terms._

## Architecture

The project is built on a "Local-First" distributed architecture, ensuring the system remains fully functional even during internet outages.

- **Global Server (Cloud):** For administrators it provides the possibility to oversee multiple sites, manage users, and audit logs. For clients this provides a way to open face data, get QR codes for entry etc.
- **Local Server (Locally):** Functions as a gateway, located on-site. It handles computationally expensive tasks like Face Recognition and ALPR using OpenCV and a custom-trained YOLOv8 model, and maintains a local PostgreSQL database. Communicates with the global server via RabbitMQ's AMQP protocol.
- **Door Controller (IoT device):** Built on the **Raspberry Pi Pico W**, this unit handles physical hardware interfacing (relays, sensors) and provides credential reading (NFC/QR) capeabilities.

## Technologies used

- **Languages:** Python, MicroPython
- **Frameworks:** FastAPI, Jinja2 (Frontend), SQLAlchemy
- **Infrastructure:** RabbitMQ, PostgreSQL, Docker
- **AI/CV:** OpenCV, ALPR (YOLOv8 model and implementation)
- **Hardware:** Raspberry Pi Pico W, Arducam MEGA 5MP, PN532 NFC module

## Repository Structure

This repository is a monorepo containing the three core sub-projects:

- `/global_server` – Cloud management platform and master API.
- `/local_server` – Edge computing logic, AI models, local services and database.
- `/door_controller` – IoT firmware for the Raspberry Pi Pico W.

## Academic Background

- **Author:** Botond Tóth
- **Institution:** ELTE Faculty of Informatics, Department of Information Systems - Budapest
- **Year:** 2025

The full thesis documentation (in Hungarian) is available in the repository:
[View thesis PDF](./docs/szd_public.pdf)

## Licenses

Licensed under the MIT License - See [LICENSE](./LICENSE) file for details.

### Third-Party Dependencies and Acknowledgments

This project uses the following libraries and components:

**Python Libraries (Local Server):**

- [DeepFace](https://github.com/serengil/deepface) - MIT License
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - AGPL-3.0 License
- [OpenCV](https://opencv.org/) - Apache 2.0 License
- [FastAPI](https://github.com/tiangolo/fastapi) - MIT License
- [SQLAlchemy](https://www.sqlalchemy.org/) - MIT License
- [aio-pika](https://github.com/mosquito/aio-pika) - Apache 2.0 License
- [Pydantic](https://github.com/pydantic/pydantic) - MIT License
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - Apache 2.0 License
- [PyOTP](https://github.com/pyauth/pyotp) - MIT License

**Python Libraries (Global Server):**

- [Uvicorn](https://www.uvicorn.org/) - BSD-3-Clause License
- [PyJWT](https://github.com/jpadilla/pyjwt) - MIT License
- [Jinja2](https://palletsprojects.com/p/jinja/) - BSD-3-Clause License
- [Passlib](https://pypi.org/project/passlib/) - BSD License

**MicroPython Libraries (Door Controller):**

- [NFC_PN532_SPI](https://github.com/Carglglz/NFC_PN532_SPI) by Carlos Gil Gonzalez - Based on Adafruit PN532 library
- Arducam MEGA camera driver - Arducam

**Infrastructure:**

- [PostgreSQL](https://www.postgresql.org/) - PostgreSQL License
- [RabbitMQ](https://www.rabbitmq.com/) - Mozilla Public License 2.0
- [Docker](https://www.docker.com/) - Apache 2.0 License

**Frontend Libraries:**

- [Bootstrap](https://getbootstrap.com/) - MIT License
- [jQuery](https://jquery.com/) - MIT License
- [QRCode.js](https://davidshimjs.github.io/qrcodejs/) - MIT License

All trademarks and product names are the property of their respective owners.
