@echo off
echo Building Job Search Application for UAT...

echo Step 1: Building Docker image...
docker build -t jobsearch-uat .

echo Step 2: Stopping any existing containers...
docker-compose down

echo Step 3: Starting UAT environment...
docker-compose up -d

echo Step 4: Waiting for application to start...
timeout /t 10

echo UAT deployment complete!
echo Application available at: http://localhost:8000
echo.
echo To view logs: docker-compose logs -f
echo To stop: docker-compose down
pause
