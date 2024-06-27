# Story Image Generator API

## Overview

This project is a Flask-based API designed to process story data, generate visual descriptions, and create images using the MidJourney API. It integrates various custom modules for story generation, visual description configuration, and image prompt generation. The generated images are posted to a webhook and stored in a SQLite database.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/story-image-generator.git
   cd story-image-generator
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   Create a `.env` file in the project root and add the following:

   ```bash
   FLASK_APP=app.py
   FLASK_ENV=development
   MID_API_KEY=your_midjourney_api_key
   ```

5. **Initialize the database:**

   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

## Usage

1. **Run the Flask application:**

   ```bash
   flask run
   ```

2. **API Endpoints:**

   - **Process a Story:**

     ```http
     POST /process-story
     ```

     **Request Body:**

     ```json
     {
       "tripettoId": "unique_tripetto_id",
       "order": "...",
       "story_configuration": "...",
       "visual_configuration": "..."
     }
     ```

   - **Get Story Data:**

     ```http
     GET /get-story-data/<tripetto_id>
     ```

     **Response:**

     ```json
     {
       "tripettoId": "unique_tripetto_id",
       "order": "...",
       "story_configuration": "...",
       "visual_configuration": "...",
       "story": "...",
       "image_urls": "..."
     }
     ```

## Logging

The application uses Python's built-in logging module to log information, warnings, and errors. Logs are displayed in the console.

## Error Handling

Global exception handling is implemented to capture and return JSON error responses.
