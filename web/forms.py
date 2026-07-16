"""
web/forms.py

Energy Monitor V2

Flask-WTF forms.
"""

from __future__ import annotations

from pathlib import Path

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FloatField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    NumberRange,
    Optional,
)

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
        validators=[
            DataRequired(),
        ],
    )

    description = StringField(
        "Description",
        validators=[
            Optional(),
        ],
    )

    meter_type = SelectField(
        "Meter type",
        choices=[
            ("modbus", "Modbus meter"),
            ("p1", "P1 Smart Meter"),
        ],
        default="modbus",
        validators=[
            DataRequired(),
        ],
    )

    driver = SelectField(
        "Driver",
        validators=[
            Optional(),
        ],
        choices=[],
    )

    protocol = SelectField(
        "Protocol",
        coerce=int,
        choices=[
            (
                Protocol.TCP.value,
                "Modbus TCP",
            ),
            (
                Protocol.RTU.value,
                "Modbus RTU",
            ),
            (
                Protocol.RTU_OVER_TCP.value,
                "RTU over TCP",
            ),
        ],
        default=Protocol.TCP.value,
    )

    address = StringField(
        "IP Address",
        validators=[
            Optional(),
        ],
    )

    port = IntegerField(
        "Port",
        default=502,
        validators=[
            Optional(),
            NumberRange(
                min=1,
                max=65535,
            ),
        ],
    )

    serial_port = SelectField(
        "Serial Port",
        choices=[],
        validators=[
            Optional(),
        ],
    )

    baudrate = IntegerField(
        "Baudrate",
        default=9600,
        validators=[
            Optional(),
            NumberRange(
                min=300,
                max=1_000_000,
            ),
        ],
    )

    bytesize = IntegerField(
        "Data bits",
        default=8,
        validators=[
            Optional(),
            NumberRange(
                min=5,
                max=8,
            ),
        ],
    )

    parity = SelectField(
        "Parity",
        choices=[
            ("N", "None"),
            ("E", "Even"),
            ("O", "Odd"),
        ],
        default="N",
    )

    stopbits = IntegerField(
        "Stop bits",
        default=1,
        validators=[
            Optional(),
            NumberRange(
                min=1,
                max=2,
            ),
        ],
    )

    slave = IntegerField(
        "Slave ID",
        default=1,
        validators=[
            Optional(),
            NumberRange(
                min=1,
                max=247,
            ),
        ],
    )

    ct = FloatField(
        "CT Ratio",
        default=1.0,
        validators=[
            Optional(),
            NumberRange(
                min=0.000001,
            ),
        ],
    )

    pt = FloatField(
        "PT Ratio",
        default=1.0,
        validators=[
            Optional(),
            NumberRange(
                min=0.000001,
            ),
        ],
    )

    timeout = FloatField(
        "Timeout",
        default=1.0,
        validators=[
            Optional(),
            NumberRange(
                min=0.1,
                max=60.0,
            ),
        ],
    )

    submit = SubmitField(
        "Save"
    )

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:

        super().__init__(
            *args,
            **kwargs,
        )

        self._load_driver_choices()
        self._load_serial_port_choices()

    # ------------------------------------------------------------------
    # Choice loaders
    # ------------------------------------------------------------------

    def _load_driver_choices(
        self,
    ) -> None:
        """Load available meter drivers."""

        modbus_drivers = [
            (
                name,
                name.upper(),
            )
            for name in DriverFactory.names()
        ]

        self.driver.choices = [
            (
                "p1",
                "P1 SMART METER",
            ),
            *modbus_drivers,
        ]

    def _load_serial_port_choices(
        self,
    ) -> None:
        """Load serial devices available on the system."""

        ports: list[str] = []

        patterns = (
            "/dev/ttyUSB*",
            "/dev/ttyACM*",
            "/dev/ttyAMA*",
            "/dev/ttyS*",
        )

        for pattern in patterns:

            for path in sorted(
                Path("/dev").glob(
                    Path(pattern).name
                )
            ):

                port = str(path)

                if port not in ports:
                    ports.append(port)

        current_port = (
            self.serial_port.data
            or ""
        ).strip()

        if (
            current_port
            and current_port not in ports
        ):
            ports.insert(
                0,
                current_port,
            )

        if ports:

            self.serial_port.choices = [
                (
                    port,
                    port,
                )
                for port in ports
            ]

        else:

            self.serial_port.choices = [
                (
                    "",
                    "No serial ports found",
                )
            ]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(
        self,
        extra_validators=None,
    ) -> bool:
        """
        Validate fields according to the selected meter type.
        """

        valid = super().validate(
            extra_validators=extra_validators
        )

        meter_type = (
            self.meter_type.data
            or "modbus"
        ).strip().lower()

        if meter_type == "p1":

            self.driver.data = "p1"

            if not (
                self.serial_port.data
                or ""
            ).strip():

                self.serial_port.errors.append(
                    "Serial port is required for P1."
                )

                valid = False

        elif meter_type == "modbus":

            if not (
                self.driver.data
                or ""
            ).strip():

                self.driver.errors.append(
                    "Driver is required."
                )

                valid = False

            try:

                protocol_value = int(
                    self.protocol.data
                )

            except (
                TypeError,
                ValueError,
            ):

                self.protocol.errors.append(
                    "Invalid protocol."
                )

                return False

            if protocol_value in (
                Protocol.TCP.value,
                Protocol.RTU_OVER_TCP.value,
            ):

                if not (
                    self.address.data
                    or ""
                ).strip():

                    self.address.errors.append(
                        "IP address is required."
                    )

                    valid = False

            elif (
                protocol_value
                == Protocol.RTU.value
            ):

                if not (
                    self.serial_port.data
                    or ""
                ).strip():

                    self.serial_port.errors.append(
                        "Serial port is required."
                    )

                    valid = False

        else:

            self.meter_type.errors.append(
                "Unsupported meter type."
            )

            valid = False

        return valid