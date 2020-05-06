import time
import sys
import win32pipe, win32file, pywintypes
import threading
import queue

class Send_server(threading.Thread):

    def __init__(self, write_q):

        # run in thread
        threading.Thread.__init__(self)
        self.daemon = True

        self.pipe_name = r'\\.\pipe\nt_snd_42'
        self.active = True

        self.write_q = write_q
        self.connected = False
        return

    def create_pipe(self):
        self.pipe = win32pipe.CreateNamedPipe(
                self.pipe_name,
                win32pipe.PIPE_ACCESS_DUPLEX,
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                1, 65536, 65536,
                0,
                None)
        return

    def wait_for_connection(self):
        try:
            print("Waiting for sending client")
            win32pipe.ConnectNamedPipe(self.pipe, None)
            print("got sending client")
            return
        except:
            print("Waiting for Client failed, closing handle")
            win32file.CloseHandle(self.pipe)

    def send_packet(self, s):
        data = str.encode(s)
        win32file.WriteFile(self.pipe, data)
        return

    def run(self):
        self.create_pipe()
        self.wait_for_connection()
        self.connected = True

        while self.active:
            time.sleep(0.1)
            if not self.write_q.empty():
                packet = write_q.get()
                self.send_packet(packet)
