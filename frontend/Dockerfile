# Base install composer and php
ARG PHP_VERSION=8.4
FROM php:${PHP_VERSION}-cli AS base

ARG PHP_EXTENSIONS="intl zip opcache pcntl pdo_mysql redis swoole"

RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/mlocati/php-extension-installer /usr/bin/install-php-extensions /usr/local/bin/
COPY --from=composer:2 /usr/bin/composer /usr/local/bin/composer

RUN install-php-extensions ${PHP_EXTENSIONS}

WORKDIR /app

ENV COMPOSER_ALLOW_SUPERUSER=1
ENV COMPOSER_NO_INTERACTION=1
ENV COMPOSER_CACHE_DIR=/root/.cache/composer

COPY composer.json composer.lock ./

# Running app for develop in live-mode
FROM base AS development

ENV PHP_CLI_SERVER_WORKERS=4

RUN cp "$PHP_INI_DIR/php.ini-development" "$PHP_INI_DIR/php.ini"

RUN --mount=type=cache,target=/root/.cache/composer \
    composer install --no-scripts --no-autoloader

COPY . .

RUN --mount=type=cache,target=/root/.cache/composer \
    composer dump-autoload --no-scripts \
    && php artisan package:discover --ansi \
    && php artisan filament:assets

EXPOSE 8000

CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8000", "--no-reload"]

# Deploying at production server
FROM base AS prod

RUN cp "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

RUN --mount=type=cache,target=/root/.cache/composer \
    composer install --no-dev --no-scripts --no-autoloader

COPY . .

RUN --mount=type=cache,target=/root/.cache/composer \
    composer dump-autoload --no-dev --optimize --classmap-authoritative --no-scripts \
    && mkdir -p storage/framework/cache/data storage/framework/sessions storage/framework/views storage/logs bootstrap/cache \
    && php artisan package:discover --ansi \
    && php artisan filament:assets \
    && chown -R www-data:www-data storage bootstrap/cache public

USER www-data

EXPOSE 8000

CMD ["sh", "-c", "php artisan optimize && exec php artisan octane:start --server=swoole --host=0.0.0.0 --port=8000 --workers=auto --task-workers=auto --max-requests=500"]