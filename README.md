# Opportunity Tracker API

A FastAPI project for tracking internships, scholarships, bootcamps, hackathons, events, fellowships, volunteer programs, and competitions.

Live API:

```text
https://opportunity-api-9e3a.onrender.com
```

Swagger docs:

```text
https://opportunity-api-9e3a.onrender.com/docs
```

## Features

- List opportunities
- Filter by category, status, organization, location, remote option, tag, and max fee
- Get one opportunity by ID
- Create a new opportunity
- Update an opportunity
- Delete an opportunity
- View basic statistics

## API Endpoints

```text
GET     /
GET     /opportunities
GET     /opportunities/{opportunity_id}
POST    /opportunities
PUT     /opportunities/{opportunity_id}
DELETE  /opportunities/{opportunity_id}
GET     /stats
```

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
uvicorn main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

## Run With Docker

Build the image:

```bash
docker build -t opportunity-api .
```

Run the container:

```bash
docker run -p 8000:8000 opportunity-api
```

Open:

```text
http://localhost:8000/docs
```

## Deployment

This project is deployed on Render using Docker.

Render builds the app from the `Dockerfile` and starts FastAPI with Uvicorn:

```dockerfile
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

## Data Storage

The app stores opportunities in `opportunities.txt`.

For demo projects this is enough, but for production a real database such as PostgreSQL is recommended.
