"""Fixtures for the tests."""

import os
from pathlib import Path

import pytest
from automator.database.db import Database
from testcontainers.postgres import PostgresContainer

script = (
    Path(__file__).parent.parent
    / "db-automator/migrations/V001_20241013143045__carstenskov.sql"
)


postgres = PostgresContainer("postgres:16-alpine")
postgres.with_volume_mapping(
    host=str(script), container=f"/docker-entrypoint-initdb.d/{script.name}"
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
