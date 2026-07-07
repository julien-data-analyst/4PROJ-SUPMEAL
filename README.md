# 4PROJ – SUPMEAL

**Author:** Julien RENOULT
**Program:** PGE.4 – Data Specialization

SUPMEAL is a web application developed as part of the **4PROJ** project. It provides a modern platform for creating, organizing, and sharing recipes, managing cookbooks, and planning meals.

---

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

### Development & Deployment

* Docker
* Docker Compose
* Git
* GitHub

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

Before running the project, make sure the following tools are installed:

* Docker
* Docker Compose

---

## 🛠️ Running the Application

Two Docker Compose configurations are available.

### Development Environment

Start the application with:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Stop the application:

```bash
docker compose -f docker-compose.dev.yml down
```

### Production Environment

Start the production stack locally:

```bash
docker compose -f docker-compose.prod.yml up --build
```

Stop the application:

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

## 🌱 Development Workflow

The `develop` branch is the main integration branch. 
Every new feature or bug fix must be developed in a dedicated branch before being merged into `develop`.

### Branch Naming Convention

Branches must follow the format:

```text
<type>(<scope>)/<feature-name>
```

Where:

* `type`

  * `feat` → New feature
  * `fix` → Bug fix

* `scope`

  * Represents the functional area concerned (authentication, recipes, frontend, api, cookbook, etc.)

* `feature-name`

  * A descriptive name using lowercase letters and hyphens.

#### Examples

```text
feat(auth)/oauth-google

feat(recipe)/recipe-creation

feat(cookbook)/cookbook-sharing

fix(api)/recipe-pagination

fix(frontend)/navbar-responsive
```

---

## 📝 Commit Convention

Commits follow the Conventional Commits style:

```text
<type>(<scope>): <description>
```

### Examples

```text
feat(auth): add Google OAuth authentication

feat(recipe): implement recipe creation endpoint

feat(mealplanner): add weekly planning page

fix(frontend): correct mobile navigation layout

fix(api): handle missing recipe image
```

Commit messages should:

* use the imperative mood;
* be concise and descriptive;
* be written in English.

---

## 📚 Documentation

Additional documentation is available in the `docs/` directory.

---

## 📄 License

This project is developed as part of the **4PROJ** academic project.
