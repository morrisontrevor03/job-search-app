# Multi-stage build for Job Search Application
FROM node:18-alpine AS frontend-build

# Build frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Python backend stage
FROM python:3.11-slim AS backend

# Install Python dependencies
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY .env ./

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./static

# Expose port
EXPOSE 8000

# Start the application
WORKDIR /app/backend
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
