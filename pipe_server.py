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
            p_command = split_packet[1]
            print("understood command" , p_command)
            p_args    = split_packet[2:]
            return p_command, p_args

    def encoder(self, p_command, p_args):
        """Encodes packet command, args into nostale-readable packet """
        p_args_str = [str(arg) for arg in p_args] #make str
        return " ".join([p_command] + p_args_str)

    def run(self):
#        while self.active:
#            time.sleep(0.1) # TODO: REMOVE FOR PRODUCTION
#            if not self.read_q.empty():
#                print(self.read_q.qsize(), " items in read queue")
#                print("latest item: ", self.read_q.get())
#            if not self.write_q.empty():
#                print(self.write_q.qsize(), " items in write queue")
#                print("latest item: ", self.write_q.get())
        while not (self.SS.connected and self.RS.connected):
            time.sleep(1)
            print("waiting for active connection")
        self.open_bazaar()

    def wait_for_response(self, exp_command, timeout = 5): #timeout  in seconds

        print("waiting for response with command ", exp_command)

        t_counter = 0
        refresh_time = 0.1
        received = False

        while not received and t_counter < timeout/refresh_time:
            if not self.read_q.empty():
                r_command, r_args = self.parser(self.read_q.get())
                if r_command == exp_command: # if the return packet command matches the expected command, response is received
                    print("response received")
                    received = True
            else:
                time.sleep(refresh_time)
                t_counter += 1
        return received, r_command, r_args

    def open_bazaar(self):
        packets = []
        responses = [] #holds expected server responses
        #Click on NPC
        packets.append(self.encoder("npc_req", [2, 9264]))
        responses.append("npc_req")
        #Click on Basar oeffnen
        packets.append(self.encoder("n_run", [60, 0, 2, 9264]))
        responses.append("rc_blist")

        for p, r in zip(packets, responses):
            self.SS.send_packet(p)
            received = self.wait_for_response(r)[0]
            if not received:
                print("Response for opening bazaar has not been received. Terminating.")
                return False
        return True

    def search_bazaar(self):
        # loop through db and send nostale_packet_IDs
        # TODO: Jan help me set this up
        packets = []

        for p in packets:
            self.SS.send_packet(p)
            received, r_command, r_args = self.wait_for_response("rc_blist")
            if received:
                self.DB.make_entry(r_command, r_args)
            else:
                print("No response was received. Moving on to next packet.")

    def get_search_packet(self, db, item_name):
        """ Searches db by item name and returns bazaar search packet"""
        return search_packet


if __name__ == "__main__":
        Handler = Packet_handler()
        Handler.run()
