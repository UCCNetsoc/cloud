
import pymysql
import structlog as logging

from typing import List
from v1 import models, exceptions
from v1.config import config

logger = logging.getLogger(__name__)

class _DB:
    con: pymysql.connections.Connection

    def __init__(self):
        self.con = pymysql.connect(
            host=config.mysql.server,
            user=config.mysql.username,
            password=config.mysql.password,
            cursorclass=pymysql.cursors.DictCursor,
            read_timeout=5,
            write_timeout=5,
            connect_timeout=5,
        )

    def __enter__(self):
        return self

    def __exit__(self ,type, value, traceback):
        if self.con:
            self.con.close()

class MySQL:
    def __init__(self):
        pass


    # Legacy netsoc setups installed wordpress as wp_<username>, we need to check for this
    def _is_username_db(
        self,
        db_name: str,
        username: str,
    ) -> bool:
        return db_name.startswith(f"{username}_") or db_name == f"wp_{username}"

    def _is_allowed_new_username_db(
        self,
        db_name: str,
        username: str
    ) -> bool:
        return db_name.startswith(f"{username}_")

    def list_by_account(
        self,
        account: models.account.Account
    ) -> List[models.mysql.Database]:
        with _DB() as db:
            logging.getLogger("api").info(type(db))
            with db.con.cursor() as cur:
                try:
                    cur.execute("SHOW DATABASES;")

                    result = list(filter(
                        lambda db_name: self._is_username_db(db_name, account.username),
                        map(lambda row: row["Database"], cur.fetchall())
                    ))

                    dbs = []
                    for name in result:
                        dbs.append(
                            models.mysql.Database(
                                name=name
                            )
                        )

                    return dbs
                except Exception as e:
                    raise exceptions.provider.Failed(f"couldn't list databases for {account.username}: {e}")

    def create_database(
        self,
        account: models.account.Account,
        database: models.mysql.Database
    ):
        if not self._is_allowed_new_username_db(database.name, account.username):
            raise exceptions.resource.Unavailable(f"Not allowed. Database name does not have prefix {account.username}")

        with _DB() as db:
            with db.con.cursor() as cur:
                try:
                    # make sure deleting or creating is a valid thing to do
                    dbs = self.list_by_account(account)
                    
                    for db in dbs:
                        if db.name == database.name:
                            raise exceptions.resource.AlreadyExists("database already exists")
                    
                    cur.execute(f"CREATE DATABASE `{database.name}`;")

                    username_pattern = db.con.escape(f"{account.username}").strip("'")
                    database_pattern = username_pattern + "%%%%"
                    if config.production:
                        sql = f"""
                            GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, REFERENCES,
                            INDEX, ALTER, EXECUTE, CREATE ROUTINE, ALTER ROUTINE
                                ON `{database_pattern}`.* TO %s@'localhost';"""
                        cur.execute(sql, account.username)

                    sql = f"""
                        GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, REFERENCES,
                        INDEX, ALTER, EXECUTE, CREATE ROUTINE, ALTER ROUTINE
                            ON `{database_pattern}`.* TO %s@'%%';"""

                    cur.execute(sql, account.username)
                except exceptions.exception.APIException as api_e:
                    raise api_e
                except Exception as e:
                    logger.error(e=e, exc_info=True)
                    raise exceptions.provider.Failed(f"couldn't create database: {e}")

    def delete_database(
        self,
        account: models.account.Account,
        database: models.mysql.Database
    ):
        if not self._is_username_db(database.name, account.username):
            raise exceptions.resource.Unavailable(f"Not allowed. Database is not for {account.username}")

        with _DB() as db:
            with db.con.cursor() as cur:
                try:
                    dbs = self.list_by_account(account)
                    found = False
                    for db in dbs:
                        if db.name == database.name:
                            found = True
                    
                    if not found:
                        raise exceptions.resource.NotFound("database doesn't exist")

                    sql = f"DROP DATABASE `{database.name}`;"
                    cur.execute(sql)
                except exceptions.exception.APIException as api_e:
                    raise api_e
                except Exception as e:
                    raise exceptions.provider.Failed(f"couldn't delete database: {e}")

    def account_user_exists(
        self,
        account: models.account.Account
    ) -> bool:
        with _DB() as db:
            db.con.autocommit = False
            with db.con.cursor() as cur:
                try:
                    # check is username already exists
                    sql = "SELECT User FROM mysql.user WHERE User=%s;"
                    cur.execute(sql, account.username)
                    if cur.rowcount:
                        return True
                    else:
                        return False
                except Exception as e:
                    raise exceptions.provider.Failed(f"couldn't check existence of mysql user: {account.username}: {e}")


    def change_password(
        self,
        account: models.account.Account,
        password: models.password.Password
    ):
        self.account_user_exists(account)
        
        with _DB() as db:
            with db.con.cursor() as cur:
                try:
                    sql = """ALTER USER %s@'%%' IDENTIFIED BY %s;"""
                    cur.execute(sql, (account.username, password,))
                except Exception as e:
                    raise exceptions.provider.Failed(f"couldn't change password of mysql user {account.username}: {e}")

    def create_account_user(
        self,
        account: models.account.Account,
        password: models.password.Password
    ):
        with _DB() as db:
            db.con.autocommit = False
            with db.con.cursor() as cur:
                try:
                    if self.account_user_exists(account):
                        raise exceptions.resource.AlreadyExists(f"mysql user {account.username} already exists")

                    sql = """CREATE USER %s@'%%' IDENTIFIED BY %s;"""
                    cur.execute(sql, (account.username, password,))

                    if config.production:
                        sql = """CREATE USER %s@'localhost' IDENTIFIED BY %s;"""
                        cur.execute(sql, (account.username, password,))

                    # grant the user permissions on all databases of the form
                    # "<username>_something".
                    # Note: the escaping must be done in two parts here becuase
                    # PyMySQL will insert quotation marks around the %s which
                    # makes the pattern `'username'_%`.
                    username_pattern = db.con.escape(f"{account.username}").strip("'")
                    database_pattern = username_pattern + "%%%%"
                    if config.production:
                        sql = f"""
                            GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, REFERENCES,
                            INDEX, ALTER, EXECUTE, CREATE ROUTINE, ALTER ROUTINE
                                ON `{database_pattern}`.* TO %s@'localhost';"""
                        cur.execute(sql, account.username)

                    sql = f"""
                        GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, REFERENCES,
                        INDEX, ALTER, EXECUTE, CREATE ROUTINE, ALTER ROUTINE
                            ON `{database_pattern}`.* TO %s@'%%';"""

                    cur.execute(sql, account.username)
                    db.con.commit()
                except Exception as e:
                    raise exceptions.provider.Failed(f"couldn't create mysql user {account.username}: {e}")
