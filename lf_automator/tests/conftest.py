"""Fixtures for the tests."""

import os
from pathlib import Path

import pytest
from lf_automator.automator.database.db import Database
from dotenv import load_dotenv
from testcontainers.postgres import PostgresContainer

# Load environment variables from .env file
load_dotenv()

script1 = (
    Path(__file__).parent.parent
    / "db-automator/migrations/V001_20241013143045__carstenskov.sql"
)

script2 = (
    Path(__file__).parent.parent
    / "db-automator/migrations/V002_20250118000000__token_inventory_tracking.sql"
)


postgres = PostgresContainer("postgres:16-alpine")
postgres.with_volume_mapping(
    host=str(script1), container=f"/docker-entrypoint-initdb.d/{script1.name}"
)
postgres.with_volume_mapping(
    host=str(script2), container=f"/docker-entrypoint-initdb.d/{script2.name}"
)


@pytest.fixture(scope="module", autouse=True)
def setup(request):
    postgres.start()

    def remove_container():
        postgres.stop()

    request.addfinalizer(remove_container)
    os.environ["DB_CONN"] = postgres.get_connection_url()
    os.environ["DB_HOST"] = postgres.get_container_host_ip()
    os.environ["DB_PORT"] = postgres.get_exposed_port(5432)
    os.environ["DB_USERNAME"] = postgres.username
    os.environ["DB_PASSWORD"] = postgres.password
    os.environ["DB_NAME"] = postgres.dbname


@pytest.fixture()
def db_connection():
    """Fixture to get the database credentials from the environment."""
    db = Database()
    db.create_connection()
    yield db
    db.close()


# def db_credentials():
#     """Fixture to get the database credentials from the environment."""
#     creds = {
#         "host": os.environ.get("DB_HOST"),
#         "port": os.environ.get("DB_PORT"),
#         "database": os.environ.get("DB_NAME"),
#         "user": os.environ.get("DB_USERNAME"),
#         "password": os.environ.get("DB_PASSWORD"),
#         "connection_url": os.environ.get("DB_CONN"),
#     }
#     return creds


# @pytest.fixture()
# def db_connection(db_credentials):
#     db = Database(
#         host=db_credentials.get("host"),
#         port=db_credentials.get("port"),
#         database=db_credentials.get("database"),
#         user=db_credentials.get("user"),
#         password=db_credentials.get("password"),
#     )
#     db.create_connection()
#     yield db
#     db.close()
