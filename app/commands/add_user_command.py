import argparse

from enums.user_role import UserRole
from services.users_service import UsersService
from entities.user import User
def add_user_command(args):
    role = UserRole.USER
    if args.role is not None:
        args_role = args.role.strip()
        for enum_role in UserRole:
            if enum_role.value == args_role:
                role = enum_role
                break
            role = UserRole.USER
    user = User(name=args.name.strip(), raw_password=args.password.strip(), email=args.email.strip(), is_active=True, role=role)
    UsersService.register_user(user)
    print("User added")
parser = argparse.ArgumentParser(description='Przykład przekazywania argumentów')
parser.add_argument('--name', '-n', type=str, required=True, help='User name')
parser.add_argument('--email', '-e', type=str, required=True, help='User email')
parser.add_argument('--password', '-p', type=str, required=True, help='User password')
parser.add_argument('--role', '-r', type=str, help='User role')

args = parser.parse_args()
add_user_command(args)
