from pydantic import BaseModel, Field, EmailStr, ConfigDict, SecretStr, field_validator
from src.field_validators_pydantic import password_verification

class UserCreate(BaseModel):
    """
    Модель для создания пользователя
    """
    name: str = Field(
        min_length=5, 
        pattern="^[A-Za-zА-Яа-яЁё0-9]+([ ._-][A-Za-zА-Яа-яЁё0-9]+)*$", 
        description="имя пользователя", 
        examples=['Maksim']
    )
    email: EmailStr = Field(description="Email пользователя")
    password: SecretStr = Field(description="Пароль пользователя")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: SecretStr):
        password_verification(v.get_secret_value())
        return v

class UserLogin(BaseModel):
    email: EmailStr = Field(description="Email пользователя")
    password: SecretStr
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: SecretStr):
        password_verification(v.get_secret_value())
        return v
        
class User(BaseModel):
    """
    Модель для ответа с данными пользователя
    """
    id: int = Field(description="id пользователя")
    name: str = Field(description="имя пользователя")
    email: EmailStr = Field(description="Email пользователя")
    
    model_config = ConfigDict(from_attributes=True)
    
class UserPasswordSetup(BaseModel):
    reset_token: str = Field(description="токен для замены пароля")
    new_password: SecretStr = Field(description="Новый пароль")
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: SecretStr):
        password_verification(v.get_secret_value())
        return v

class UserPasswordSetupAuth(BaseModel):
    old_password: SecretStr | None = Field(default = None, description="Старый пароль")
    new_password: SecretStr = Field(description="Новый пароль")
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: SecretStr):
        password_verification(v.get_secret_value())
        return v

class UserVerificationCode(BaseModel):
    email: EmailStr = Field(description="email пользователя")
    code: str = Field(description="Код введённый пользователем в поля")
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str):
        if len(v) != 6:
            raise ValueError("Введённый код должен быть шестизначным")
        return v