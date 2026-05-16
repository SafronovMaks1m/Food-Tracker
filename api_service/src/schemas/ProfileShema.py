from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator
from fastapi import Form

class ChangeProfile(BaseModel):
    name: str | None = Field(
        default= None,
        min_length=5, 
        pattern="^[A-Za-zА-Яа-яЁё0-9]+([ ._-][A-Za-zА-Яа-яЁё0-9]+)*$", 
        description="имя пользователя", 
        examples=['Maksim']
    )    
    
    @classmethod
    def as_form(
        cls, 
        name: str | None = Form(default=None)
    ):
        return cls(name=name)

class ChangeEmail(BaseModel):
    new_email: EmailStr = Field(description="новый Email пользователя")
    password: SecretStr = Field(description="Пароль пользователя")