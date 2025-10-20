# Discord Support Bot

A Discord bot with ticket system and member management features.

## Features

- 🎫 Ticket System
  - Create support tickets
  - Private channels for each ticket
  - Ticket transcripts
  - Staff management

- 👥 Member Management
  - Member list with status
  - Role statistics
  - Online member tracking

## Setup

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Create a .env file with your Discord token:
```
DISCORD_TOKEN=your_token_here
```

3. Run the bot:
```bash
python start.py
```

## Commands

- `!setup-tickets` - Set up the ticket system (Admin only)
- `/membres` - View member statistics

## Configuration

- Create a "Staff" role for ticket management
- Tickets are created in a "Support Tickets" category

## Hosting

The bot can be hosted 24/7 using:
- Railway
- Oracle Cloud
- VPS services