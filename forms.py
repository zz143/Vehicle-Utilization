from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField , SelectField
from wtforms.validators import InputRequired, NumberRange, ValidationError

class OrderForm(FlaskForm):
    slot = SelectField('Slot', choices=[('1', '6am - 9am'), ('2', '9am - 1pm'), ('3', '4pm - 7pm'), ('4', '7pm - 11pm')])
    weight = DecimalField('Weight', validators=[NumberRange(min=0, max=100, message="Weight should be in range 0.01 Kg to 100 Kg"), InputRequired()])
    submit = SubmitField('Create Order')

class VehicleForm(FlaskForm):
    slot = SelectField('Slot', choices=[('1', '6am - 9am'), ('2', '9am - 1pm'), ('3', '4pm - 7pm'), ('4', '7pm - 11pm')])
    submit = SubmitField('Get Vehicle Distribution')