import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
	__tablename__ = 'user'

	name = Column(String(50), nullable = False)
	email = Column(String(50), nullable = False)
	picture = Column(String(250))
	id = Column(Integer, primary_key = True)

	@property
	def serialize(self):
		"""Return object data in serializeable format"""
		return {
        	'name': self.name,
        	'email': self.email,
        	'picture': self.picture,
        	'id': self.id,
        }

class Fish(Base):
	__tablename__ = 'fish'

	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	lures = relationship("Lure", cascade="all, delete-orphan")

	@property
	def serialize(self):
		"""Return object data in serializable format"""
		return {
			'name': self.name,
			'id': self.id,
			'picture': self.picture,
		}

class Lure(Base):
	__tablename__ = 'lure'

	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	description = Column(String(250))
	price = Column(String(8))
	fish_id = Column(Integer, ForeignKey('fish.id'))
	fish = relationship(Fish)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
		return {
			'name': self.name,
			'description': self.description,
			'id': self.id,
			'price': self.price,
		}

engine = create_engine('sqlite:///fishguide.db')

Base.metadata.create_all(engine)