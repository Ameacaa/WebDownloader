from Anitube import StringReplace, GetFilesFromPath, TimeTake
from File import Anime, Episode, LoadFile
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from pathlib import Path
import os, sys, time

DOWNLOAD_FOLDER_PATH = Path('E:/Videos')


def RenameFile( status: bool, filename: str, download_path: Path ):
	if status:
		old_name = Path( download_path / filename )
		index = filename.find('-ep-')
		new_name = StringReplace(filename[index:], '', ['-'], True) if index != -1 else filename
		new_name = Path( download_path / new_name )
		os.rename(old_name, new_name)


def GetDownloadLink( driver: webdriver, episode: Episode ) -> str:
	downloadLink = ''
	driver.get( episode.link )
	try:
		button = driver.find_element( By.CLASS_NAME, 'download' )
		driver.implicitly_wait(1)
		button.submit()
		driver.implicitly_wait(1)
		downloadLink = driver.find_element( By.CLASS_NAME, 'download' ).get_property( 'href' )
	except:
		print( f'The download link has not been found, try manually: {episode.link}' )
	return downloadLink


def OpenHeadlessChrome( download_path: Path ):
	op_chrome = webdriver.ChromeOptions()
	op_chrome.add_argument('--headless=new')
	op_chrome.add_experimental_option( 'prefs', { 'download.default_directory': download_path }  )
	driver = webdriver.Chrome(options=op_chrome)
	return driver


def WaitDownload( path: str ) -> tuple:
	downloading_file = ''

	# Find the downloading file
	for retries in range(100):
		time.sleep(0.2)
		file = GetFilesFromPath( path, ['.crdownload'], True )
		if len( file ) == 1:
			downloading_file = file[0]
			break
	n_files = len( GetFilesFromPath( path ) )
	# Check if download file has been found
	if downloading_file == '':
		print('File not found after 200 retries (~20 seconds) -- Passing this file')
		return (False, '')
	
	while len( GetFilesFromPath( path, ['.crdownload'] ) ) != 0:
		time.sleep(0.5)
	
	return (True, downloading_file) if n_files == len( GetFilesFromPath(path) ) else (False, '')

@TimeTake
def Download( forceDownload: bool = False ) -> None:
	animes = LoadFile()
	if len(animes) == 0:
		print('No animes to download')
		quit()

	for anime in animes:
		# Path to download anime and Create folder if not exist
		download_path = Path( DOWNLOAD_FOLDER_PATH / anime.title / anime.season )
		download_path.mkdir(parents=True, exist_ok=True)
		# Check if already download anime
		if not forceDownload and len(anime.episodes) == len( GetFilesFromPath( download_path, ['.mp4'] ) ):
			continue

		# Open Chrome with options
		driver = OpenHeadlessChrome( str(download_path) )
		
		next_percent = 100/20
		print(f'Downloading {anime.title:>20} - Expected({len(anime.episodes)*70/60} mins):\n[' + '-'*20 +']\t[', end='')
		for i, episode in enumerate(anime.episodes):
			if not forceDownload and episode.name in GetFilesFromPath( download_path, ['.mp4'], True ):
				continue

			driver.get( GetDownloadLink( driver, episode ) ) # Download
			status, filename = WaitDownload( download_path ) # Wait download ends
			RenameFile( status, filename, download_path ) # Rename file

			while float( (i+1) / len(anime.episodes) * 100 ) >= next_percent:
				next_percent += 100/20
				print(f'-', end='')
			sys.stdout.flush()
		print(']')

