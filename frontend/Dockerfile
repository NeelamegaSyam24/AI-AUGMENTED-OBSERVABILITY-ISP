FROM node:22-alpine AS builder

WORKDIR /app
ARG VITE_API_URL=http://localhost:8000
ARG VITE_GRAFANA_URL=http://localhost:3000
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_GRAFANA_URL=${VITE_GRAFANA_URL}
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage - serve with nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
