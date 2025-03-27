# Refirall-Platform

**Refirall-Platform** — это веб-приложение, разработанное с использованием фреймворка Django. Проект включает в себя конфигурацию для развёртывания с помощью Docker и использует Nginx в качестве веб-сервера.

## Начало работы

Следуйте инструкциям ниже для настройки и запуска проекта на вашем локальном компьютере.

### Предварительные требования

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Установка

1. **Клонируйте репозиторий:**

   ```bash
   git clone https://github.com/DeMarkiz/Refirall-Platform.git
   ```

2. **Перейдите в директорию проекта:**

   ```bash
   cd Refirall-Platform
   ```

3. **Создайте файл окружения `.env`:**

   Скопируйте пример файла окружения и при необходимости отредактируйте значения переменных:

   ```bash
   cp .env.example .env
   ```

4. **Постройте и запустите контейнеры:**

   ```bash
   docker-compose up --build
   ```

5. **Примените миграции базы данных:**

   ```bash
   docker-compose exec web python manage.py migrate
   ```

6. **Создайте суперпользователя:**

   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

## Лицензия

Этот проект лицензирован по MIT License. Подробности см. в `LICENSE`.

