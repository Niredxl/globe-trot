# Globe Trotter

Globe Trotter is a travel planning application that allows users to create multi-city trips, manage budgets, and discover activities.

## Features

- User Authentication (Sign up, Login)
- Create and manage trips with budget limits
- Interactive Itinerary Builder
- Activity Search
- Public Trip Sharing
- Admin Dashboard

## Tech Stack

- Python (Flask)
- SQLite
- HTML/CSS (Bootstrap 5)

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application locally:

```bash
flask run
```

Access the app at `https://globe-trot.onrender.com/`.

## Deployment

This project is configured for deployment on Render.

**Note:** The application uses SQLite, which does not persist data across restarts on ephemeral file systems like Render. For production use, migrate to a persistent database like PostgreSQL.
