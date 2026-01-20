# Global server

Cloud-hosted management platform for multi-site access control. Provides centralized administration, user management, audit logs, and client-facing services including QR code generation and facial data enrollment across distributed local servers.

## Key Features

- **Multi-Site Management**: Centralized administration for multiple physical locations
- **Web Interface**: Jinja2-templated UI for administrators and end-users
- **JWT Authentication**: Token-based user authentication with bcrypt password hashing
- **RPC Orchestration**: AMQP-based distributed communication with local servers
- **User Self-Service**: QR code generation, TOTP setup and facial recognition enrollment
- **Audit & Statistics**: Logging and activity monitoring across all sites

## Main components:

- `app/main.py` - FastAPI web server with authentication and RPC client orchestration
- `app/ddrpc/DDRPC.py` - RPC helper classes for AMQP-based communication
- `app/templates/*` - Jinja2 HTML templates
- `app/static/*`, `app/p_static/*`, `app/u_static/*` - Frontend JavaScript and assets (Bootstrap, jQuery, QR generation)
- `app/db/*` - SQLAlchemy ORM layer with PostgreSQL backend

## License

Licensed under the same terms as the main repository.
