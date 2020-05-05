
import time
import sys
import win32pipe, win32file, pywintypes
import threading
import queue

class Read_server(threading.Thread):

    def __init__(self, read_q):
        # run in thread
        threading.Thread.__init__(self)
        self.daemon = True

        self.pipe_name = r'\\.\pipe\nt_pub_1337'
        self.active = True
        self.connected = False

        self.blacklist = ["stat"]

        self.read_q = read_q
        return

    def create_pipe(self):
        self.pipe = win32pipe.CreateNamedPipe(
                self.pipe_name, #        r'\\.\pipe\nt_snd_42',
                win32pipe.PIPE_ACCESS_DUPLEX,
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                1, 65536, 65536,
                0,
                None)

    def wait_for_connection(self):
        try:
            print("waiting for client")
            win32pipe.ConnectNamedPipe(self.pipe, None)
            print("got client")
            return
        except:
            print("Waiting for Client failed, closing handle")
            win32file.CloseHandle(self.pipe)

    def read_packet(self):
        return str(win32file.ReadFile(self.pipe, 64*1024)[1])[2: -3] #take index 1 element = message, turn into str and clean up.

    def should_ignore(self, packet):
        sendrcv, command = packet.split(" ")[0:2]
        if sendrcv == "send":
            return True

        if command in self.blacklist:
            return True

        return False


    def run(self):
        self.create_pipe()
        self.wait_for_connection()
        self.connected = True

        while self.active:
            if not self.read_q.full():
                packet = self.read_packet()
                if not self.should_ignore(packet):
                    self.read_q.put(packet)
                    print("passing packet ", packet, " on to handler")
