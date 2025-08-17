from sqlalchemy import Column, Integer, String, Float
from database import Base

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    cost = Column(Float)
    amount = Column(Integer)