"""
web/forms.py

Energy Monitor V2

Flask-WTF forms.
"""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FloatField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, NumberRange

from common.enums import Protocol
from modbus.drivers.factory import DriverFactory


class MeterForm(FlaskForm):
    """Meter configuration form."""

    enabled = BooleanField(
        "Enabled",
        default=True,
    )

    name = StringField(
        "Name",
        validators=[DataRequired()],
    )

    description = StringField(
        "Description",
    )

    driver = SelectField(
        "Driver",
        validators=[DataRequired()],
        choices=[],
    )

    protocol = SelectField(
        "Protocol",
        coerce=int,
        choices=[
            (Protocol.TCP.value, "TCP"),
            (Protocol.RTU.value, "RTU"),
        ],
    )

    address = StringField("IP Address")

    port = IntegerField(
        "Port",
        default=502,
        validators=[NumberRange(min=1, max=65535)],
    )

    serial_port = StringField("Serial Port")

    baudrate = IntegerField(
        "Baudrate",
        default=9600,
    )

    bytesize = IntegerField(
        "Data bits",
        default=8,
    )

    parity = SelectField(
        "Parity",
        choices=[
            ("N", "None"),
            ("E", "Even"),
            ("O", "Odd"),
        ],
    )

    stopbits = IntegerField(
        "Stop bits",
        default=1,
    )

    slave = IntegerField(
        "Slave ID",
        default=1,
        validators=[
            NumberRange(min=1, max=247),
        ],
    )

    ct = FloatField(
        "CT Ratio",
        default=1.0,
    )

    pt = FloatField(
        "PT Ratio",
        default=1.0,
    )

    timeout = FloatField(
        "Timeout",
        default=1.0,
    )

    submit = SubmitField("Save")

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.driver.choices = [
            (name, name.upper())
            for name in DriverFactory.names()
        ]