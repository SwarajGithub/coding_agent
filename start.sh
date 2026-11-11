#!/bin/bash
set -e

echo "Building and spinning up the Autonomous Coding Agent"
# Force a clean background build cycle
docker compose up --build -d

echo "Deployment Completed!"
echo "• UI interface exposed at http://localhost:3000"
echo "• FastAPI Server exposed at http://localhost:8000"
