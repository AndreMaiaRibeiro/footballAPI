# Premier League Player Search

## Description
This Django web application allows users to search for Premier League players by name. It retrieves player data from a football API, caches the information for performance optimization, and provides a user-friendly interface for searching players.

## Features
- Fetches Premier League teams and players using an external API.
- Caches player data to improve performance.
- Allows users to search for players by name.
- Displays player details including name, team, and position.

## Requirements
- Python 3.x
- Django
- Requests library

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/AndreMaiaRibeiro/footballAPI.git
   cd footballAPI
   ```

2. **Set Up a Virtual Environment (Optional but recommended)**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows use `envScriptsactivate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   Create a `.env` file in the project root directory and add your API keys:
   ```
   FOOTBALL_API_KEY=your_api_key_here
   FOOTBALL_API_URL=https://api.football-data.org/v2
   ```

## Running the Application

1. **Apply Migrations**
   Make sure to apply any database migrations:
   ```bash
   python manage.py migrate
   ```

2. **Run the Development Server**
   Start the Django development server:
   ```bash
   python manage.py runserver
   ```

3. **Access the Application**
   Open your web browser and navigate to:
   ```
   http://127.0.0.1:8000/
   ```

## Usage
- Use the search bar to look for players by name.
- The application will display the players matching your search query.
