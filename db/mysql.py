import os

import mysql.connector

from utils import get_secret


def get_db() -> mysql.connector.MySQLConnection:
    mysql_config = get_secret(os.environ["MYSQL_SECRET_NAME"])
    db = mysql.connector.connect(
        host=mysql_config["host"],
        user=mysql_config["username"],
        password=mysql_config["password"],
        database=mysql_config["dbname"],
        connect_timeout=3000000,
    )
    return db
