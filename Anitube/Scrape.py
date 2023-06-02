from bs4 import BeautifulSoup
from File import Anime, Episode, SaveFile
from Anitube import StringReplace, TimeTake
import os, re, requests # Nao retirar os, senao o Anitube nao functiona


def GetAnimeInfos( soup: BeautifulSoup ) -> tuple:
	'''Return anime infos in list -> ( 0 = Name, 1 = Season )'''

	try:
		anime_name = StringReplace( soup.find('div', class_='anime_container_titulo').text, ' ', ['Baixar ', '-'], True, True )
		return (anime_name, 'S1')
	except:
		pass

	return ('NotFound', 'S1')


def GetEpisodeInfos( soup_td: BeautifulSoup ) -> tuple:
	'''Return episode infos in list -> ( 0 = Name, 1 = BestDownloadLink )'''

	episode_name = 'Unknow'

	# Get name (episode number)
	try:
		name = StringReplace( soup_td[0].text, '', [' '], True, True )
		start = name.find('ep')
		episode_name = 'Not_Found' if start == -1 else name[start:]
	except:
		pass

	# Get download best link
	try:
		link = ''
		link = str(soup_td[3].a['href']).strip() # FHD
		if link != '':
			return (episode_name, link)
	except:
		pass
	try:
		link = ''
		link = str(soup_td[2].a['href']).strip() # HD
		if link != '':
			return (episode_name, link)
	except:
		pass
	try:
		link = ''
		link = str(soup_td[1].a['href']).strip() # SD
		if link != '':
			return (episode_name, link)
	except:
		pass

	return (episode_name, 'NotFound')


def VerifyUrls( anitube_urls: list ) -> list[str]:
	'''Return the download page to scrape if the url is not from there'''
	
	download_urls: list[str] = []

	for url in anitube_urls:
		# download page
		if re.search(r'https?:\/\/(www\.)?(anitube.vip\/)?(download)', url) != None:
			download_urls.append( url )

		# anime page
		elif re.search(r'https?:\/\/(www\.)?(anitube.vip\/)?[-a-zA-Z0-9]{1,256}(\/)[-a-zA-Z0-9]{1,256}', url) != None:
			soup = BeautifulSoup( requests.get(url).text, 'lxml' )
			try:
				download_urls.append( str( soup.find('a', class_='anime_downloadBTN')['href'] ).strip() )
			except:
				print(f'The download url for \'{url}\' is not found')	

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
							download_urls.append( link )
							break
			except:
				print(f'The download url for \'{url}\' is not found')
				continue
		
		# not a anitube url
		else:
			print(f'\'{url}\' is not from anitube or something is wrong')
			continue

	return download_urls

@TimeTake
def Scrape( anitube_urls: list, overwrite_file:bool=False ) -> None:
	'''Scrape Anitube Website and will put the informations in file.
	anitube_urls: links from website 'anitube.vip'; overwrite_file: Overwrite or append file
	'''
	
	# Check urls inserted
	anitube_urls = VerifyUrls( anitube_urls ) # Get download urls
	if len(anitube_urls) == 0: # Check if have urls to scrape
		print('No anitube url found')
		return

	animes_list = []
	for url in anitube_urls:
		try:
			soup = BeautifulSoup( requests.get(url).text, 'lxml' ) # HTML Parser
			
			episode_list = []
			for soup_tr in soup.find('table', class_='downloadpag_episodios').find('tbody').find_all('tr'):
				episode_infos = GetEpisodeInfos( soup_tr.find_all('td') )
				episode_list.append( Episode(name=episode_infos[0], link=episode_infos[1] ) )
			
			anime_infos = GetAnimeInfos( soup )
			animes_list.append( Anime(title=anime_infos[0], season=anime_infos[1], episodes=episode_list) )
		except:
			print(f'Error scrapping \'{url}\'')
	SaveFile( animes_list, overwrite_file )

