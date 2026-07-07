# 4PROJ – SUPMEAL
# Author : Julien RENOULT
# Promo : PGE.4 - Spé Data
SUPMEAL is a web application developed as part of the **4PROJ** project. 
It provides a modern platform for creating, organizing, and sharing recipes, managing cookbooks, and planning meals.

## 🚀 Tech Stack

### Backend

* Python
* Django
* Django REST Framework
* PostgreSQL
* uv

### Frontend

* Nuxt
* Vue.js
* TypeScript
* Tailwind CSS

### Deployment

* Docker
* Docker Compose

---

## 📁 Project Structure

```text
.
├── backend/
├── frontend/
├── docs/
├── db_postgres/
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── README.md
```

---

## ⚙️ Prerequisites

Before running the project, make sure you have installed:

* Docker
* Docker Compose

---

## 🛠️ Running the Application

Two Docker Compose configurations are available depending on your needs.

### Development Environment

Start the development environment with hot reloading:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Stop the services:

```bash
docker compose -f docker-compose.dev.yml down
```

---

### Production Environment

Start the production stack locally:

```bash
docker compose -f docker-compose.prod.yml up --build
```

Stop the services:

```bash
docker compose -f docker-compose.prod.yml down
```

---

## 🌐 Default Services

| Service     | URL                   |
| ----------- | --------------------- |
| Frontend    | http://localhost:3000 |
| Backend API | http://localhost:8000 |

---

## 📚 Documentation

Project documentation can be found in the `docs/` directory.

---

## 📄 License

This project is developed as part of the **4PROJ** academic project.
