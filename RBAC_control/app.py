from modules.auth import RoleManager
from modules.rag import RAGWithRoles
from dotenv import load_dotenv
from modules.user_management import UserManager
import os
# Load environment variables
load_dotenv()

# Neo4j configurations
NEO4J_BOLT_URL = os.getenv("NEO4J_BOLT_URL")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")
print("Neo4j Configuration:")
print(f"NEO4J_BOLT_URL: {NEO4J_BOLT_URL}")
print(f"NEO4J_USERNAME: {NEO4J_USERNAME}")
print(f"NEO4J_PASSWORD: {NEO4J_PASSWORD}")
print(f"NEO4J_DATABASE: {NEO4J_DATABASE}")
def user_management_menu(user_manager):
    while True:
        print("\nUser Management Menu:")
        print("1. Create User")
        print("2. Delete User")
        print("3. List Users and Roles")
        print("4. Assign Role to User")
        print("5. Remove Role from User")
        print("6. Exit User Management")

        choice = input("Enter your choice: ")

        if choice == "1":
            username = input("Enter username: ")
            password = input("Enter password: ")
            roles = input("Enter roles (comma-separated, leave blank for default 'reader'): ").split(",")
            roles = [role.strip() for role in roles if role.strip()]
            user_manager.create_user(username, password, roles)
        elif choice == "2":
            username = input("Enter username to delete: ")
            user_manager.delete_user(username)
        elif choice == "3":
            user_manager.list_users_with_roles()
        elif choice == "4":
            username = input("Enter username: ")
            role = input("Enter role to assign: ")
            user_manager.assign_role(username, role)
        elif choice == "5":
            username = input("Enter username: ")
            role = input("Enter role to remove: ")
            user_manager.remove_role(username, role)
        elif choice == "6":
            print("Exiting User Management...")
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    print("Neo4j Configuration:")
    print(f"NEO4J_BOLT_URL: {NEO4J_BOLT_URL}")
    print(f"NEO4J_USERNAME: {NEO4J_USERNAME}")
    print(f"NEO4J_PASSWORD: {NEO4J_PASSWORD}")
    print(f"NEO4J_DATABASE: {NEO4J_DATABASE}")

    username = input("Enter your username: ")
    password = input("Enter your password: ")

    # Authenticate User
    role_manager = RoleManager(NEO4J_BOLT_URL, username, password, NEO4J_DATABASE)
    is_authenticated, roles = role_manager.authenticate_user(username, password)

    if not is_authenticated:
        print("Authentication failed. Exiting...")
        return

    print(f"Authenticated as {username}. Roles: {roles}")

    # Initialize UserManager for admin functions
    user_manager = UserManager(NEO4J_BOLT_URL, NEO4J_USERNAME, NEO4J_PASSWORD)
    
    # Main Operation Menu
    while True:
        print("\nMain Menu:")
        print("1. User Management")
        print("2. Add Documents")
        print("3. Query Graph")
        print("4. Retrieval QA")
        print("5. Exit")

        choice = input("Enter your choice: ")
        if choice == "1":
            user_management_menu(user_manager)
        elif choice == "2":
            rag = RAGWithRoles(roles, username, password, NEO4J_DATABASE)
            rag.add_documents()
        elif choice == "3":
            rag = RAGWithRoles(roles, username, password, NEO4J_DATABASE)
            rag.text_to_cypher_qa()
        elif choice == "4":
            rag = RAGWithRoles(roles, username, password, NEO4J_DATABASE)
            rag.retrieval_qa()
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

    # Clean up
    role_manager.close()
    user_manager.close()

if __name__ == "__main__":
    main()
