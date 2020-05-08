# nostale-market-scanner
Market scanner tool that checks prices for items and maintains a database of price developments in online mmo NosTale.

# How To Use:

0. Make sure you have installed all dependencies
1. Configure name_to_id.csv by setting toScan to 1 for all items that you want scanned
2. Start terminal as admin
3. Start Nostale
4. Move character next to Bazaar NPC
5. Run src/packet_handler.py

# Example Packet:

## c_blist  0 0 0 0 0 0 0 4 396 555 2047 3005 1 2195

p_command = c_blist: Search Bazaar

p_args[0] = 0: PacketIndex

p_args[1] = 0: TypeFilter

p_args[2] = 0: SubTypeFilter

p_args[3] = 0: LevelFilter

p_args[4] = 0: RareFilter

p_args[5] = 0: UpgradeFilter

p_args[6] = 0: OrderFilter

p_args[7] = 4: Unknown

p_args[8] = [396, 555, 2047, 3005, 1, 2195]: matched item IDs

For a full list of packets: https://github.com/NosCoreIO/NosCore.Packets
