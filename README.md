# Ninja Items App

## Overview

This app is a repair shop inventory management system with a hierarchical structure for components. It includes a Django backend with a Ninja API and a React-like frontend.

## Features

- Hierarchical inventory management
- Item creation with notes and file attachments
- Item movement within the hierarchy
- Item deletion
- Listing creation for items to be sold

## Backend Setup

1. Make sure you have Python and Django installed.
2. Navigate to the project directory.
3. Run `pip install -r requirements.txt` to install the required dependencies.
4. Run `python manage.py createsuperuser createsuperuser`.
5. Run `python  manage.py makemigrations`.
6. Apply the database migrations with `python manage.py migrate`.
7. Start the Django development server with `python manage.py runserver`.

## Frontend Setup

The frontend is a static website that can be served by any web server. You can simply open the `index.html` file in your browser to view the frontend.

## Accessing the App

Once the backend server is running, you can access the API at `http://localhost:8000/api`. The frontend will interact with this API to display and manage the inventory.

## API Endpoints

- `GET /api/items`: Get the full inventory tree
- `GET /api/items/{item_id}`: Get a specific item with its subtree
- `POST /api/items`: Create a new item
- `PUT /api/items/{item_id}/move`: Move an item within the hierarchy
- `DELETE /api/items/{item_id}`: Delete an item
- `POST /api/items/{item_id}/notes`: Add a note to an item
- `POST /api/items/{item_id}/files`: Upload a file to an item