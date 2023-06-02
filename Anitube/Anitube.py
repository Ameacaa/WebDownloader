from functools import wraps
import time, os



def GetFilesFromPath(
	path: str, 
	fileExtension: list[str] = None,
	removeExtension: bool = False,
) -> list[str]:
	'''Get files from folderPath'''

	# Get all files from path
	allFiles = [ f for f in os.listdir(path) if os.path.isfile( os.path.join(path, f) ) ]
	
	# Return all files
	if fileExtension == None:
		return [os.path.splitext(file)[0] for file in allFiles] if removeExtension == True else allFiles

	# Get files with the extention file
	files = []
	for file in allFiles:
		filename, extention = os.path.splitext(file)
		if extention in fileExtension:
			files.append(file if not removeExtension else filename)
	return files


def TimeTake(func):
	@wraps(func)
	def TimeTake_wrapper(*args, **kwargs):
		begin = time.monotonic_ns()
		result = func(*args, **kwargs)
		timetake = (time.monotonic_ns() - begin) / 1_000_000_000
		print(f'Time taken ({func.__name__}): {timetake:.3f} seconds')
		return result
	return TimeTake_wrapper


def StringReplace(
	text: str,
	newChar: str= '-',
	oldChars: list = ['\\', '/', ':', '*', '?', '"', '<', '>', '|'],
	appendInOldChars: bool = False,
	stripText: bool = True
) -> str:
	'''
	Return a string replacing oldChars with the newChar\n
	oldChars by default are invalid WindowsOS character for files and folders
	'''
	# Append or not the olds list
	if appendInOldChars:
		oldChars = oldChars + ['\\', '/', ':', '*', '?', '"', '<', '>', '|']

	# Replacing strings
	for oldChar in oldChars:
		text = text.replace( oldChar, newChar )

	return text.strip() if stripText else text





