from sqlalchemy import Column, Integer, String, MetaData
# from .database import Base
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy import ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship

metadata = MetaData()

Base = declarative_base(metadata=metadata)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    address = Column(String(200), nullable=True)
    phone = Column(String(15), nullable=True)


class Magazine(Base):
    __tablename__ = 'magazines'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(200), nullable=False)
    base_price = Column(Integer, nullable=False)
    discount = Column(Float, nullable=False, default=10.0)
    discount_half_yearly = Column(Float, nullable=False, default=10.0)
    discount_quarterly = Column(Float, nullable=True)
    discount_annual = Column(Float, nullable=True)

class Plan(Base):
    __tablename__ = 'plans'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), unique=True, nullable=False)
    description = Column(String(200), nullable=False)
    renewal_period = Column(Integer, nullable=False)

    def __init__(self, title, description, renewal_period):
        self.title = title
        self.description = description
        self.renewal_period = renewal_period

# monthly_plan = Plan(title='Monthly', description='Renewal period of 1 month', renewal_period=1)
# quarterly_plan = Plan(title='Quarterly', description='Renewal period of 3 months', renewal_period=3)
# half_yearly_plan = Plan(title='Half-yearly', description='Renewal period of 6 months', renewal_period=6)
# annual_plan = Plan(title='Annual', description='Renewal period of 12 months', renewal_period=12)

class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    magazine_id = Column(Integer, ForeignKey('magazines.id'), nullable=False)
    plan_id = Column(Integer, ForeignKey('plans.id'), nullable=False)
    price = Column(Integer, nullable=False)
    price_at_renewal = Column(Integer, nullable=False, default=0)
    next_renewal_date = Column(Date, nullable=False, default='2021-01-01')
    is_active = Column(Boolean, nullable=False, default=True)

    user = relationship("User", backref="subscriptions")
    magazine = relationship("Magazine", backref="subscriptions")
    plan = relationship("Plan", backref="subscriptions")