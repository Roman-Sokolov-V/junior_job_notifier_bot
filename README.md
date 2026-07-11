# Junior Job Notifier Bot

A Telegram bot that serves as the user-facing frontend for [**Junior Job Notifier**](https://github.com/Roman-Sokolov-V/junior_job_notifier) — a job vacancy aggregation system originally built for personal use to track openings on individual companies' own career pages, rather than the major job boards where competition for junior roles is fierce. It scrapes listings directly from company sites, stores them in Supabase, and matches them against user-defined search profiles.

While the [main project](https://github.com/Roman-Sokolov-V/junior_job_notifier) handles scraping, storage, and filtering, this bot is where users interact with the system: registering, managing search profiles, and browsing matched vacancies — no separate web frontend required.

## 🚀 Try It Now

👉 [**@junior_job_notifier_bot**](https://t.me/junior_job_notifier_bot) — open in Telegram and press `/start`.

> ⏳ **Note on first response time:** this bot runs on Render's free tier, which spins the service down after 15 minutes of inactivity. If nobody has used the bot recently, **the very first message may take up to ~1 minute to get a reply** while the service wakes up. This is expected — please don't assume the bot is broken if the first response is slow. Every message after that is fast (typically well under a second). See [Deployment](#deployment) for details on why this trade-off was made.

## How It Works

1. A user registers via the bot and creates one or more **search profiles**.
2. Each profile defines filtering criteria (see below).
3. The scraper (in the main project) collects new vacancies daily and filters them against every active profile.
4. Matched vacancies are stored and made available to the user through this bot.

## Features

### Registration & Onboarding
- On `/start`, the bot checks whether the user is already registered.
  - **New user:** prompted to register via a button, then guided through a step-by-step profile setup using `FSMContext`.
  - **Existing user:** shown the main menu keyboard.
- After completing registration, the user is immediately prompted to create their first search profile.

### Main Menu
Available to registered users as a persistent keyboard:
- **Show found vacancies** — browse vacancies matched against the user's active profiles.
- **Add / edit profile** — same step-by-step FSM flow used during onboarding.
- **My profiles** — view all existing search profiles, with an option to delete each one.
- **Delete subscription** — unsubscribe / remove the user's account from the system.

### `/help`
Displays usage instructions.

> All other functionality is handled through inline keyboard callbacks rather than additional bot commands.

### Search Profiles
Users can create an **unlimited number of profiles**. Each profile can combine the following filters, all of which are optional (at least one is required when creating a profile):

| Filter | Behavior |
|---|---|
| **Include keywords** | Rejects vacancies whose title contains *none* of the listed keywords. |
| **Exclude keywords** | Rejects vacancies whose title contains *at least one* of the listed keywords. |
| **AI prompt (semantic matching)** | Vacancies surviving the keyword filters are passed through a neural network for semantic matching against a free-text prompt describing what the user is looking for. |

This layered approach lets users combine cheap, fast keyword filtering with more expensive semantic matching only on the reduced candidate set.

## Tech Stack

- **Python** 3.14+
- **[aiogram](https://docs.aiogram.dev/)** 3.29+ — Telegram Bot framework, using FSM for multi-step flows (registration, profile creation/editing) and middleware-based dependency injection
- **[Supabase](https://supabase.com/)** (`supabase-py` 2.31+) — async Postgres client for user, profile, and vacancy data
- **aiohttp** 3.14+ — webhook server (see [Deployment](#deployment))
- **cachetools** — in-memory caching
- **uv** — dependency management (`pyproject.toml` / `uv.lock`)

## Project Structure

```
junior_job_notifier_bot/
├── src/
│   ├── db/
│   │   └── crud.py              # Supabase CRUD operations
│   ├── handlers/
│   │   ├── start.py             # /start, registration entry point
│   │   ├── not_registered_user.py
│   │   ├── profile.py           # profile creation/editing FSM, deletion
│   │   ├── me.py                # "My profiles" view
│   │   └── vacancies.py         # browsing matched vacancies
│   ├── keyboards/
│   │   └── keyboards.py         # reply & inline keyboards
│   ├── middlewares/
│   │   ├── supabase.py          # injects the Supabase client into handlers
│   │   └── user.py              # injects user data, registration status
│   ├── bot.py                   # Bot/Dispatcher factory, startup/shutdown hooks
│   └── exceptions.py
├── main.py                      # aiohttp webhook server entry point (production)
├── polling_main.py              # long polling entry point (local development only)
├── settings.py                  # environment configuration, logging setup
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

## Architecture Notes

- **Middleware-based DI**: `SupabaseMiddleware` and `UserInjectedMiddleware` inject the Supabase client and current user data into every handler, so handlers can simply declare `db: AsyncClient` or `user_data: dict` as parameters.
- **FSM for multi-step flows**: registration and profile creation/editing use aiogram's `FSMContext` to walk users through multi-step forms via chat.
- **Webhook, not polling**: the bot runs as an aiohttp web server and receives updates via Telegram webhooks rather than long polling — see [Deployment](#deployment) for why.

## Docker

The project includes two Docker images:

| File | Purpose | Entry command |
|---|---|---|
| `Dockerfile` | Production webhook mode | `CMD ["python", "main.py"]` |
| `polling.Dockerfile` | Long polling mode (local development / testing outside Render) | `CMD ["python", "polling_main.py"]` |

`polling.Dockerfile` is identical to the production `Dockerfile` except for the final `CMD`, so both images share the same dependencies and build steps.

**Build and run the production (webhook) image:**

```bash
docker build -f Dockerfile -t junior-job-notifier-bot .
docker run --env-file .env -p 10000:10000 junior-job-notifier-bot
```

Note that, as with running locally without Docker, the webhook image still requires a publicly reachable HTTPS URL to actually receive updates from Telegram.

**Build and run the polling image:**

```bash
docker build -f polling.Dockerfile -t junior-job-notifier-bot-polling .
docker run --env-file .env junior-job-notifier-bot-polling
```

No port mapping is needed for the polling image, since it doesn't run an HTTP server — it connects out to Telegram via `getUpdates` instead.

## Deployment

This bot is deployed on [Render](https://render.com)'s free Web Service tier using **webhooks** instead of long polling.

### Why webhooks?

Render's free tier is designed around HTTP services that spin down after 15 minutes of inactivity and wake up on the next incoming request. Long polling doesn't fit this model well — it requires an always-running background loop with no inbound HTTP traffic to keep the service "awake," and it doesn't play well with Render's rolling deploys (which briefly run old and new instances side by side). Running the bot as a proper `aiohttp` web service listening for Telegram webhook `POST` requests aligns naturally with how Render expects a web service to behave, gets free automatic HTTPS on the `*.onrender.com` domain, and avoids the reconnect/router-conflict issues inherent to restarting a polling loop mid-deploy.

### Required environment variables

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase service/anon key |
| `WEBHOOK_SECRET` | Static secret token used to verify that incoming webhook requests actually originate from Telegram |
| `PORT` | Provided automatically by Render |

> `WEBHOOK_SECRET` must be set explicitly as a fixed environment variable — do not generate it at runtime, or it will differ between deploys/restarts and cause Telegram's webhook requests to be rejected with `401` during rolling deploys.

> ⚠️ **After running the bot locally in polling mode** (e.g. while the Render service was suspended for local testing), Telegram will reject webhook calls until the webhook is re-registered. Render's **"Restart service"** button is *not* reliable for this — in practice it did not trigger a fresh `on_startup` / `set_webhook()` call. Use **Manual Deploy → Clear build cache & deploy** instead, which reliably starts a genuinely new instance.

### Running Locally

> **Note:** this bot depends on a Supabase database populated by the [scraper project](https://github.com/Roman-Sokolov-V/junior_job_notifier). Database credentials are private and not distributed, so cloning this repo alone won't give you a fully working bot — running it locally is mainly useful for reading/reviewing the code and architecture, not for full functional testing. If you'd like to try the bot itself, see [Try It Now](#-try-it-now) above.

For contributors with their own Supabase setup:

```bash
uv sync
cp .env.example .env  # fill in your own Supabase project + bot token
uv run polling_main.py
```

`polling_main.py` runs the bot in long polling mode, avoiding the tunneling setup that webhook mode would otherwise require locally. See [Docker](#docker) for containerized alternatives.

## Related Projects

- [**junior_job_notifier**](https://github.com/Roman-Sokolov-V/junior_job_notifier) — the scraping and matching engine this bot serves as a frontend for.

## License

This project is open-source and available under the [MIT License](LICENSE).

## Contact & Connect

If you have any questions, suggestions, or would like to collaborate on this project, feel free to reach out:

- **Telegram:** [@Roman_Sokolo_v](https://t.me/Roman_Sokolo_v)
- **LinkedIn:** [roman-sokolov](https://www.linkedin.com/in/roman-sokolov-a7614330b/)
- **Email:** roman.sokolov.developer@gmail.com
