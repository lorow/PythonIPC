import json
import os
from concurrent.futures import ThreadPoolExecutor
from enum import IntEnum
from queue import Queue
from threading import Event
from typing import Callable, Optional

from utils import get_response_message

if os.name == "nt":
    from pipe_handlers.windows import get_pipe, read_from_pipe, write_to_pipe
else:
    from pipe_handlers.linux import get_pipe, read_from_pipe, write_to_pipe


class IPCState(IntEnum):
    IDLE = 0
    START = 1
    STOP = 2


class IPCClient:
    """
    Client for IPC communication, does two things.
    Handles communication over named pipes and writes data from in_queue to memory mapped region
    """

    def __init__(
        self,
        event: Event,
        pipe_definition: dict[str, Queue],
        command_handlers: Optional[dict[str, Callable]] = None,
    ):
        self.pipe_definition = pipe_definition
        self.basic_message = "{'message': '{data}'}"

        provided_command_handlers = command_handlers if command_handlers else {}
        self.command_handlers = {
            **provided_command_handlers,
            "start": self.handle_start_command,
            "stop": self.handle_stop_command,
        }

        self.pipes_states = {
            name: IPCState.IDLE for name, _ in self.pipe_definition.items()
        }
        self.event = event

    def handle_missing_command(self, **args):
        return get_response_message(data="Command not supported")

    def handle_start_command(self, pipe_name, **args):
        """Lets the data be written to the memory mapped region if we have any data"""
        self.pipes_states[pipe_name] = IPCState.START
        message = get_response_message(data="Stream started")
        return message

    def handle_stop_command(self, pipe_name, **args):
        self.pipes_states[pipe_name] = IPCState.STOP
        return get_response_message(data="Stream stopped")

    def stream_data(self, pipe_name, data_queue: Queue, event: Event):
        # we want to return as fast as possible before we start blocking
        # if the user quits after we start waiting for connection, oh well

        if event.is_set():
            return

        with get_pipe(pipe_name) as pipe:
            while True:
                if event.is_set():
                    return
                try:
                    data = data_queue.get_nowait()
                except Queue.Empty:
                    continue
                else:
                    write_to_pipe(pipe, data)

    def handle_commands(self, pipe_name: str, event: Event):
        if event.is_set():
            return

        with get_pipe(pipe_name=pipe_name) as pipe:
            while True:
                if event.is_set():
                    return

                data = read_from_pipe(pipe)
                response = None
                if data:
                    command = json.loads(data.decode("utf-8"))
                    print("Command to execute", command)
                    command_handler = self.command_handlers.get(
                        command["command"], self.handle_missing_command
                    )
                    if command_handler:
                        print("Command found, executing", command_handler)
                        command_data = command.get("data") or {}
                        response = command_handler(
                            **{"pipe_name": pipe_name, **command_data}
                        )
                if response:
                    write_to_pipe(pipe, response)

    def run(self):
        # self.handle_commands(f"left_eye_commands", event)
        with ThreadPoolExecutor(max_workers=2) as executor:
            for pipe_definition in self.pipe_definition.items():
                pipe_name, data_queue = pipe_definition
                executor.submit(self.handle_commands, f"{pipe_name}_commands", event)
                executor.submit(
                    self.stream_data, f"{pipe_name}_stream", data_queue, event
                )


if __name__ == "__main__":
    event = Event()
    pipes = {
        "left_eye": Queue(),
        "right_eye": Queue(),
    }

    ipc_client = IPCClient(event=event, pipe_definition=pipes)
    ipc_client.run()
