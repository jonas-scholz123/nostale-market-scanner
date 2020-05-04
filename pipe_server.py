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

    def run(self):
        self.create_pipe()
        self.wait_for_connection()

        while self.active:
            if not self.read_q.full():
                self.read_q.put(self.read_packet())

class Send_server(threading.Thread):

    def __init__(self, write_q):

        # run in thread
        threading.Thread.__init__(self)
        self.daemon = True

        self.pipe_name = r'\\.\pipe\nt_snd_42'
        self.active = True

        self.write_q = write_q
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

        while self.active:
            time.sleep(0.1)
            if not self.write_q.empty():
                packet = write_q.get()
                self.send_packet(packet)


class Packet_handler():

    def __init__(self):
        print("initialising Packet handler")
        self.active = True
        self.buf_size = 10 # buf size for queue
        self.read_q = queue.Queue(self.buf_size)
        self.write_q = queue.Queue(self.buf_size)

        #start Read Pipe
        self.RS = Read_server(self.read_q)

        #start Send Pipe
        self.SS = Send_server(self.write_q)

        self.RS.start()
        self.SS.start()

        return

    def parser(self, packet):
        """Reads packet, seperates commands, args """
        if packet.startswith("send"):
            return # TODO:  implement checks
        elif packet.startswith("recv"):
            split_packet = packet.split(" ")
            p_command = split_packet[0]
            p_args    = split_packet[1:]
            return p_command, p_args

    def encoder(self, p_command, p_args):
        """Encodes packet command, args into nostale-readable packet """
        p_args_str = [str(arg) for arg in p_args] #make str
        return " ".join([p_command] + p_args_str)

    def run(self):
        while self.active:
            time.sleep(0.1) # TODO: REMOVE FOR PRODUCTION
            if not self.read_q.empty():
                print(self.read_q.qsize(), " items in read queue")
                print("latest item: ", self.read_q.get())
            if not self.write_q.empty():
                print(self.write_q.qsize(), " items in write queue")
                print("latest item: ", self.write_q.get())


if __name__ == "__main__":
        Handler = Packet_handler()
        Handler.run()
