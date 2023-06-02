from dataclasses import dataclass, field
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import re
from pathlib import Path
import json
import os
import os.path
from colorama import init, Fore
import sys
import time
sys.path.append(r'D:\Projects\VideoDownloader') 
from Anitube import StringReplace, TimeTake, GetFilesFromPath


FILE_SCRAPER_PATH = Path(r'D:\Projects\VideoDownloader\Anitube\Animes.json')
# DOWNLOAD_FOLDER_PATH = Path(r'E:\Videos')
DOWNLOAD_FOLDER_PATH = Path(r'E:\zTEMP')


# -----------------------------
# ---------- Scraper ----------

@dataclass
class EpisodeClass:
	name: str = field(default_factory=str)# epNumber.mp4
	link: str = field(default_factory=str)# best link to dl

@dataclass
class AnimeClass:
	title: str = field(default_factory=str)# Folder name
	season: str = field(default_factory=str)# Subfolder name
	episodes: list[EpisodeClass] = field(default_factory=list)


def SaveFile( animeList: list[AnimeClass], rewrite:bool = False ) -> None:
	# Convert Anime class to dict (episode need to convert too)
	dictAnimes = [] # Anime dict (file data)
	for anime in animeList:
		dictEpisode = [] # Episode dict (file data)
		for episode in anime.episodes:
			dictEpisode.append(episode.__dict__)
		anime.episodes = dictEpisode # Tranform episodes to dict before convert anime to dict too
		dictAnimes.append(anime.__dict__)

	# Append to existing data
	if os.path.isfile( FILE_SCRAPER_PATH ) and not rewrite:
		with open( FILE_SCRAPER_PATH, 'r' ) as f:
			fileAnimes = json.load(f) # Get anime dict
		if len(fileAnimes) != 0:
			dictAnimes.extend(fileAnimes)
			dictAnimes = list(set(dictAnimes)) # Remove doubles
	
	# Save in file
	with open(FILE_SCRAPER_PATH, 'w') as f:
		json.dump(dictAnimes, f)

	print('File saved successfully')


def LoadFile() -> list[AnimeClass]:
	classAnimes = []
	with open( FILE_SCRAPER_PATH, 'r' ) as f:
		fileAnimes = json.load(f)
		for fileAnime in fileAnimes:
			anime = AnimeClass(**fileAnime) # Get the anime with episode in dict
			eps = [EpisodeClass(**episode) for episode in anime.episodes] # Convert ep dicts to ep class
			anime.episodes = eps # Set episode dict to episode class
			classAnimes.append(anime)
	return classAnimes





def GetAnimeInfos( soup: BeautifulSoup ) -> list[str]:
	''' Return anime infos in list -> ( 0 = Name, 1 = Season ) '''

	anime = ['Unknow Anime Name', 'Unknow Anime Season']

	try:
		anime[0] = StringReplace( soup.find('div', class_='anime_container_titulo').text, ' ', ['Baixar ', '-'], True, True )
	except:
		pass
	try:
		anime[1] = StringReplace( soup.find('div', class_='anime_container_titulo').text, ' ', ['Baixar ', '-'], True, True )
	except:
		pass

	return anime


def GetEpisodeInfos( soup_td: BeautifulSoup ) -> list[str]:
	''' Return episode infos in list -> ( 0 = Name, 1 = BestDownloadLink ) '''

	episode = ['Unknow Episode Name', 'Unknow Episode Link']

	# Get name (episode number)
	try:
		name = StringReplace( soup_td[0].text, '', [' '], True, True )
		start = name.find('ep')
		episode[0] = 'Not Found Episode Name' if start == -1 else name[start:]
	except:
		pass

	# Get download best link
	try:
		link = ''
		link = str(soup_td[3].a['href']).strip() # FHD
		if link != '':
			episode[1] = link
			return episode
	except:
		pass
	try:
		link = ''
		link = str(soup_td[2].a['href']).strip() # HD
		if link != '':
			episode[1] = link
			return episode
	except:
		pass
	try:
		link = ''
		link = str(soup_td[1].a['href']).strip() # FHD
		if link != '':
			episode[1] = link
			return episode
	except:
		pass

	return episode


def VerifyUrls( anitube_urls: list ) -> list[str]:
	'''Return the download page to scrape if the url is not from there'''
	
	downloadUrls: list[str] = []

	for url in anitube_urls:
		if re.search(r'https?:\/\/(www\.)?(anitube.vip\/)?(download)', url) != None:
			downloadUrls.append( url )

		# anime page
		elif re.search(r'https?:\/\/(www\.)?(anitube.vip\/)?[-a-zA-Z0-9]{1,256}(\/)[-a-zA-Z0-9]{1,256}', url) != None:
			soup = BeautifulSoup( requests.get(url).text, 'lxml' )
			try:
				downloadUrls.append( str( soup.find('a', class_='anime_downloadBTN')['href'] ).strip() )
			except:
				print(f'The download link for \'{url}\' is not found')	

		# seach page
		elif re.search(r'https?:\/\/(www\.)?(anitube.vip\/)?(busca.php)', url) != None:
			soup = BeautifulSoup( requests.get(url).text, 'lxml' )
			try:
				for anime in soup.find_all('div', class_='ani_loop_item_infos'):
					if str( anime.a.text ).strip().find('Dublado') != -1:
						continue
					for link_a in anime.find_all('a'):
						link = link_a['href']
						if re.search(r'https?:\/\/(www\.)?(anitube.vip\/)?(download)', link) != None:
							downloadUrls.append( link )
							break
			except:
				print(f'The download link for \'{url}\' is not found')
				continue
		else:
			print(f'\'{url}\' is not from anitube or something is wrong')
			continue

	return downloadUrls

@TimeTake
def Scrape( anitube_urls: list, newFile:bool=False ) -> None:
	'''
	Scrape Anitube Website and will put the informations in file\n
	anitube_urls: links from website anitube.vip\n
	newFile: If false, the scrape will append in file
	'''
	#os.system('cls')
	if len(anitube_urls) == 0:
		print('No Anitube Url insered')
		return
	animes: list[AnimeClass] = []
	anitube_urls = VerifyUrls( anitube_urls ) # Get download urls 
	for url in anitube_urls:
		soup = BeautifulSoup( requests.get(url).text, 'lxml' ) # HTML Parser
		animeInfos = GetAnimeInfos( soup )	
		episodeList: list[EpisodeClass] = []
		for soup_tr in soup.find('table', class_='downloadpag_episodios').find('tbody').find_all('tr'):
			episodeInfos = GetEpisodeInfos( soup_tr.find_all('td') )
			episodeList.append( EpisodeClass( name=episodeInfos[0], link=episodeInfos[1] ) )
		animes.append( AnimeClass(title=animeInfos[0], season=animeInfos[1], episodes=episodeList) )
	SaveFile( animes, newFile )


# ------------------------------
# ---------- Download ----------

def IsEpisodeAlreadyExist( episode: EpisodeClass, downloadPath: str ) -> bool:
	return episode.name in GetFilesFromPath( downloadPath, ['.mp4'], True )
	

def IsAnimeAlreadyExist( anime: AnimeClass, downloadPath: str ) -> bool:
	return os.path.isdir( downloadPath ) and len(anime.episodes) == len( GetFilesFromPath( downloadPath, ['.mp4'] ) )


def WaitDownload( downloadPath: str ) -> tuple:
	downloadingFile = ''

	# Find the downloading file
	for retries in range(100):
		time.sleep(0.2)
		file = GetFilesFromPath( downloadPath, ['.crdownload'], True )
		if len( file ) == 1:
			downloadingFile = file[0]
			break
	nFiles = len( GetFilesFromPath( downloadPath ) )
	# Check if download file has been found
	if downloadingFile == '':
		print('File not found after 200 retries (~20 seconds) -- Passing this file')
		return (False, '')
	
	while len( GetFilesFromPath( downloadPath, ['.crdownload'] ) ) != 0:
		time.sleep(0.5)
	
	return (True, downloadingFile) if nFiles == len( GetFilesFromPath(downloadPath) ) else (False, '')


def Download( forceDownload: bool = False ) -> None:
	animes = LoadFile()
	if len(animes) == 0:
		print(Fore.RED + 'No animes to download')
		quit()

	for anime in animes:
		# Path to download anime
		downloadPath = os.path.join( DOWNLOAD_FOLDER_PATH, anime.title )

		# Check if already exist this folder and files OR create folder to avoid problems
		if os.path.isdir( downloadPath ):
			if not forceDownload and IsAnimeAlreadyExist( anime, downloadPath ):
				continue
		else:
			os.mkdir( downloadPath )

		# Open Chrome with options
		opChrome = webdriver.ChromeOptions()
		opChrome.add_argument('--headless=new')
		opDownloadPath = { 'download.default_directory': downloadPath } 
		opChrome.add_experimental_option( 'prefs', opDownloadPath )
		driver = webdriver.Chrome(options=opChrome)

		
		nOfEpisodes = len(anime.episodes)
		nextValuePercent = 100/20
		print(f'Downloading {anime.title:>20}:\n[' + '-'*20 +']\t[', end='', flush=True)
		for i, episode in enumerate(anime.episodes):
			if not forceDownload and IsEpisodeAlreadyExist( episode, downloadPath ):
				continue

			# Open the episode link page and find the href of download button
			downloadLink = ''
			driver.get( episode.link )
			try:
				button = driver.find_element( By.CLASS_NAME, 'download' )
				driver.implicitly_wait(1)
				button.submit()
				driver.implicitly_wait(1)
				downloadLink = driver.find_element( By.CLASS_NAME, 'download' ).get_property( 'href' )
			except:
				print( Fore.RED + f'The download link has not been found, try manually: {episode.link}' )

			# Open the download link (it will download automatically)
			driver.get( downloadLink )

			# Rename file
			status, filename = WaitDownload( downloadPath )
			if status:
				old = os.path.join( downloadPath, filename)
				new = StringReplace(filename[filename.find('-ep-'):], '', ['-'], True) if filename.find('-ep-') is not -1 else filename
				new = os.path.join( downloadPath, new )
				os.rename(old, new)

			# Calc percentage
			while float( i+1 / (nOfEpisodes) * 100 ) >= nextValuePercent:
				print(f'-', end='', flush=True)
				nextValuePercent += 100/20
		print(']')

opChrome = webdriver.ChromeOptions()
opChrome.add_argument('--headless=new')
opDownloadPath = { 'download.default_directory': DOWNLOAD_FOLDER_PATH } 
opChrome.add_experimental_option( 'prefs', opDownloadPath )
driver = webdriver.Chrome(options=opChrome)