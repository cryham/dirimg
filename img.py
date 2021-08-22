#!/usr/bin/python3
#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
from PIL import Image, ImageChops, ImageStat


start_dir = os.getcwd()
#start_dir += '/img-test'

recursive = True


data = Path(os.path.realpath(__file__)).parent
crop_dir = os.path.join(data,'img-crops')


print('Path: ' + start_dir)
print('---------------------------------------------')


class Crop:
	rect = (0,0,1,1)  # crop rect
	cimg = 0
	subdir = 'a'  # moves img inside, if crop matches
	moved = 0

	def __init__(self, x1,y1,x2,y2, fname, subdir):
		try:
			fpath = os.path.join(crop_dir, fname)
			self.rect = (x1,y1,x2,y2)
			self.subdir = subdir
			cimg = Image.open(fpath)
			self.cimg = cimg.crop(self.rect)
		except Exception as ex:
			print(fpath + ' ' + str(ex))
			exit(1)
	
	def check(self, img, fpath):
		move = False

		crimg = img.crop(self.rect)
		diff = ImageChops.difference(crimg, self.cimg)
		if diff.getbbox():
			stat = ImageStat.Stat(diff)
			ratio = sum(stat.mean) / (len(stat.mean) * 255) * 100

			#print(self.subdir + '  {:.2f} %  '.format(ratio) + fpath)
			move = ratio < 1.0
		else:
			move = True
		
		if move:
			#  match, move into subdir
			#  add subdir to path
			path = Path(fpath)
			file = path.parts[-1]
			new_path = os.path.join(path.parent, self.subdir)
			
			if not os.path.exists(new_path):
				os.mkdir(new_path)
			shutil.move(fpath, new_path)
			self.moved += 1
		return move


class Crops:
	all = list()  # all Crop images
	moved = 0

	def add(self, x1,y1,x2,y2, fname, subdir):
		self.all.append(Crop(x1,y1,x2,y2, fname, subdir))

	#  check if subdir is in crops, from previous run
	def pathChk(self, fpath):
		dir = Path(fpath).parts[-2]  # last subdir

		for c in self.all:
			if dir == c.subdir:
				#  skip crop made subdirs, already moved
				return True
		return False

	def check(self, img, fpath):
		for cr in self.all:
			if cr.check(img, fpath):
				self.moved += 1
				return True
		return False

	def stats(self):
		for cr in self.all:
			print(cr.subdir + ' ' + str(cr.moved))
		print('All: ' + str(self.moved))


#  Process
#------------------------------------------------------------------------------------------
def process_file(dir, fname):
	fpath = os.path.join(dir, fname)
	if not os.path.isfile(fpath):
		return

	fspl = os.path.splitext(fname)
	fne = fspl[0]  # fname no ext
	ext = fspl[1]
	#fpath2 = os.path.join(dir, fne+'!'+ext)
	
	try:
		img = Image.open(fpath)
		if crops.pathChk(fpath):
			return

		#print(str(img.size[0]) + ',' + str(img.size[1]) + '  ' + fpath)
		if crops.check(img, fpath):
			return
		
	except Exception as ex:
		print(fpath + ' ' + str(ex))
		pass


#------------------------------------------------------------------------------------------

#  Load crop images
crops = Crops()
crops.add(416,5, 500,20, '1.jpg', '1')
## todo: adjust, add more here ..


#  Main get loop
#------------------------------------------------------------------------------------------
if not recursive:
	files = os.listdir(start_dir)

	files.sort()
	for fname in files:
		process_file(start_dir, fname)
else:
	for dir, subdirs, files in os.walk(start_dir):
		if dir.find('/.') != -1:  # skip hidden
			continue

		files.sort()
		for fname in files:
			process_file(dir, fname)

crops.stats()
