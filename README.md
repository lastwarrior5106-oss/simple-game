# Row Match AI Backend (FastAPI + React + AI Agents)

A game backend system enhanced with an AI agent that can dynamically execute backend operations.

This project combines:

* A **classic REST API**
* An **AI system that calls endpoints automatically**

---

## 🚀 Overview

This project was built to explore:

* AI + Backend integration
* Tool-using AI systems
* Scalable backend architecture

👉 Users can:

* Use API normally (register/login)
* Or interact with AI and let it handle operations

---

## 🤖 AI System

The AI allows users to perform backend actions using natural language.

### Example:

```text
"Create a user and level it up twice"
"Create a team and join it"
```

👉 AI will:

1. Understand the request
2. Decide which endpoints to call
3. Execute them in order
4. Return a human-readable response

---

## 🧠 Architecture

```text
User → AI Router → Supervisors → Tools (API) → Response
```

### Components

* **Router**

  * Interprets user intent
  * Plans execution steps

* **Supervisors**

  * Users Supervisor → user operations
  * Teams Supervisor → team operations

* **Tools**

  * Backend endpoints wrapped as callable functions

* **Responder**

  * Explains results to the user

👉 AI does NOT replace backend
👉 It uses backend as a tool layer

---

## 🔐 Authentication

Normal authentication system (not AI-driven)

### Register

```
POST /auth/register
```

### Login

```
POST /auth/login
```

### Other

* `PUT /auth/change-email`
* `PUT /auth/change-password`

---

## 👤 User Endpoints

* `GET /user/`
* `POST /user/`
* `PUT /user/{user_id}/level-up`
* `GET /user/me`
* `DELETE /user/me`
* `DELETE /user/{user_id}`
* `PATCH /user/{user_id}/coins`

---

## 👥 Team Endpoints

* `POST /team/`
* `POST /team/{team_id}/join`
* `POST /team/leave`
* `POST /team/{team_id}/leave/{target_user_id}`
* `GET /team/suggested`
* `DELETE /team/{team_id}`

---

## 🤖 AI Endpoints

* `POST /ai/chat`
* `POST /ai/chat/stream`

👉 AI uses backend endpoints internally

---

## 🏗️ Project Structure

```text
backend/
├── src/
│   ├── controllers/
│   ├── services/
│   ├── database/
│   ├── models/
│   ├── routers/
│   ├── utils/
│   ├── ai/
│   └── middlewares/
├── tests/
├── alembic/
├── docker-compose.yml
```

Frontend:

```text
frontend/
├── src/
│   ├── pages/
│   ├── components/
│   ├── api/
│   └── context/
```

---

## ⚙️ Run Project

### Backend

```bash
uvicorn main:app --reload
```

### Frontend

```bash
npm install
npm run dev
```

---

## ⚠️ Important Note

Database seeding is disabled:

```python
# await seed_database()
```

Because it resets the database on every restart.

---

## 🧪 Additional Features

* Database migrations (Alembic)
* Automated tests (pytest)
* Docker support (docker-compose)
* AI tool execution layer (MCP server)

---

## 🧠 Tech Stack

* FastAPI
* SQLModel
* PostgreSQL
* JWT Authentication
* Passlib (bcrypt)
* React + Vite
* AI Agent Architecture (LangGraph-style)

---

## 👨‍💻 Contributors

* Süleyman Emre Sarılı
* Mustafa Can Eke

---

## 🎯 Purpose

This project demonstrates:

* AI systems that use tools (API endpoints)
* Backend-driven AI execution
* Modular and scalable architecture

---

## 🚀 Future Improvements

* Parallel AI execution
* Tool registry system
* Advanced monitoring
* Production deployment pipeline

---
