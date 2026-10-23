# Умный кабинет предпринимателя by "Питон и Слоник"

> Описание будет скоро

## Развертывание на удаленном сервере

Развертывание данного проекта для большей совместимости построено на базе файловой системы Linux. 
Для того чтобы развернуть данный проект локально в ОС Windows, используйте WSL или иную ВМ с установленными Docker и Mutagen.

### 0. Создание ssh-конфига

Сгенерируйте ssh-ключ без passphrase и добавте `key.pub` часть ключа на сервер в `~/.ssh/authorized_keys`

Для работы Docker Context и синхронизации через Mutagen настройте подключение к серверу по SSH-ключу в `~/.ssh/config`:

```sshconfig
Host domain.ru
    HostName domain.ru
    User root
    IdentityFile ~/.ssh/your_secret_key
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 10m
    ServerAliveInterval 30
    ServerAliveCountMax 3

```

Проверьте подключение без пароля:
```sh
ssh root@domain.ru
```

### 1. Настройка Docker-контекста

Создайте удаленный Docker-контекст, который позволит выполнять команды `docker compose` с вашей машины напрямую на удаленном сервере по SSH:

```sh
docker context create domain.ru --docker "host=ssh://root@domain.ru"
```

Проверьте список контекстов:
```sh
docker context ls
```

### 2. Создание environment-файлов для сервисов

В корне проекта и в директориях сервисов создайте `.env` (для prod и общей инфраструктуры) и `.env.dev` (для dev-окружения) на основе примеров `.env.example`:

```sh
cp .env.example .env
cp backend/.env.example backend/.env
cp backend/.env.example backend/.env.dev
cp backend-ml/.env.example backend-ml/.env
cp backend-ml/.env.example backend-ml/.env.dev
cp frontend/.env.example frontend/.env
cp frontend/.env.example frontend/.env.dev
```

В корневом `.env` укажите домен и имя созданного Docker-контекста. 
Если `DOCKER_CONTEXT` бедет пустым, то все будет запускаться в локальном контексте `default`:

```dotenv
DOMAIN="domain.ru"
DOCKER_CONTEXT="domain.ru"

MARIADB_TAG="13.0.2"
MARIADB_USER="username"
MARIADB_BUFFER_POOL="512M"
```

Также в `.config/secrets` создайте фалы `mariadb_root_password` и `mariadb_password`. А в папку `.config/nginx/certs` положите файлы сертификаты (`fullchain.pem` и `privkey.pem`) для домена `*.domain.ru` (wildcard-сертификат). При локальном развертывании используйте самоподписанные сертификаты.

> Если вы подключаетесь к уже настроенному серверу, где `.env` и `.env.dev` уже лежат в `/opt/alfa/enviroment/`, вы можете пропустить ручное заполнение, так как эти файлы автоматически загрузятся с сервера.

### 3. Запуск синхронизации файлов

Синхронизация конфигураций и `.env`-файлов с сервером работает в двустороннем режиме через **Mutagen**:
- `./.config` ↔ `/opt/alfa` (конфиги Nginx, инициализация БД, миграции и секреты. Папка `enviroment` исключена из `.config`)
- `./` (`.env`, `.env.dev`) ↔ `/opt/alfa/enviroment/root`
- `./backend` (`.env`, `.env.dev`) ↔ `/opt/alfa/enviroment/backend`
- `./backend-ml` (`.env`, `.env.dev`) ↔ `/opt/alfa/enviroment/backend-ml`
- `./frontend` (`.env`, `.env.dev`) ↔ `/opt/alfa/enviroment/frontend`

Для запуска всех сессий синхронизации и открытия монитора выполните:
```sh
make sync
```

Управление синхронизацией:
- `make sync-status` — показать статус всех сессий синхронизации
- `make sync-monitor` — открыть live-монитор всех сессий (`Ctrl+C` для выхода из монитора, без прерывания синхронизации)
- `make sync-restart` — перезапустить все сессии синхронизации
- `make sync-stop` — остановить и удалить сессии синхронизации

### 4. Запуск базовой инфраструктуры

Инфраструктура автоматически запускается перед `make dev*` и `make prod*`, но её можно поднять или остановить и отдельно:

```sh
# Запуск БД
make infra

# Остановка БД
make infra-down
```

### 5. Запуск dev-версии

> Если вы не собираетесь производить отладку и изменение кода в реальном времени, переходите к п.6.

Для запуска **всего** dev-окружения сразу с автоматической синхронизацией кода (`watch`):

```sh
make dev
```

Для **параллельной разработки отдельных сервисов** разными разработчиками:

```sh
make dev-back     # только backend-dev
make dev-front    # только php-frontend-dev
make dev-ml-back  # только backend-ml-dev
```

Остановка dev-окружения:
```sh
make dev-down
```

Dev-версия будет доступна по адресу `https://dev.domain.ru`.

### 6. Запуск и сборка Prod-версии (продакшн)

Сборка и деплой происходят напрямую через удаленный контекст:

```sh
# Собрать и запустить все сервисы в продакшне
make prod
```

Остановка prod-окружения:
```sh
make prod-down
```

Prod-версия будет доступна по адресу `https://app.<DOMAIN>`, включая редирект с корневого `https://domain.ru` и принудительное включение `http://domain.com` 304 -> `https://app.domain.ru`.

### 0.1. Дополнительные скрипты (Makefile)

#### Управление контейнером реверс-прокси(Nginx) (использует `DOCKER_CONTEXT` и `DOMAIN` из корневого `.env`):
- `make nginx-up` — запустить Nginx
- `make nginx-stop` — остановить Nginx
- `make nginx-down` — остановить и удалить контейнер Nginx
- `make nginx-restart` — перезапустить контейнер Nginx
- `make nginx-hard-restart` — полностью пересоздать контейнер Nginx
- `make nginx-reload` — пересобрать шаблоны конфигов с переменной `${DOMAIN}` и перезагрузить конфигурацию Nginx без даунтайма
- `make nginx-test` — пересобрать шаблоны и проверить синтаксис конфигов (`nginx -t`)
- `make nginx-logs` — просмотр логов Nginx в реальном времени
- `make nginx-shell` — открыть `sh` внутри контейнера Nginx
- `make nginx-status` — статус контейнера Nginx
- `make nginx-rebuild` — пересобрать и перезапустить Nginx

## Локальный запуск

Для работы полностью локально (без удаленного сервера):
1. В корневом `.env` оставьте `DOCKER_CONTEXT=""` (по умолчанию будет использован локальный контекст `default`).
2. Скопируйте содержимое `./.config` в `/opt/alfa` (или настройте локальные пути) и заполните `.env` / `.env.dev` в папках сервисов.
3. Запустите инфраструктуру и нужное окружение:
    ```sh
    make prod
    ```
    > Локальное развертывание тестируется и не гарантируется полноценная совместимость 

> Разработано и придумано @shtrmx @st0rmeed @artemepp @YarKhim @Nikola-san в 2026 году