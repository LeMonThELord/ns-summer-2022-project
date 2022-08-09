import database_operations as do
import face_recog as face
import util
from util import log
import sys

arguments = sys.argv

if "-d" in arguments:
    util._DEBUG = True

def add_people(conn):
    print("Please enter information")
    first_name = input("First name: ")
    last_name = input("Last name: ")
    nick_name = input("Nick name: ")
    age = input("Age: ")
    relation = input("Relation: ")
    information = [first_name, last_name, nick_name, age, relation]
    id = do.add_people(conn, information)
    print(f"Please remember your id: {id}")

def get_face_feature():
    # image_path = input("Please enter path of image to learn (camera by default): ")
    feature_ids = face.get_face()

def associtate_face(conn):
    print("Please enter information")
    user_id = input("user id: ")
    feature_id = input("feature id: ")
    do.associate_face(conn, user_id, feature_id)

def run_ui(conn):
    face.run(conn)

# Setup command list
conn_commands = {"add identity": add_people, "associate face": associtate_face, "run ui": run_ui}
empty_commands = {"get face": get_face_feature}

# Connect to database
database_name = "../resources/temp.db"
conn = None
if do.check_database(database_name):
    log("Connected to existing DB")
    conn = do.connect_database(database_name)
    # do.init_table(conn, "../resources/schema/3.context_schema.json")
    # do.init_table(conn, "../resources/schema/4.conversation_schema.json")
else:
    log("Connected to new DB")
    conn = do.init_database(database_name)

# Main program logic
while True:
    command = input("Please enter your command: ").lower()
    if command in conn_commands:
        conn_commands[command](conn)
    elif command in empty_commands:
        empty_commands[command]()
    elif command == "ls":
        [print(i) for i in conn_commands.keys()]
        [print(i) for i in empty_commands.keys()]
    elif command == "exit":
        break
    else:
        print(f"Invalid command: {command}")

conn.close()
