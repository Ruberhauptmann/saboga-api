read -r -p "Enter migration message: " message
docker exec saboga-api alembic revision --autogenerate -m "$message"
