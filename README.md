---
title: Junior Job Notifier Bot
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---



# junior_job_notifier_bot

An asynchronous Telegram bot that serves as the user interface for the **[junior_job_notifier](https://github.com/YOUR_GITHUB_USERNAME/junior_job_notifier)** ecosystem. It allows job seekers to register, configure their job search filters, and manage their subscriptions.

---
# The project is under development, everything that is below is only plans for now



## 🏗️ System Architecture & Ecosystem Context

This repository is a **microservice** designed with loose coupling and separation of concerns in mind. It does not handle heavy cron jobs or web scraping; instead, it focuses purely on user interaction and data ingestion.

* **The Main Service (`junior_job_notifier`):** Periodically scrapes job boards, processes new vacancies, and dispatches daily alerts to active users based on their preferences.
* **This Service (`junior_job_notifier_bot`):** Handles incoming Telegram webhooks, automates user registration, and updates search filters (city, keywords, experience, etc.) in the shared database.
* **Shared Infrastructure:** Both services communicate seamlessly through a single, centralized **Supabase (PostgreSQL)** database.

---

## 🛠️ Tech Stack

* **Language:** Python 3.11+
* **Bot Framework:** [Aiogram 3.x](https://github.com/aiogram/aiogram) (Fully asynchronous, featuring FSM and custom Middlewares)
* **Web Framework:** [FastAPI](https://github.com/fastapi/fastapi) (Acts as the webhook receiver endpoint)
* **Database Client:** Supabase Python SDK
* **Deployment:** Serverless via **Vercel** (Cloud Functions)
* **Containerization:** Docker & Docker Compose (For local development and testing)

---

## 🚀 Key Features Demonstrated

1.  **Serverless Webhook Architecture:** Instead of using resource-heavy Long Polling, the bot utilizes event-driven Webhooks integrated with FastAPI, making it fully compatible with free serverless platforms (like Vercel) with zero downtime.
2.  **Automated User Ingestion:** Implements custom `OuterMiddleware` in `aiogram` to check user registration status in Supabase on every interaction, instantly creating a database record for new users.
3.  **Advanced Finite State Machine (FSM):** Provides a seamless, step-by-step interactive configuration dialogue using Inline Keyboards to collect precise vacancy filters from the user.

---

## 💻 Local Setup & Development

### Prerequisites
* Docker and Docker Compose installed **OR** Python 3.11+
* A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
* Access keys to your existing `junior_job_notifier` Supabase instance

### Configuration
1. Clone the repository:
   ```bash
   git clone [https://github.com/YOUR_GITHUB_USERNAME/junior_job_notifier_bot.git](https://github.com/YOUR_GITHUB_USERNAME/junior_job_notifier_bot.git)
   cd junior_job_notifier_bot