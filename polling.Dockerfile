FROM ghcr.io/astral-sh/uv:python3.14-alpine3.23

#  додаю юзера

#RUN useradd -m -u 1000 user
RUN adduser -D -u 1000 user

# Працюємо в папці /app
WORKDIR /app
RUN chown user:user /app

# Оптимізація uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV PATH="/app/.venv/bin:$PATH"

# Кешування та встановлення залежностей
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project


# Копіюємо код одночасно надавая права поточному юзеру
COPY --chown=user:user . /app

# Фінальна синхронізація проєкту
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked


# Запуск бота
CMD ["python", "polling_main.py"]




