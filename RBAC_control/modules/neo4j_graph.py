# modules/neo4j_graph.py
from neo4j import GraphDatabase

class Neo4jGraph:
    def __init__(self, url, username, password, database):
        self._driver = GraphDatabase.driver(url, auth=(username, password), database=database)
        self._database = database  # Add this line

    def close(self):
        self._driver.close()
