import time
import sys
import win32pipe, win32file, pywintypes
import threading
import queue
import pymongo
import pandas as pd
from pprint import pprint
import datetime

class DB_handler():

    def __init__(self):
        self.localhost_adress = "mongodb://localhost:27017/"
        self.db_client = pymongo.MongoClient(self.localhost_adress)

        self.db = self.db_client["db"]
        self.basarframe = self.db["basarframe"]

    def insert_entry(self, df):

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        df.insert(len(df.columns), "timestamp", [timestamp for i in range(len(df.index))])
        records = df.to_dict('records')
        self.basarframe.insert_many(records)
        return

    def print_db(self):
        cursor = DBH.basarframe.find({})
        for doc in cursor:
            pprint(doc)
        return

    def wipe_db(self):
        self.db_client.drop_database("db")
        return


if __name__ == "__main__":
    DBH = DB_handler()
    DBH.print_db()
