fname = input("Filename: ")
f = open(fname,"rb")
offset = 0x0
infile = True
while infile:
   addr = str(hex(offset)[2:].zfill(8))
   hexline = ""
   ascline = ""
   for x in range(0x10):
      byte = f.read(1)
      if len(byte) == 0: 
        hexline = hexline.ljust(48)
        infile = False
        break
      if ord(byte) > 29: 
        aschr = chr(byte[0])  
      else:
        aschr = "."
      ascline = ascline + aschr
      hexline = hexline + hex(byte[0])[2:].zfill(2) + " "
   print(addr+" "+hexline+" "+ascline)
   offset = offset + 0x10
f.close()