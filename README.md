# What is this?
This is "RpgForSocialInteraction", a webapp developed as part of my bachelor's thesis. In essence, it is a fun role-playing game with a bit of social deduction meant to bring people closer together.

# How do i run this?
- `git clone https://github.com/mostghoste/RpgForSocialInteraction`
- `cp .env.example .env`
- In `.env`, configure `DJANGO_SECRET_KEY` to a secure string and add `DEEPSEEK_API_KEY` (optional)
- `docker compose up --build`
- Populate the DB with default characters and questions with `docker compose exec backend python manage.py populate_db` (optional)

# Short Description of the Stack:
## Backend
Django. Python (from python:3), dependencies installed via requirements.txt. Runs on :8000.
## Frontend
Svelte/SvelteKit app built with Node (from node:18-alpine). Frontend implemented with tailwindcss based on original figma designs. The built frontend is served by an Nginx (from nginx:stable-alpine) container. Runs on :3000.
## Orchestration
Docker Compose is used to spin up and manage all of the containers.
