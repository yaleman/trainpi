# from signal import pause
import time
from buildhat import DeviceError, PassiveMotor  # type: ignore

# the train is a "passive" motor - https://buildhat.readthedocs.io/en/latest/buildhat/passivemotor.html


def main() -> None:
    try:
        print("Hello world")
        print("Starting Motor")

        motor = PassiveMotor("A")

        try:
            motor.isconnected()
        except DeviceError as e:
            print("DeviceError connecting to motor:", e)

        motor.set_default_speed(30)

        print("Start motor")
        motor.start()
        time.sleep(3)
        print("Stop motor")
        motor.stop()
    except Exception as error:
        print(f"ERROR! {error}")
        motor.stop()


if __name__ == "__main__":
    main()
