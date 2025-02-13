<h1 align="center">Let's Start</h1>

<p align="center">
Welcome to the "Waffle Moderator" project! 🚀
</p>

---

## A Note from the Developer

Before diving into the details, I’d like to clarify that I’m not a professional web developer. I learned SQLAlchemy and Quart while creating this bot, so it may not be perfect. However, I’m proud to present one of the first fully functional Telegram moderation bots available on GitHub!

---

## Features

- Moderation tools such as Mute, Ban, Kick, and Reports (Warn is coming soon).
- Management through an integrated website interface.
- Additional features that are better discovered at runtime for security reasons.


<h1 align="center">Delpoy to your device</h1>

## Repository Setup

Follow these steps to clone the repository and set up the environment:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/aleksfolt/Waffle-Moderator.git
   cd Waffle-Moderator

2. **Create a Virtual Environment:**
    ```bash
    # On Linux/macOS:
    python3 -m venv venv
    
    # On Windows:
    python -m venv venv

3. **Activate the Virtual Environment:**
    ```bash
    # On Linux/macOS:
    source venv/bin/activate
    
    # On Windows:
    venv\Scripts\activate
    
4. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt

## Telegram

1. **Create a Bot**:  
   - Go to [BotFather](https://t.me/BotFather) on Telegram and create a new bot.  
   - Copy the token provided by BotFather after creating the bot.

2. **Set the Webhook URL**:  
   - In BotFather, use the `/setdomain` command to set the webhook URL for your bot.
   - Choose your bot and provide your domain (e.g., `https://yourdomain.com`).

3. **Configure Your Bot**:  
   - Open the `config.py` file in the project.
   - Paste your bot token into the `BOT_TOKEN` variable.
   - Optionally, change the bots name by modifying the `BOT_NAME` variable.

## Database Setup

To deploy the bot, you need to set up a PostgreSQL database. Follow these steps:

1. **Install PostgreSQL (if not already installed):**
   ```bash
   # On Ubuntu/Debian:
   sudo apt update
   sudo apt install postgresql postgresql-contrib

   # On macOS (via Homebrew):
   brew install postgresql

   # On Windows:
   # Download and install PostgreSQL from https://www.postgresql.org/download/
   
 2. **Start PostgreSQL Service:**
    ```bash
    # On Ubuntu/Debian:
    sudo service postgresql start
    
    # On macOS:
    brew services start postgresql

3. **Create the Database and User:**
    ```bash
    # Access the PostgreSQL shell as the postgres user:
    sudo -u postgres psql
    
    # Inside the PostgreSQL shell, run the following commands:
    CREATE DATABASE waffledb;
    CREATE USER waffle WITH PASSWORD 'FromSiberiaLove';
    GRANT ALL PRIVILEGES ON DATABASE waffledb TO waffle;
    
    # Exit the PostgreSQL shell:
    \q

4. **Check conetction:**
    ```bash
    psql -h localhost -U waffle -d waffledb

5. **Optional Configuration:**
If you prefer to use different database credentials, update the following values in the config.py file:
    ```python
    DATABASE_URL = (
        "postgresql+asyncpg://waffle:FromSiberiaLove@localhost:5432/waffledb"
    )
    
    
## Start Bot

**Well, everything is ready! Now let's launch the bot:**
   ```python
    # On Linux/MacOs
    python3 main.py
    
    # On Windows
    python main.py
```

Notes for Shindows Users

- Filesystem Differences:

The bot may not work correctly on Windows due to differences in the filesystem and path handling. For the best experience, consider using a Linux-based environment or tools like [WSL (Windows Subsystem for Linux).](https://learn.microsoft.com/en-us/windows/wsl/)

- Database Connection:

Ensure PostgreSQL is properly configured and accessible on Windows. Use the connection details specified in the `config.py` file

---

![Alt](https://repobeats.axiom.co/api/embed/22bdbb27a62c696b0facf970435df34132dc6405.svg "Repobeats analytics image")
