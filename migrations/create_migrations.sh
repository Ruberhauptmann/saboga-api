read -r -p "Enter migration message: " message
docker exec -w /app/migrations saboga-api alembic revision --autogenerate -m "$message"
