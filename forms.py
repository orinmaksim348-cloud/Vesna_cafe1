from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, Email, Optional, ValidationError
import re

def validate_phone(form, field):
    """Валидатор для номера телефона"""
    phone = field.data
    # Простая валидация: начинается с +, затем цифры
    if not re.match(r'^\+\d{10,15}$', phone):
        raise ValidationError('Введите номер в формате +71234567890')

class PhoneLoginForm(FlaskForm):
    """Форма для ввода номера телефона"""
    phone = StringField('Номер телефона', 
                       validators=[DataRequired(), validate_phone],
                       render_kw={"placeholder": "+71234567890"})
    submit = SubmitField('Получить код')

class OTPVerificationForm(FlaskForm):
    """Форма для ввода SMS-кода"""
    otp = StringField('Код из SMS', 
                     validators=[DataRequired(), Length(min=6, max=6)],
                     render_kw={"placeholder": "Введите 6-значный код", 
                               "maxlength": "6", 
                               "pattern": "[0-9]{6}"})
    submit = SubmitField('Подтвердить и войти')

class ProfileForm(FlaskForm):
    """Форма редактирования профиля"""
    name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[Optional(), Email()])
    submit = SubmitField('Сохранить')

class CheckoutForm(FlaskForm):
    """Форма оформления заказа"""
    address = StringField('Адрес доставки', validators=[DataRequired(), Length(min=5, max=200)])
    phone = StringField('Контактный телефон', validators=[DataRequired(), validate_phone])
    comment = TextAreaField('Комментарий к заказу', validators=[Optional(), Length(max=500)])
    payment_method = StringField('Способ оплаты', default='cash')
    submit = SubmitField('Подтвердить заказ')