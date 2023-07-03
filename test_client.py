from time import sleep

import pywintypes
import win32file
import win32pipe

handle = None
if __name__ == "__main__":
    try:
        while handle is None:
            try:
                handle = win32file.CreateFile(
                    r"\\.\pipe\left_eye_commands",
                    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32file.OPEN_EXISTING,
                    0,
                    None,
                )
                print("Pipe acquired")
            except pywintypes.error:
                print("Waiting for pipe to be created")
                # the named pipe doesn't exist yet, let's wait
                sleep(1)

        win32pipe.SetNamedPipeHandleState(
            handle, win32pipe.PIPE_ACCESS_DUPLEX, None, None
        )
        win32file.WriteFile(handle, b'{"command": "start"}')
        while True:
            try:
                win32file.WriteFile(handle, b'{"command": "read_address"}')
                resp = win32file.ReadFile(handle, 64 * 1024)
                print(f"message: {resp}")
                sleep(1)
            except pywintypes.error:
                print("Error reading")
                sleep(1)
    except:
        print("Exiting")
        if handle:
            print("Closing the pipe connection")
            handle.close()
