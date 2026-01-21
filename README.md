# MyFortress

## Overview
MyFortress is a Python-based service that acts as a bridge between home automation devices, cloud APIs, and the central automation suite. It provides secure, extensible connectors for smart home integration and automation.

## Guild Workflow
- Quest template: https://github.com/Aarogaming/AaroneousAutomationSuite/blob/main/guild/QUEST_TEMPLATE.md
- Protocol: https://github.com/Aarogaming/AaroneousAutomationSuite/blob/main/docs/GUILD_PROTOCOL.md

## Features
- Connects to a variety of smart home devices and APIs
- Secure local and remote communication
- Extensible plugin system for new device types
- REST and/or MQTT API for integration

## Getting Started

### Prerequisites
- Python 3.12+
- (Optional) Docker for containerized deployment
- See `.env.example` for required environment variables

### Setup
1. Clone the repository and navigate to the MyFortress directory.
2. Create and activate a Python virtual environment:
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in required secrets.
5. Run the gateway service:
   ```sh
   python main.py
   ```

## Usage
- Configure device connectors in the `config/` directory.
- Use the REST or MQTT API to interact with connected devices.
- See the `docs/` folder for advanced configuration and integration guides.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License
MIT
