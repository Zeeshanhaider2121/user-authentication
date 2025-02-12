from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_BOLT_URL = os.getenv("NEO4J_BOLT_URL")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE=os.getenv("NEO4J_DATABASE")


class RoleManager:
    def __init__(self, uri, username, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.database = database

    def authenticate_user(self, username, password):
        try:
            temp_driver = GraphDatabase.driver(NEO4J_BOLT_URL, auth=(username, password))
            with temp_driver.session() as session:
                result = session.run("CALL dbms.showCurrentUser()")
                user_info = result.single()
                roles = user_info.get("roles", [])
                return True, roles
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False, []

    def close(self):
        self.driver.close()