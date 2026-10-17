# Docker – DevOps Assignment

**Student:** Samriddhi Mishra
**GitHub repository:** https://github.com/samriddhi0604/Docker_Samriddhi_Mishra
**Docker Hub images:** `samriddhi0604/docker-assignment-frontend` and `samriddhi0604/docker-assignment-backend`

A full-stack application containerised with Docker:

- **frontend/** – Node.js + Express. Shows a course registration form (like Flask Assignment 2) and sends each submission to the backend.
- **backend/** – Flask. Validates and processes the form data and stores it (MongoDB if `MONGO_URI` is set, otherwise a JSON file in a Docker volume).
- **docker-compose.yml** – runs both containers on the same network (`app-network`). The frontend reaches the backend at `http://backend:5000` using the Compose service name.

## Project structure

```
Docker_Samriddhi_Mishra/
├── backend/
│   ├── app.py              # Flask API: /submit, /submissions, /api, /health
│   ├── data.json
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── frontend/
│   ├── server.js           # Express server: form, forwards to Flask
│   ├── views/index.ejs     # form page (shows errors)
│   ├── views/success.ejs   # "Data submitted successfully"
│   ├── public/style.css
│   ├── package.json / package-lock.json
│   ├── Dockerfile
│   └── .dockerignore
├── docker-compose.yml
├── .github/workflows/docker-publish.yml   # CI: build, test and push to Docker Hub
└── .gitignore              # node_modules, .vscode, __pycache__, .env ...
```

## Run with Docker Compose

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend:  http://localhost:5000/health · http://localhost:5000/submissions

## Run the published images from Docker Hub

```bash
samriddhi0604NAME=samriddhi0604 docker compose pull
samriddhi0604NAME=samriddhi0604 docker compose up
```

## Routes

| Service | Route | Method | Description |
|---|---|---|---|
| frontend | `/` | GET | Form page |
| frontend | `/submit` | POST | Sends the form to Flask; redirects to `/success` or shows the error on the same page |
| frontend | `/success` | GET | "Data submitted successfully" |
| frontend | `/health` | GET | Checks the connection to the backend |
| backend | `/submit` | POST | Validates, processes and stores a submission (JSON) |
| backend | `/submissions` | GET | All stored submissions |
| backend | `/api` | GET | JSON list from `data.json` |
| backend | `/health` | GET | Health check used by Docker Compose |

## CI / Docker Hub

`.github/workflows/docker-publish.yml` runs on every push to `main`: it builds both images with
`docker compose build`, starts them with `docker compose up -d`, tests the form flow end to end,
and pushes both images to Docker Hub with `docker compose push`.
