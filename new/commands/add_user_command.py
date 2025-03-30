from repositories.users_repository import UsersRepository
import db

def add_user_command():
    UsersRepository.add_user(name="Test", password="aaaaa5", email="email@mail.com")
    print("User added")

add_user_command()