# import time
import sys

from typing import Optional
from buildhat import DeviceError, PassiveMotor  # type: ignore[import-untyped]

from textual.binding import Binding
from textual.app import App, ComposeResult
from textual.widgets import Button, Static, Header, Footer
from textual.reactive import reactive

from trainpi import get_motor
from trainpi.timedisplay import TimeDisplay

DEFAULT_SPEED = 50


class SpeedDisplay(Static):
    """A widget to display the speed of the motor."""

    speed = reactive(0)

    def watch_speed(self, speed: int) -> None:
        """Called when the speed attribute changes."""
        self.update(f"Speed: {speed}")

    def speed_up(self, motor: Optional[PassiveMotor]) -> None:
        """Method to increase the speed of the motor."""
        self.speed = min(100, self.speed + 10)
        if motor is not None:
            motor.start(self.speed)

    def speed_down(self, motor: Optional[PassiveMotor]) -> None:
        """Method to decrease the speed of the motor."""
        self.speed = max(-100, self.speed - 10)
        if motor is not None:
            motor.start(self.speed)


class TrainControls(Static):
    running = False

    def __init__(self, motor: Optional[PassiveMotor]) -> None:
        super().__init__()
        self.motor = motor

    def compose(self) -> ComposeResult:
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Reset", id="reset")
        yield TimeDisplay()
        yield SpeedDisplay()

    def speed_up(self) -> None:
        # max out at 100
        speed = self.query_one(SpeedDisplay)
        speed.speed_up(self.motor)

    def speed_down(self) -> None:
        speed = self.query_one(SpeedDisplay)
        speed.speed_down(self.motor)

    def start_running(self) -> None:
        self.running = True
        self.add_class("started")

        speed = self.query_one(SpeedDisplay)
        speed.speed = 0

        time_display = self.query_one(TimeDisplay)
        time_display.start()

    def stop_running(self) -> None:
        self.running = False
        if self.motor is not None:
            self.motor.stop()

        speed = self.query_one(SpeedDisplay)
        speed.speed = 0

        self.remove_class("started")
        time_display = self.query_one(TimeDisplay)
        time_display.stop()

    def toggle_running(self) -> None:
        if self.motor is not None:
            if self.running:
                self.motor.stop()
            else:
                try:
                    self.motor.isconnected()
                except DeviceError as e:
                    print("DeviceError connecting to motor:", e)
                    sys.exit(1)

        if self.has_class("started"):
            self.stop_running()
        else:
            self.start_running()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id
        time_display = self.query_one(TimeDisplay)
        if button_id in ("start", "stop"):
            self.toggle_running()
        elif button_id == "reset":
            time_display.reset()


class TrainPiApp(App[None]):
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
        Binding(
            key="space", action="stop_start", description="Toggle motor", show=False
        ),
        Binding(key="w", action="speed_up", description="Speed Up", show=False),
        Binding(key="s", action="speed_down", description="Speed Down", show=False),
    ]

    CSS_PATH = "trainpi.tcss"

    def __init__(self, motor: PassiveMotor) -> None:
        self.motor = motor
        self.dark: bool = False
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield TrainControls(self.motor)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_stop_start(self) -> None:
        stopstart = self.query_one(TrainControls)
        stopstart.toggle_running()

    def action_speed_up(self) -> None:
        speedup = self.query_one(TrainControls)
        speedup.speed_up()

    def action_speed_down(self) -> None:
        speeddown = self.query_one(TrainControls)
        speeddown.speed_down()


def main() -> None:
    motor = get_motor()
    if motor is None:
        print("No motor found. Please connect a motor.")
        sys.exit(1)

    else:
        try:
            app = TrainPiApp(motor)
            app.run()
        except Exception as error:
            print(error)
        finally:
            if motor is not None:
                motor.stop()


if __name__ == "__main__":
    main()
