# Product Overview

Lejre Fitness Automator is an internal automation system for Lejre Fitness that streamlines routine operational tasks.

## Core Functionality

- **Token Pool Management**: Manages access token pools with tracking and threshold monitoring
- **Email Notifications**: Sends automated emails via SendGrid for alerts and notifications
- **Database Operations**: PostgreSQL-based data persistence for token pools and history
- **Foreninglet Integration**: Integrates with Foreninglet API for member and activity management

## Key Modules

- `automator`: Core automation logic with token counting and threshold alerts
- `database`: PostgreSQL connection and query execution
- `mailer`: SendGrid email delivery
- `tokenpools`: Token pool creation, tracking, and management with database persistence
- `token`: A physical token used to open a door, given to each member to get in out of hours
