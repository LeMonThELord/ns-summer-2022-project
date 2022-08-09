from util import *
import sqlite3
import json
import os


def init_table(conn, schema_file):
    with open(schema_file, 'r') as f:
        data = json.load(f)
        table_name = data["table_name"]
        log(f"table_name: {table_name}")
        table_schema = data["schema"]
        log(f"table_schema: {table_schema}")

        statement = f"DROP TABLE IF EXISTS {table_name}"
        conn.execute(statement)

        schema = ""
        for rule in table_schema:
            column = f'{rule["name"]} {rule["type"]} {rule["extra"]}'
            schema += column
            if rule != table_schema[-1]:
                schema += ","

        constraints = (
            ""
            if (len(data["constraints"]) == 0)
            else ", " + str(data["constraints"]).strip("[]").replace("'", "")
        )

        statement = f"CREATE TABLE {table_name} ({schema} {constraints})"
        log(f"CREATE TABLE: {statement}")
        conn.execute(statement)


def check_database(filename):
    from os.path import isfile, getsize

    if not isfile(filename):
        return False
    if getsize(filename) < 100:
        return False

    return True


def connect_database(database_name):
    conn = sqlite3.connect(database_name)
    return conn


def init_database(database_name):
    conn = connect_database(database_name)
    # get configs
    path = "../resources/schema/"
    config_files = [os.path.join(path, file) for file in os.listdir(path)]
    # create tables
    for config in config_files:
        init_table(conn, config)
    return conn


def add_people(conn, information):
    cmd = f"INSERT INTO people Values (NULL, {str(information).strip('[]')})"
    log(cmd)
    cursor = conn.execute(cmd)
    conn.commit()
    return cursor.lastrowid


def associate_face(conn, user_id, feature_id):
    cmd = f"INSERT INTO face Values ({float(feature_id)}, {user_id})"
    cursor = conn.execute(cmd)
    conn.commit()


def get_profile(conn, face_id):
    cmd = f"SELECT p.* FROM people p natural join face f WHERE face_id={face_id}"
    cursor = conn.execute(cmd)
    result = cursor.fetchone()
    if result is None:
        return dict()
    profile = {
        "id": result[0],
        "first_name": result[1],
        "last_name": result[2],
        "nick_name": result[3],
        "age": result[4],
        "relation": result[5],
    }
    log(profile)
    return profile

def get_conversations(conn, face_id):

    cmd = f"SELECT context_id, time, keywords FROM (conversation left outer join context using (CONTEXT_ID)) left outer join face using (ID) WHERE face_id={face_id} order by time"
    cursor = conn.execute(cmd)
    results = cursor.fetchall()
    context_list = []
    if results is not None:
        for result in results:
            context_list.append(list(result))
    log(context_list)
    return context_list


def insertOrUpdate_identity(conn, id, name):
    # Check existence
    cmd = f"SELECT * FROM People WHERE ID=?"
    cursor = conn.execute(cmd, id)
    isRecordExist = 0
    for row in cursor:
        isRecordExist = 1
    if isRecordExist == 1:
        cmd = f"UPDATE people SET NICK_NAME=:name WHERE ID=:id"
    else:
        cmd = f"INSERT INTO people(ID,NICK_NAME) Values(:id,:name)"

    # Add or update person
    conn.execute(cmd, {"name": str(name), "id": str(id)})
    conn.commit()
