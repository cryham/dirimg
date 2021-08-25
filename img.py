#!/usr/bin/python3
#!/usr/bin/env python3
import os
import shutil
import hashlib
from pathlib import Path
from PIL import Image, ImageChops, ImageStat


#  options: start path, etc.
#  also see below:  Main - start setup
#------------------------------------------------------------------------------------------

start_dir = os.getcwd()
#start_dir += '/img-test'  # test

recursive = True
useGroups = True
#useGroups = False


#------------------------------------------------------------------------------------------
print('Path: ' + start_dir)
print('---------------------------------------------')

#  const
data = Path(os.path.realpath(__file__)).parent
crops_dir = os.path.join(data, 'img-crops')

#  var
prevImgGrp = None
prevPath = ''
count = 0  # all files

#  classes

#------------------------------------------------------------------------------------------
class Crop:

	#  const
	cimg = 0         # crop image
	rect = (0,0,1,1) # crop rect
	rectGrp = None   # group hash rect
	subdir = 'a'     # moves img inside, if crop matches
	#  var
	moved = 0    # images moved
	grouped = 0  # images grouped
	groups = 0   # groups count

	def __init__(self, rect, fname, subdir, rectGroup):
		try:
			fpath = os.path.join(crops_dir, fname)
			self.rect = rect
			self.rectGrp = rectGroup
			self.subdir = subdir
			cimg = Image.open(fpath)
			self.cimg = cimg.crop(self.rect)
		except Exception as ex:
			print("Crop failed: " + fpath + ' ' + str(ex))
			exit(1)


	#  return if img crop different
	def imgDiff(self, img, rect, img2, fpath = None):

		crimg = img.crop(rect)  # img2 already cropped with rect
		diff = ImageChops.difference(crimg, img2)

		if diff.getbbox():  # has differences
			stat = ImageStat.Stat(diff)
			ratio = sum(stat.mean) / (len(stat.mean) * 255) * 100

			if fpath != None:  # test
				print(self.subdir + '  {:.2f} %  '.format(ratio) + fpath)

			return ratio < 1.0  ## par  same if not much
		else:
			if fpath != None:  # test
				print(self.subdir + '  same  ' + fpath)
			return True  # same exactly


	#  move into subdir, adds subdir to path
	def moveTo(self, fpath, subdir):

		path = Path(fpath)
		file = path.parts[-1]
		new_path = os.path.join(path.parent, subdir)
		
		if not os.path.exists(new_path):
			os.mkdir(new_path)
		shutil.move(fpath, new_path)
		self.moved += 1


	def CheckGroup(self, img, fpath):
		global prevImgGrp
		global prevPath

		if self.rectGrp != None:
			#  check same group area if crop has it
			same = False
			if prevImgGrp == None:
				#  store 1st in group
				#  todo: add to list, min count to move?
				prevImgGrp = img.crop(self.rectGrp)
				prevPath = fpath
				#prevImgGr.show()
				return True
			else:
				same = self.imgDiff(img, self.rectGrp, prevImgGrp) #, fpath)
			
			#print('y' if same else 'n')
			if same:
				#  get hash from image, for subidr name
				md5hash = hashlib.md5(prevImgGrp.tobytes())
				subdir = self.subdir + '-' + md5hash.hexdigest()[0:6]
				#print(subdir)
				self.moveTo(fpath, subdir)
				self.grouped += 1
				
				if prevPath != '':
					self.groups += 1  # group end
					self.moveTo(prevPath, subdir)
					prevPath = ''
				return True
			else:
				prevImgGrp = img.crop(self.rectGrp)
				prevPath = fpath
				return True
			pass
		else:
			prevImgGrp = None
		return False


	#  Check One crop for match on image, and group crop
	def CheckOne(self, img, fpath):

		move = self.imgDiff(img, self.rect, self.cimg) #, fpath)
		if move:
			if useGroups:
				if self.CheckGroup(img, fpath):
					return True
			
			self.moveTo(fpath, self.subdir)
		else:
			prevImgGrp = None
			prevPath = ''
		return move


#------------------------------------------------------------------------------------------
class Crops:

	all = list()  # all Crop images, const
	moved = 0
	last = -1  # last crop that matched, id to all

	def add(self, rect, fname, subdir, rectGrp = None):
		self.all.append(Crop(rect, fname, subdir, rectGrp))


	#  path check, skip if subdir is in crops, from previous run
	def pathChk(self, fpath):

		dir = Path(fpath).parts[-2]  # last subdir

		for c in self.all:
			if dir == c.subdir or dir.startswith(c.subdir + '-'):
				#  skip crop made subdirs (^grouped too), already moved
				return True
		return False


	#  Check All crops for matches on image
	def CheckAll(self, img, fpath):
		
		#  first, try last one matched, again (speed up)
		if self.last >= 0:
			cr = self.all[self.last]
			if cr.CheckOne(img, fpath):
				self.moved += 1
				return True
		
		#  check all
		i = 0
		for cr in self.all:
			#if i != self.last:
			if cr.CheckOne(img, fpath):
				self.moved += 1
				self.last = i
				return True
			i += 1
		
		self.last = -1
		return False


	#  print end summary
	def EndStats(self):
		
		grouped = 0
		groups = 0
		for cr in self.all:  # all crop dirs
			grp = ''
			if cr.grouped > 0:
				grouped += cr.grouped
				groups += cr.groups
				grp = '  grp ' + str(cr.grouped) + '  G ' + str(cr.groups)

			cnt = str(cr.moved) + grp  if  cr.moved > 0  else  '-'
			#  right align
			print('{:>12}'.format(cr.subdir) + '  ' + cnt)

		global count  # total
		grp = ''
		if grouped > 0:
			grp = '  grp ' + str(grouped) + '  G ' + str(groups)
		perc = '{:.2f} %  {} / {} '.format(100.0 * self.moved / count, self.moved, count)
		print('Moved:  ' + perc + grp)



#  Process
#------------------------------------------------------------------------------------------
def ProcessFile(dir, fname):
	
	fpath = os.path.join(dir, fname)
	if not os.path.isfile(fpath):
		return

	global count
	count += 1

	#fspl = os.path.splitext(fname)
	#fne = fspl[0]  # fname no ext
	#ext = fspl[1]
	#fpath2 = os.path.join(dir, fne+'!'+ext)
	
	try:
		img = Image.open(fpath)
		if crops.pathChk(fpath):
			return

		#print(str(img.size[0]) + ',' + str(img.size[1]) + '  ' + fpath)
		if crops.CheckAll(img, fpath):
			return
		
	except Exception as ex:
		print(fpath + ' ' + str(ex))
		pass



#------------------------------------------------------------------------------------------
#  Main - start setup
#  Load crop images
#------------------------------------------------------------------------------------------
crops = Crops()
crops.add(416,5, 500,20, '1.jpg', '1')
## todo: adjust, add more here ..


#  Main get loop
#------------------------------------------------------------------------------------------
if not recursive:
	files = os.listdir(start_dir)

	files.sort()
	for fname in files:
		ProcessFile(start_dir, fname)
else:
	for dir, subdirs, files in os.walk(start_dir):
		if dir.find('/.') != -1:  # skip hidden
			continue

		files.sort()
		for fname in files:
			ProcessFile(dir, fname)

crops.EndStats()
