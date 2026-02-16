# Lejre Fitness Automator

Welcome to the Lejre Fitness Automator project! This project aims to automate internal routines for Lejre Fitness, enhancing efficiency and reducing manual workload.

## Overview

Lejre Fitness Automator is designed to streamline various internal processes, ensuring smooth and efficient operations within the organization.

## Features

- Automates routine tasks
- Enhances operational efficiency
- Reduces manual workload
- **Token Inventory Tracking**: Automated tracking of physical access tokens distributed to members with threshold alerts

## Getting Started

To get started with the project, clone the repository and follow the setup instructions provided in the documentation.

### Token Inventory Tracking

The Token Inventory Tracking system automatically monitors and manages the distribution of physical access tokens to members.

#### Usage

The system can be run using the convenience wrapper script:

```bash
# Start the scheduler (runs daily at configured time)
./run_token_inventory.sh

# Execute token count immediately
./run_token_inventory.sh --run-now

# Check current system status
./run_token_inventory.sh --status

# View execution history
./run_token_inventory.sh --history

# View last 20 executions
./run_token_inventory.sh --history --limit 20

# Enable verbose logging
./run_token_inventory.sh --verbose --run-now
```

Alternatively, you can run the main.py script directly:

```bash
PYTHONPATH=lf-automator python lf-automator/main.py [options]
```

#### Configuration

Configure the system using environment variables in your `.env` file:

```bash
# Token threshold for alerts
TOKEN_THRESHOLD=10

# Email configuration
ALERT_EMAIL_SENDER=noreply@lejrefitness.dk
ALERT_EMAIL_RECIPIENTS=admin@lejrefitness.dk,manager@lejrefitness.dk
ALERT_EMAIL_TEMPLATE=templates/threshold_alert.html

# Schedule (cron format: minute hour day month weekday)
DAILY_COUNT_SCHEDULE=0 9 * * *  # 9 AM daily
DAILY_COUNT_ENABLED=true

# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=lfautomator
DB_USERNAME=your_username
DB_PASSWORD=your_password

# Foreninglet API configuration
API_BASE_URL=https://api.foreninglet.dk
API_USERNAME=your_api_username
API_PASSWORD=your_api_password

# SendGrid API key
SENDGRID_API_KEY=your_sendgrid_api_key
```

## Contributing

We welcome contributions! Please read our contributing guidelines before submitting any changes.

## License

This project is licensed under the MIT License.

---

For more information, please contact the project maintainers.
