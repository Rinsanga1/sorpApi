import argparse

from app import app
from app.utils.models import db, AdminUsers

with app.app_context():
    parser = argparse.ArgumentParser(description="Admin User Creation")

    parser.add_argument("user", help="Username for the admin user")
    parser.add_argument("pw", help="Password for the admin user")

    args = parser.parse_args()

    log_entry = AdminUsers(username=args.user, email=args.pw)
    db.session.add(log_entry)
    db.session.commit()

    print({"new user added": args.user})
