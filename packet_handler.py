import time
import sys
import win32pipe, win32file, pywintypes
import threading
import queue

from send_server import Send_server
from read_server import Read_server

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
        while not (self.SS.connected and self.RS.connected):
            time.sleep(1)

            if not self.SS.connected:
                print("waiting for send server connection")
            if not self.RS.connected:
                print("waiting for read server connection")

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

    def parse_basar_search(self, search_args):
        '''search_args = list of packet arguments returned by search_bazaar package.
                         Each packet is one bazaar entry'''

        entries = args[1:]

        entry_df = pd.DataFrame([e.split("|") for e in entries])
        entry_df.columns = ["basarID", "sellerID", "sellerName", "itemID", "quantity",
                            "unknown3", "price", "expiryTime", "unknown4", "unknown5",
                            "unknown6", "unknown7", "unknown8", "unknown9", "unknown10"]
        return entry_df



    def get_search_packet(self, db, item_name):
        """ Searches db by item name and returns bazaar search packet"""
        return search_packet


if __name__ == "__main__":
        Handler = Packet_handler()
        Handler.run()
