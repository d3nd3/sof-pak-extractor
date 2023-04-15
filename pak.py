#i 	int
#c 	char


import sys
import struct
import os


"""
id	4 byte string	Should be "PACK" (not null-terminated).
offset	Integer (4 bytes)	Index to the beginning of the file table.
size	Integer (4 bytes)	Size of the file table.

You can determine the number of files stored in the .pak file by dividing the "size" value in the header by 64 (the size of the file entry struct)
"""


def find_file_in_pak(filename_glob,pakpathname):
	with open(os.path.abspath(pakpathname),'rb') as f:
		the_pak = bytearray(f.read())

	# get the directory offset
	dir_off = struct.unpack_from('<i', the_pak, 4)[0]
	print(f"dir off is {dir_off}")

	dir_len = struct.unpack_from('<i', the_pak, 8)[0]
	print(f"dir len is {dir_len}")

	found_file = {}

	index = 0
	# iterate the directory
	while index < dir_len:
		# read the relative_path from the directory
		# cant assume its null byte padded
		# search for dot or find nearest null byte from left
		rel_path = struct.unpack_from('56s',the_pak,dir_off+index)[0].split('\x00')[0].lower()
		if filename_glob in rel_path:
			print("found the file")
			found_file['path'] = rel_path
			# read the offset the file is stored at from the directory
			found_file['pos'] = struct.unpack_from('<i',the_pak,dir_off+index+56)[0]
			# read the size of the file
			found_file['size'] = struct.unpack_from('<i',the_pak,dir_off+index+60)[0]
			break
		# print "rel path is " + rel_path
		index += 64


	return the_pak[found_file['pos']:found_file['pos'] +found_file['size']]


"""
pak_in_data is a directory containing all the pak data to be packed
"""
def createpak(data_in_dir,pak_out):
	
	file_address_book = []
	#running totals, fpos starts at 12
	tsize = 0
	fpos = 12

	# print "data_in_dir : " + data_in_dir

	# eg. data_in_dir = "fsm"
	# grab info from all files in folder recursively
	for root, dirs, files in os.walk(data_in_dir):
		# root is same as data_in_dir supplied root = "fsm"
		# files in current directory
		for f in files:
			# data_in_dir + filename (relativeness depends on data_in_dir) eg. "pakdata/textures/sprite.m32"
			full_path = os.path.join(root,f)
			# path relative to 'root' directory passed to function eg. "textures/sprite.m32"
			fpath_rel = os.path.relpath(full_path,data_in_dir).replace("\\","/")
			# figures out the absolute path if its relative eg. "c:/pakdata/textures/sprite.m323"
			fpath_abs = os.path.abspath(full_path)
			
			fsize = os.path.getsize(fpath_abs)
			tsize += fsize
			file_address_book.append( 
									  {
										"path_rel": fpath_rel.lower(),
										"path_abs" : fpath_abs,
										"size": fsize,
										"pos": fpos
									  }
									)
			fpos+=fsize        

	print(f"total files = {len(file_address_book)}") #855
	print(f"total filesize = {tsize}")
	header = 12 #bytes #(4c+2ints)
	dirofs = tsize + 12
	dirlen = len(file_address_book)*64
	mypakfile = bytearray(header + dirlen + tsize)
	struct.pack_into('4s',mypakfile,0,'PACK')
	struct.pack_into('<i',mypakfile,4,dirofs)
	struct.pack_into('<i',mypakfile,8,dirlen)
	for entry in file_address_book:
		with open(entry["path_abs"], 'rb') as f:
			# print " size is : " + str(entry["size"])
			# mypakfile.extend(bytearray(f.read()))
			mypakfile[entry["pos"]:entry["pos"] + entry["size"]] = bytearray(f.read())
	index=0
	#to write a formula instead
	#offset = a + b + c
	for entry in file_address_book:
		#dirofs += (index * 64)
		# it pads it with null bytes, good
		struct.pack_into('56s',mypakfile,dirofs+ 0 + (index*64),entry["path_rel"])  #entry["pos"]

		struct.pack_into('<i',mypakfile,dirofs+56+(index*64),entry["pos"])
		# print " size is : " + str(entry["size"])
		struct.pack_into('<i',mypakfile,dirofs+60+(index*64),entry["size"])
		index+=1 
	#just write it here for now
	with open(pak_out, 'wb') as f:
		print(f"writing out {pak_out}")
		f.write(mypakfile)


def unpack_pak(pak_file, unpack_loc):
	with open(pak_file,'rb') as f:
		the_pak = bytearray(f.read())

	# get the directory offset
	dir_off = struct.unpack_from('<i', the_pak, 4)[0]
	# print "dir off is " + str(dir_off)
	dir_len = struct.unpack_from('<i', the_pak, 8)[0]
	# print "dir len is " + str(dir_len)

	index = 0
	# iterate the directory
	while index < dir_len:
		# read the relative_path from the directory
		file = {}
		file['path'] = struct.unpack_from('56s',the_pak,dir_off+index)[0].split(b'\x00')[0].lower().decode("utf-8")
		# print ":".join("{:02x}".format(ord(c)) for c in file['path'])
		file['pos'] = struct.unpack_from('<i',the_pak,dir_off+index+56)[0]
		file['size'] = struct.unpack_from('<i',the_pak,dir_off+index+60)[0]
		index += 64

		fullpath = os.path.join(unpack_loc,file['path'])
		
		# print fullpath
		dirpath = os.path.dirname(fullpath)
		if ( not os.path.exists(dirpath) ):
			os.makedirs(dirpath)
		try:
			with open( fullpath,'wb' ) as f:
				f.write(the_pak[file['pos']:file['pos'] +file['size']])
		except IOError:
			sys.exit(1)

# createpak("/mnt/c/users/dende/desktop/semiworking","/mnt/c/users/dende/desktop")
# createpak("fsm",".")
# unpack_pak('crash.pak',"dog")

# with open("haha.txt",'wb') as f:
# 	text = find_file_in_pak("sofplus.cfg","sofplus.pak")
# 	f.write(text)

# sys.argv[0] is python script name
# unpack bla.pak outdir

# python script.py unpack file.pak outdir
if sys.argv[1] == "unpack" and len(sys.argv) == 4:
	unpak_this = sys.argv[2]
	to_here = sys.argv[3]
	unpack_pak(unpak_this,to_here)

# python script.py unpack indir outfile
if sys.argv[1] == "pack" and len(sys.argv) == 4:
	pak_this = sys.argv[2]
	out_pak = sys.argv[3]
	createpak(pak_this,out_pak)
	# os.rename('packme_tmp','dontpackme_tmp')



