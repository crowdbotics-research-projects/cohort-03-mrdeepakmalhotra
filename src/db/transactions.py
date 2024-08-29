from sqlalchemy.orm import sessionmaker
from models import User, Magazine
from contextlib import contextmanager
import random, string

def generate_random_email(domain="example.com", length=10):
    # Generate a random string of letters and digits for the email username
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    # Construct the email address
    email = f"{username}@{domain}"
    
    return email

class DBTransactions:

    def __init__(self, engine):
        self.engine = engine
        self.session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    @contextmanager
    def session_scope(self, commit: bool = True):
        session = self.session()
        try:
            yield session
            if commit:
                session.commit()
        finally:
            session.close()

    def authenticate_user(self, email: str, password: str):
        with self.session_scope() as db_session:
            user = db_session.query(User).filter(User.email == email, User.password == password).first()
            if not user:
                return False
            return user
    
    def authenticate_user_by_username(self, username: str, password: str):
        with self.session_scope() as db_session:
            user = db_session.query(User).filter(User.username == username, User.password == password).first()
            if not user:
                return False
            return user


    def register(self, username: str, password: str, email: str = None, address: str = None, phone: int = None):
        with self.session_scope() as db_session:
            if email is None:
                email = generate_random_email()
            db_session.add(User(username=username, email=email, password=password, address=address, phone=phone))
            db_session.commit()
            db_session.close()
            return {"message": "User registered successfully"}
    
    def add_magazine(self, name: str, desc: str):
        with self.session_scope() as db_session:
            db_session.add(Magazine(name=name, description=desc))
            db_session.commit()
            db_session.close()
            return {"message": "User registered successfully"}
    
    def login(self, email: str, password: str):
        with self.session_scope() as db_session:
            user = db_session.query(User).filter(User.email == email, User.password == password).first()
            if user is None:
                raise Exception("User not found")
            return user
    
    def get_user_by_id(self, user_id: int):
        with self.session_scope() as db_session:
            user = db_session.query(User).filter(User.id == user_id).first()
            if user is None:
                raise Exception("User not found")
            return user



# def register(username: str, email: str, password: str, address: Optional[str] = None, phone: Optional[str] = None):
#     db_session = SessionLocal()
#     db_session.add(User(username=username, email=email, password=password, address=address, phone=phone))
#     db_session.commit()
#     db_session.close()
#     return {"message": "User registered successfully"}