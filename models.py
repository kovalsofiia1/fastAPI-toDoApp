# from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
# from sqlalchemy.orm import relationship
# from database import Base
#
# class Users(Base):
#     __tablename__ = "users"
#
#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String, unique=True, index=True)
#     username = Column(String, unique=True, index=True)
#     first_name = Column(String)
#     last_name = Column(String)
#     hashed_password = Column(String)
#     is_active = Column(Boolean, default=True)
#     role = Column(String, default="user")  # Default role is "user"
#
#     todos = relationship("Todos", back_populates="owner")
#
# class Todos(Base):
#     __tablename__ = "todos"
#
#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String)
#     description = Column(String)
#     priority = Column(Integer)
#     complete = Column(Boolean, default=False)
#     owner_id = Column(Integer, ForeignKey("users.id"))
#
#     owner = relationship("Users", back_populates="todos")
#     categories = relationship(
#         "Category",
#         secondary="todo_category",  # This is the association table
#         back_populates="todos"  # This connects with the Category model
#     )
#
# class Category(Base):
#     __tablename__ = "categories"
#
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, unique=True, index=True)
#     description = Column(String)
#
#     todos = relationship(
#         "Todos",
#         secondary="todo_category",  # This is the association table
#         back_populates="categories"  # This connects with the Todos model
#     )
#
#
# # Association table for many-to-many relationship
# class TodoCategory(Base):
#     __tablename__ = "todo_category"
#
#     id = Column(Integer, primary_key=True, index=True)
#     todo_id = Column(Integer, ForeignKey("todos.id"))
#     category_id = Column(Integer, ForeignKey("categories.id"))
#
#     todo = relationship("Todos")
#     category = relationship("Category")  # Remove `back_populates`
