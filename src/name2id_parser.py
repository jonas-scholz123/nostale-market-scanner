import pandas as pd

fpath_items = "../data/items.dat"
fpath_shortcodes = "../data/shortcodes_map.txt"
#df = pd.read_table("data/items.dat")
#df

shortcodes_content = open(fpath_shortcodes).readlines()

shortcode2name = {}

for line in shortcodes_content:
    splitline = line.split()

    if not splitline:
        continue

    shortcode = splitline[0]
    name = " ".join(splitline[1:])

    shortcode2name[shortcode] = name


import re

datContent = [i.split() for i in open(fpath_items).readlines()]
#datContent = " ".join(open(fpath_items).readlines()).split("#")
#datContent = open(fpath_items).readlines()
#print(datContent[10].split("\t"))

name2id = {}

for (i, line) in enumerate(datContent):
    if not line: continue
    if line[0] == "VNUM":
        itemID = line[1]
        #print("itemID: ", itemID)
    if len(datContent) <= i + 1: break

    if not datContent[i+1]: continue
    if datContent[i + 1][0] == "NAME":
        #print(datContent[i+1])
        #print(itemID)
        shortcode = datContent[i + 1][1]
        try:
            name = shortcode2name[shortcode]
            name2id[name] = itemID
        except(KeyError):
            continue

from pprint import pprint

name_and_id = [(k, v) for k, v in name2id.items()]
df = pd.DataFrame(name_and_id, columns = ["itemName", "itemID"])
df.set_index("itemID", inplace = True)
df.insert(1, "toScan", 0)
df.insert(2, "packetWorks", 1)
df.insert(2, "replacementPacket", 0)

df.to_csv("../name_to_id.csv")
#%%
#import requests
#url = "https://raw.githubusercontent.com/KILL009/Parse-Of-Opennos-All-Languaje-/master/Parse-DE/_code_DE_Item.txt"
#r = requests.get(url)
#
#with open('shortcodes_map.txt', 'wb') as f:
#    f.write(r.content)
