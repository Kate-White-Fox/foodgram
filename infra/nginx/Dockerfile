# Этап 1: Сборка фронтенда
FROM node:21.7.1-alpine AS build-stage
WORKDIR /app
# Пути указаны относительно корня проекта (так как context в compose будет ..)
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Этап 2: Прокси и раздача
FROM nginx:1.25.4-alpine
# Копируем конфиг из папки infra
COPY infra/nginx.conf /etc/nginx/conf.d/default.conf
# Копируем статику фронта
COPY --from=build-stage /app/build/ /usr/share/nginx/html/
# Копируем документацию
COPY docs/ /usr/share/nginx/html/api/docs/
