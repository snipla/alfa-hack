#!/bin/bash
set -e

mariadb -u root -p"$(cat "$MARIADB_ROOT_PASSWORD_FILE")" <<-EOSQL
    CREATE DATABASE IF NOT EXISTS \`alfa_prod\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE DATABASE IF NOT EXISTS \`alfa_dev\`  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

    GRANT ALL PRIVILEGES ON \`alfa_prod\`.* TO '${MARIADB_USER}'@'%';
    GRANT ALL PRIVILEGES ON \`alfa_dev\`.*  TO '${MARIADB_USER}'@'%';
    FLUSH PRIVILEGES;
EOSQL
