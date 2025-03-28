# Приложение URL Shortener (FastAPI/sqlalchemy/fastapi_users/fastapi_cache/postgres/alembic/redis/celery)

## Описание приложения
URL Shortener — это приложение, которое позволяет получать сокращенные URL (alias'ы), переходить по alias'ам (redirect), получать по ним статистику, управлять ими (удаление, изменения ссылок и т.д.). Помимо этого, есть дополнительные функции, которые описаны ниже. Вот основные функции:
  1. Создание коротких URL.
  2. Перенаправление по короткому URL.
  3. Обновление и удаление коротких URL.
  4. Получение статистики по URL
  5. Регистрация и аутентификация пользователей.


## Инструкция по запуску
1. Клонировать репозиторий:
```bash
git clone <repository_url>
cd <repository_directory>
```

2. Убедиться, что была "запуллена" ветка `release` (финальная версия приложения):
```bash
git pull origin release
```

3.Создать файл с секретными данными (пароли, хосты, логины и т.д.) - `.env`.


4. Запустить docker-compose (должен быть установлен docker, docker-compose):
```bash
docker-compose up --build
```

5. Далее, по следующим адресам будет доступно приложение:
   - Само FastAPI приложение: `127.0.0.1:8000`;
   - Dashboard celery: `127.0.0.1:5555`.


## Описание API
API состоит из следующих endpoint'ов:

- **`POST /links/shorten`** - создание alias'оа

- **`GET /links/search`** - поиск alias'а по исходному url

- **`GET /links/{short_code}`** - redirect на исходный url по alias'у;

- **`DELETE /links/{short_code}`** - удаление alias'а из базы данных (доступно только для зарегистрированных/авторизированных пользователей);

-  **`PUT /links/{short_code}`** - изменение alias'а в базе данных (доступно только для зарегистрированных/авторизированных пользователей);

- **`GET /links/{short_code}/stats`** - получение статистики использования ссылки по alias'у;

- **`POST /links/get_QR/`** - получение QR-code для передаваемой ссылки;

- **`POST /links/show_expired_url`** - статистика по ссылкам, срок действия которых истек.

- **GET /links/show_expired_url`** - статистика по ссылкам, срок действия которых истек.

- **POST /auth/jwt/login`** - логин пользователя.

- **POST /auth/jwt/logout`** - логаут пользователя пользователя.

- **POST /auth/register`** - регистрация пользователя.



## Примеры запросов
- Создание alias'а (**`POST /links/shorten`**):
```
{
  "url": "https://en.wikipedia.org/",
  "custom_alias": "wiki",
  "expires_at": "2028-03-28T19:43:54.067Z"
}
```
   
![Снимок экрана 2025-03-28 224419](https://github.com/user-attachments/assets/93694b5a-10e5-405d-914b-f825c291b0cb)
![Снимок экрана 2025-03-28 224423](https://github.com/user-attachments/assets/ee01dbb6-f343-4c40-ad00-7a2270d69af2)


- Redirect на исходный url по alias'у (`GET /links/{short_code}`)
```
http://127.0.0.1:8000/links/wiki
```
![Снимок экрана 2025-03-28 224446](https://github.com/user-attachments/assets/b78914a6-4049-4b91-8b84-e13e1f502e56)


-  Регистрация пользователя:
```
{
  "email": "vadim@example.com",
  "password": "123",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false
}
```
![Снимок экрана 2025-03-28 225203](https://github.com/user-attachments/assets/a4a70da9-c8b9-4b5a-bb4d-9ff93770ffed)


## Описание БД

**`user`**:
  -  `registred_at`: дата и время регистрации;
  -  `id`: первичный ключ пользователя;
  -  `email`: email пользователя;
  -  `hashed_password`: хэшированный пароль;
  -  'is_active': является ли пользователь активным;
  -  `is_superuser`: является ли пользователь суперюзером;
  -  `is_verified`: является ли пользователь суперюзером.


**`url`**:
  - `id`: первичный ключ ссылки;
  - `user_id`: id пользователя, который создал ссылку;
  - `initial_url`: исходный url;
  - `shorten_url`: созданный для исходного url alias;
  - `open_url_count`: количество переходов по  ссылке;
  - `created_at`: дата создания ссылки;
  - `last_used_at`: дата последнего использования ссылки;
  - `expires_at`: дата истечения срока ссылка.


**`history`**:
  - `id`: исходный PK ссылки;
  - `user_id`: идентификатор пользователя, который создал ссылку;
  - `initial_url`: исходный url;
  - `shorten_url`: созданный для исходного url alias;
  - `open_url_count`: количество переходов по  ссылке;
  - `created_at`:  дата создания ссылки;
  - `last_used_at`: дата последнего использования ссылки;
  - `expired_at`: дата истечения срока ссылка.




