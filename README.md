# Antigravity System

Project initialized via Antigravity Agent.

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd antigravity_system
    ```

2.  **Environment Setup:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configuration:**

    *   **Environment Variables:**
        Copy `.env.example` to `.env` and add your Google Gemini API Keys (comma-separated).
        ```bash
        cp .env.example .env
        # Edit .env: GOOGLE_API_KEYS="key1,key2,key3"
        ```

    *   **Google Cloud Service Account:**
        Place your `service_account.json` file inside the `config/` folder.  
        *This file is required for Google Sheets access.*

    *   **Site Configuration:**
        Copy `config/sites.json.example` to `config/sites.json` and configure your websites.
        ```bash
        cp config/sites.json.example config/sites.json
        ```
        Update the JSON with your:
        *   Spreadsheet ID
        *   WordPress URL & Credentials (Application Password recommended)
        *   Persona Prompt

## Usage

Run the main script:
```bash
python3 main.py
```

## Security Note
This project maps sensitive files in `.gitignore` to prevent leakage:
*   `.env`
*   `config/service_account.json`
*   `config/sites.json`

