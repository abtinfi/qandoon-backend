# Qandoon Backend

This is the FastAPI backend for the Qandoon project. It provides APIs for managing and interacting with the Qandoon platform.

## Features

- Built with FastAPI for high performance.
- Fully written in Python.
- Dockerized for easy deployment.

## Prerequisites

Make sure you have the following installed:

- Docker
- Docker Compose (if needed)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/abtinfi/qandoon-backend.git
   cd qandoon-backend
   ```

2. If not using Docker, you can manually install dependencies:
   - Create and activate a virtual environment:
     - On macOS/Linux:
       ```bash
       python3 -m venv venv
       source venv/bin/activate
       ```
     - On Windows:
       ```bash
       python -m venv venv
       venv\Scripts\activate
       ```
   - Install the required dependencies:
     ```bash
     pip install -r requirements.txt
     ```

## Environment Variables

Create a `.env` file in the root directory of the project and add the required environment variables. Here is an example:

```
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your_secret_key
DEBUG=True
```

Make sure to replace the values with your actual configuration.

## Running the Application with Docker

1. Build and start the Docker containers:
   ```bash
   docker-compose up --build
   ```

   This will build the Docker image and start the FastAPI backend along with any required services (e.g., database).

2. By default, the application will be accessible at `http://127.0.0.1:8000`.

3. To stop the containers:
   ```bash
   docker-compose down
   ```

## Running the Application Without Docker

1. Start the development server:
   ```bash
   uvicorn main:app --reload
   ```

   By default, the application will be accessible at `http://127.0.0.1:8000`.

## Testing

Run the tests to verify the application:
```bash
pytest
```

## API Documentation

FastAPI provides interactive API documentation out of the box. Once the server is running, you can access it at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Deployment

To deploy the application, you can use services like Docker, AWS, Azure, Google Cloud, or Heroku. Make sure to set up the environment variables and configure the server for production.

### Example using Docker:

1. Build the Docker image:
   ```bash
   docker build -t qandoon-backend .
   ```

2. Run the Docker container:
   ```bash
   docker run -d -p 8000:8000 --env-file .env qandoon-backend
   ```

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

