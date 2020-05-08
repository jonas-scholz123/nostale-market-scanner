import time
import sys
import win32pipe, win32file, pywintypes
import threading
import queue
import pymongo
import pandas as pd
import psutil
from pprint import pprint

from send_server import Send_server
from read_server import Read_server
from db_handler import DB_handler
from injector import Injector

class Packet_handler():

    def __init__(self):
        print("initialising Packet handler")
        self.active = True
        self.buf_size = 10 # buf size for queue
        self.read_q = queue.Queue(self.buf_size)
        self.write_q = queue.Queue(self.buf_size)

        #needed for dll injection
        self.paths_dll = [r"C:\Users\jonas\Desktop\nostale-packet-sender-master\nostale-packet-sender-master\build\nostale_packet_sender.dll",
                    r"C:\Users\jonas\Desktop\nostale-packet-sender-master\nostale-packet-publisher-master\build\nostale_packet_publisher.dll"]
        self.pid = self.get_pid("NostaleClientX.exe")
        self.inject_dlls()

        # read csv to find which items to scan:
        self.ID_csv_path = "../name_to_id.csv"
        self.get_scannables()
        print(self.scannables)

        # init database handler
        self.DB = DB_handler()

        #start Read Pipe
        self.RS = Read_server(self.read_q)

        #start Send Pipe
        self.SS = Send_server(self.write_q)

        self.RS.start()
        self.SS.start()


        return

    def get_pid(self, process_name):
        for proc in psutil.process_iter():
            try:
               if proc.name() == process_name:
                   self.pid = proc.pid
                   return proc.pid
            except (psutil.AccessDenied):
               pass

        print("Can not find Nostale, terminating.")

    def inject_dlls(self):
        injector = Injector()

        # Load the process from a given pid
        injector.load_from_pid(self.pid)

        # Inject the DLL
        for path_dll in self.paths_dll:
            injector.inject_dll(path_dll)

        # Unload to close the process handle.
        injector.unload()


    def get_scannables(self):
        packetIDs = pd.read_csv(self.ID_csv_path)
        scannables = packetIDs[packetIDs["toScan"] == 1].copy()
        self.scannables = scannables.drop("toScan", axis = 1)
        return

    def set_packet_not_working(self, itemID):
        packetIDs = pd.read_csv(self.ID_csv_path)
        packetIDs.loc[packetIDs["itemID"] == itemID, "packetWorks"] = 0
        packetIDs.to_csv(self.ID_csv_path, index=False)

    def parser(self, packet):
        """Reads packet, seperates commands, args """
        if packet.startswith("send"):
            return # TODO:  implement checks
        elif packet.startswith("recv"):
            split_packet = packet.split(" ")
            p_command = split_packet[1]
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

        self.market_scanner()

    def market_scanner(self):
        self.open_bazaar()
        print("basar opened")
        time.sleep(3)

        while True:
            for itemID, item_name, replacement_packet, packet_works in self.scannables.values:

                if not packet_works:
                    if replacement_packet:
                        packet = replacement_packet
                    else:
                        print("packet for ", item_name, "doesn't work, moving on...")
                        continue
                else:
                    packet = "c_blist  0 0 0 0 0 0 0 0 1 " + str(int(itemID))

                print("sending packet ", packet, " to search for ", item_name)
                success = self.search_bazaar(packet, item_name)
                if not success:
                    self.set_packet_not_working(itemID)
                time.sleep(1.5)
            time.sleep(1200)
            self.get_scannables() #refreshes csv

        return

    def wait_for_response(self, exp_command, timeout = 10): #timeout  in seconds

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
                    return received, r_command, r_args
            else:
                time.sleep(refresh_time)
                t_counter += 1
        return received, 0, 0

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

    def search_bazaar(self, packet, item_name):
        # loop through db and send nostale_packet_IDs


        self.SS.send_packet(packet)
        received, r_command, r_args = self.wait_for_response("rc_blist")
        if received:
            success, entry_df = self.parse_basar_search(r_args)
            if not success: return False
            entry_df.insert(1, "itemName", [item_name for i in range(len(entry_df.index))])
            self.DB.insert_entry(entry_df)
        else:
            print("No response was received. Moving on to next packet.")

        return True

    def parse_basar_search(self, search_args):
        '''search_args = list of packet arguments returned by search_bazaar package.
                         Each packet is one bazaar entry'''
        entries = search_args[1:]
        entry_df = pd.DataFrame([e.split("|") for e in entries])
        if len(entry_df.columns) < 14:
            print("Basar search failed.")
            return False, 0
        entry_df.columns = ["basarID", "sellerID", "sellerName", "itemID", "quantity", #_id = basarID
                            "unknown3", "price", "expiryTime", "unknown4", "unknown5",
                            "unknown6", "unknown7", "unknown8", "unknown9", "unknown10"]


        to_drop = [entry for entry in entry_df.columns.tolist() if entry.startswith("unknown")]

        entry_df.drop(labels = to_drop, axis = 1, inplace = True)
        entry_df.dropna(inplace = True)

        return True, entry_df



    def get_search_packet(self, db, item_name):
        """ Searches db by item name and returns bazaar search packet"""
        return search_packet



if __name__ == "__main__":
    Handler = Packet_handler()
    Handler.run()
