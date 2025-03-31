import argparse
from services.users_service import UsersService
from entities.user import User
def add_user_command(args):
    user = User(name=args.name, raw_password=args.password, email=args.email)
    UsersService.register_user(user)
    print("User added")
parser = argparse.ArgumentParser(description='Przykład przekazywania argumentów')
parser.add_argument('--name', '-n', type=str, required=True, help='User name')
parser.add_argument('--email', '-e', type=str, required=True, help='User email')
parser.add_argument('--password', '-p', type=str, required=True, help='User password')
args = parser.parse_args()
add_user_command(args)
