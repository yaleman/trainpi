# trainpi
import platform
from typing import Optional

from buildhat import PassiveMotor  # type: ignore[import-untyped]


# the train is a "passive" motor - https://buildhat.readthedocs.io/en/latest/buildhat/passivemotor.html
def get_motor() -> Optional[PassiveMotor]:
    system = platform.system()
    if system == "Darwin":
        return None
    elif system == "Linux":
        motor = PassiveMotor("A")
        motor.plimit(1.0)
        motor.set_default_speed(50)
        return motor
    else:
        return None
