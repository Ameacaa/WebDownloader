from dataclasses import dataclass, field
from pathlib import Path
import json

FILE = Path.cwd() / 'Anitube' / 'Animes.json'


@dataclass
class Episode:
	name: str = field(default_factory=str)# epNumber.mp4
	link: str = field(default_factory=str)# best link to dl

@dataclass
class Anime:
	title: str = field(default_factory=str)# Folder name
	season: str = field(default_factory=str)# Subfolder name
	episodes: list[Episode] = field(default_factory=list)


def CheckDuplicates( animes_dict: list[Anime] ):
	new_animes_dict = []
	animes_title = []

	for anime in animes_dict:
		if anime['title'] not in animes_title:
			animes_title.append(anime['title'])
			new_animes_dict.append(anime)

	return new_animes_dict


def SaveFile( animes_class: list[Anime], overwrite:bool = False ) -> None:
	# Convert Anime class to dict (episode need to convert too)
	animes_dict = [] # Anime dict (file data)
	for anime in animes_class:
		episode_dict = [] # Episode dict (file data)
		for episode in anime.episodes:
			episode_dict.append(episode.__dict__)
		anime.episodes = episode_dict # Tranform episodes to dict before convert anime to dict too
		animes_dict.append(anime.__dict__)

	# Append to existing data
	if FILE.is_file() and not overwrite:
		with open( FILE, 'r' ) as f:
			fileAnimes = json.load(f) # Get anime dict
		if fileAnimes is not None:
			animes_dict.extend(fileAnimes)
			#dictAnimes = list(set(dictAnimes)) # Remove doubles
	
	animes_dict = CheckDuplicates( animes_dict )

	# Save in file
	with open(FILE, 'w') as f:
		json.dump(animes_dict, f)


def LoadFile() -> list[Anime]:
	animes_class = []
	with open( FILE, 'r' ) as f:
		animes_in_file = json.load(f)
		if animes_in_file is not None:
			for anime_file in animes_in_file:
				anime = Anime(**anime_file) # Get the anime with episode in dict
				eps = [Episode(**episode) for episode in anime.episodes] # Convert ep dicts to ep class
				anime.episodes = eps # Set episode dict to episode class
				animes_class.append(anime)
	return animes_class

