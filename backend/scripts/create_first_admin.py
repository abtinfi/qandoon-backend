from backend.database.config import get_db
from backend.models.user import User
from backend.core.security import hash_password
import getpass
import re

def validate_email(email):
    # Basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    # Password must be at least 8 characters long and contain at least one uppercase letter,
    # one lowercase letter, one number, and one special character
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def create_first_admin():
    # Get database session
    db = next(get_db())
    
    # Get admin email
    while True:
        email = input("Enter admin email: ").strip()
        if validate_email(email):
            break
        print("Invalid email format. Please try again.")
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    
    if existing_user:
        if existing_user.is_admin:
            print("User is already an admin!")
            return
        
        # Update existing user to admin
        existing_user.is_admin = True
        db.commit()
        print(f"\nUser {email} has been updated to admin successfully!")
        return
    
    # Get admin name
    name = input("Enter admin name: ").strip()
    
    # Get admin password
    while True:
        password = getpass.getpass("Enter admin password: ").strip()
        if validate_password(password):
            confirm_password = getpass.getpass("Confirm admin password: ").strip()
            if password == confirm_password:
                break
            print("Passwords do not match. Please try again.")
        else:
            print("Password must be at least 8 characters long and contain at least one uppercase letter, "
                  "one lowercase letter, one number, and one special character.")
    
    # Create new user
    hashed_password = hash_password(password)
    new_admin = User(
        email=email,
        name=name,
        password=hashed_password,
        is_verified=True,  # Set as verified since this is the first admin
        is_admin=True
    )
    
    # Add to database
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    print("\nFirst admin user created successfully!")
    print(f"Email: {email}")
    print("Please save these credentials securely!")

if __name__ == "__main__":
    create_first_admin() 