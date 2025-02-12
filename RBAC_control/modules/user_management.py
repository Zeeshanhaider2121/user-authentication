
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

class UserManager:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def create_user(self, username, password, roles=["reader"]):
        if self.user_exists(username):
            logging.error(f"User '{username}' already exists.")
            return

        # Do not hash the password; store it in plain text (NOT RECOMMENDED)
        plain_password = password

        # Validate roles before user creation
        valid_roles = self.list_roles()
        invalid_roles = [role for role in roles if role not in valid_roles]
        if invalid_roles:
            logging.error(f"Invalid roles provided: {', '.join(invalid_roles)}. These roles will not be assigned.")
            roles = [role for role in roles if role not in invalid_roles]  # Filter out invalid roles

        try:
            with self.driver.session() as session:
                # Create the user
                session.run(
                    f"CREATE USER {username} SET PASSWORD '{plain_password}' CHANGE NOT REQUIRED"
                )
                logging.info(f"User '{username}' created successfully.")
                
                # Assign valid roles
                for role in roles:
                    session.run(f"GRANT ROLE {role} TO {username}")
                    logging.info(f"Role '{role}' granted to user '{username}'.")
        except Exception as e:
            logging.error(f"Error creating user '{username}': {e}")

    def user_exists(self, username):
        with self.driver.session() as session:
            result = session.run(f"SHOW USERS WHERE user = '{username}'")
            return result.single() is not None

    def list_roles(self):
        """List all available roles in Neo4j."""
        with self.driver.session() as session:
            result = session.run("SHOW ROLES")
            roles = [record["role"] for record in result]
            logging.info("Available roles in Neo4j:")
            for role in roles:
                logging.info(role)
            return roles

  
    def list_users_with_roles(self):
        with self.driver.session() as session:
        # Query to retrieve users and their roles
            result = session.run("SHOW USERS YIELD user, roles")
        
        # Loop through the result and log the users and their roles
            logging.info("Users and their roles in the database:")
            for record in result:
                user = record["user"]
                roles = record["roles"]
                logging.info(f"User: {user}, Roles: {roles}")


    def delete_user(self, username):
        try:
            with self.driver.session() as session:
                session.run(f"DROP USER {username}")
                logging.info(f"User '{username}' deleted.")
        except Exception as e:
            logging.error(f"Error deleting user '{username}': {e}")
    
    def get_user_roles(self, username):
        """Get roles assigned to a specific user."""
        with self.driver.session() as session:
            result = session.run("SHOW USERS")
            roles = []
            for record in result:
                if record["user"] == username:
                   roles = record["roles"]  # Extract the roles for the given user
                   break
            if not roles:
               logging.warning(f"No roles found for user '{username}'.")
            else:
               logging.info(f"Roles for user '{username}': {roles}")
               return roles


    def remove_role(self, username, role):
        """Remove a specific role from a user."""
        with self.driver.session() as session:
            session.run(f"REVOKE ROLE {role} FROM {username}")
            logging.info(f"Role '{role}' revoked from user '{username}'.")
