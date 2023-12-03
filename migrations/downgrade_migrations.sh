read -r -p "Where to downgrade to? " downgrade
docker exec saboga-api alembic downgrade "$downgrade"
