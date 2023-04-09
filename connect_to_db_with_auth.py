from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy
import datetime
import json

user_list = {}

def connect_with_connector_auto_iam_authn() -> sqlalchemy.engine.base.Engine:
    """
    Initializes a connection pool for a Cloud SQL instance of MySQL.

    Uses the Cloud SQL Python Connector with Automatic IAM Database Authentication.
    """
    # Note: Saving credentials in environment variables is convenient, but not
    # secure - consider a more secure solution such as
    # Cloud Secret Manager (https://cloud.google.com/secret-manager) to help
    # keep secrets safe.
    info = {}
    with open('secret.json', "r") as f:
        info = json.loads(f.read())
    
    instance_connection_name = info["INSTANCE_CONNECTION_NAME"]  # e.g. 'project:region:instance'
    db_iam_user = info["DB_IAM_USER"]  # e.g. 'sa-name@project-id.iam'
    db_name = info["DB_NAME"]  # e.g. 'my-database'
    ip_type = IPTypes.PUBLIC

    # initialize Cloud SQL Python Connector object
    connector = Connector()

    def getconn() -> pymysql.connections.Connection:
        conn: pymysql.connections.Connection = connector.connect(
            instance_connection_name,
            "pymysql",
            user=db_iam_user,
            db=db_name,
            enable_iam_auth=True,
            ip_type=ip_type,
        )
        return conn

    # The Cloud SQL Python Connector can be used with SQLAlchemy
    # using the 'creator' argument to 'create_engine'
    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
        # ...
    )
    return pool

if __name__ == '__main__':
    # initialize Connector object
    pool = connect_with_connector_auto_iam_authn()

    with pool.connect() as db_conn:
        ### query operations ###
        # insert statement
        def query_insert(user, email, pwd):
            stmt = sqlalchemy.text(
                "INSERT INTO `db`.`user` (`username`,`email`,`password`,`create_time`) VALUES (:username,:email,:password,:create_time);"
            )
            # insert into database
            db_conn.execute(stmt, parameters={"username": user, "email": email, "password": pwd, "create_time": datetime.datetime.now()})
            db_conn.commit()
        
        # delete statement
        def query_delete(user):      
            stmt = sqlalchemy.text(
                "DELETE FROM `db`.`user` WHERE (`username` = :username);"
            )
            # delete a user
            db_conn.execute(stmt, parameters={"username": user})
            db_conn.commit()
        
        # search statement
        def query_search(user, pwd):      
            stmt = sqlalchemy.text(
                "SELECT 1 FROM `db`.`user` WHERE (`username` = :username) AND (`password` = :password);"
            )
            # search a user with pwd
            res = db_conn.execute(stmt, parameters={"username": user, "password": pwd}).fetchall()
            return False if len(res) == 0 else True
        
        ### query operations examples ###
        # query_insert("test2", "test2@gmail.com", "test2pwd")
        # query_delete("test2")
        # print(query_search("test1", "test1pwd"))

        # query database
        result = db_conn.execute(sqlalchemy.text("SELECT * from db.user")).fetchall()

        # save the results to global user list format {key(userid): value{email, pwd, ts}, ...}
        for username, email, pwd, ts in result:
            row = {"email": email, "password": pwd, "create_time": ts}
            user_list[username] = row
        
        # debug: print all users
        print(user_list)
