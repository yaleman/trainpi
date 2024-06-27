# import time
import sys
from time import monotonic
from typing import Optional
from buildhat import DeviceError, PassiveMotor  # type: ignore[import-untyped]

import platform

# from textual.containers import ScrollableContainer
from textual.binding import Binding
from textual.app import App, ComposeResult
from textual.widgets import Button, Static, Header, Footer
from textual.reactive import reactive

# the train is a "passive" motor - https://buildhat.readthedocs.io/en/latest/buildhat/passivemotor.html

# def dothething() -> None:
#     try:
#         print("Connecting to motor...")

#         motor = PassiveMotor("A")
#         try:
#             motor.isconnected()
#         except DeviceError as e:
#             print("DeviceError connecting to motor:", e)
#         motor.plimit(1.0)
#         motor.set_default_speed(100)

#         print("Start motor")
#         motor.start()
#         time.sleep(3)
#         print("Stop motor")
#         motor.stop()
#     except Exception as error:
#         print(f"ERROR! {error}")
#         motor.stop()


class TimeDisplay(Static):
    """A widget to display elapsed time."""

    start_time = reactive(monotonic)  # type: ignore[var-annotated,arg-type]
    time = reactive(0.0)
    total = reactive(0.0)

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self) -> None:
        """Method to update the time to the current time."""
        self.time = self.total + (monotonic() - self.start_time)

    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")

    def start(self) -> None:
        """Method to start (or resume) time updating."""
        self.start_time = monotonic()
        self.update_timer.resume()

    def stop(self) -> None:
        """Method to stop the time display updating."""
        self.update_timer.pause()
        self.total += monotonic() - self.start_time
        self.time = self.total

    def reset(self) -> None:
        """Method to reset the time display to zero."""
        self.total = 0
        self.time = 0


class TrainControls(Static):

    # BINDINGS = [("s", "start_stop", "Start/Stop")]

    running = False
    speed = 50

    def __init__(self, motor: PassiveMotor) -> None:
        super().__init__()
        self.motor = motor

    def compose(self) -> ComposeResult:
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Reset", id="reset")
        yield TimeDisplay()

    def speed_up(self) -> None:
        self.speed = min(100, self.speed + 10)
        if self.running:
            self.motor.set_speed(self.speed)

    def speed_down(self) -> None:
        self.speed = max(0, self.speed - 10)
        if self.running:
            self.motor.set_speed(self.speed)
            if self.speed == 0:
                self.toggle_running()

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
                self.motor.start(self.speed)

        if self.has_class("started"):
            self.running = False
            self.remove_class("started")
            time_display = self.query_one(TimeDisplay)
            time_display.stop()
        else:
            self.running = True
            self.add_class("started")
            time_display = self.query_one(TimeDisplay)
            time_display.start()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id
        time_display = self.query_one(TimeDisplay)
        if button_id in ("start", "stop"):
            self.toggle_running()
        elif button_id == "reset":
            time_display.reset()


class TrainPiApp(App):
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
        super().__init__()
        self.motor = motor

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


def get_motor() -> Optional[PassiveMotor]:
    system = platform.system()
    if system == "Darwin":
        # print("You're on a Mac")
        return None
    elif system == "Linux":
        # print("You're on Linux")
        motor = PassiveMotor("A")
        motor.plimit(1.0)
        motor.set_default_speed(50)
        return motor
    else:
        # print(f"You're on a different system: {system}")
        return None


def main() -> None:
    motor = get_motor()
    app = TrainPiApp(motor)
    app.run()

    if motor is not None:
        motor.stop()


if __name__ == "__main__":
    main()
