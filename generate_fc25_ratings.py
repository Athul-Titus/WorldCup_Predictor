"""
generate_fc25_ratings.py — Generate FC25-style player ratings for WC 2026 squad players.
Creates data/male_players.csv with overall, pace, shooting, passing, dribbling, defending, physic.
Based on known real-world player ratings from EA FC 25.
"""
import pandas as pd
import numpy as np
import os

# Known FC25 ratings for notable players (as close to real as possible)
KNOWN_RATINGS = {
    # Argentina
    'Lionel Messi': {'overall': 88, 'pace': 75, 'shooting': 87, 'passing': 89, 'dribbling': 93, 'defending': 34, 'physic': 62},
    'Emiliano Martinez': {'overall': 87, 'pace': 50, 'shooting': 30, 'passing': 55, 'dribbling': 40, 'defending': 25, 'physic': 78},
    'Julian Alvarez': {'overall': 86, 'pace': 82, 'shooting': 84, 'passing': 78, 'dribbling': 85, 'defending': 53, 'physic': 74},
    'Lautaro Martinez': {'overall': 87, 'pace': 83, 'shooting': 87, 'passing': 72, 'dribbling': 84, 'defending': 42, 'physic': 78},
    'Rodrigo De Paul': {'overall': 84, 'pace': 72, 'shooting': 72, 'passing': 82, 'dribbling': 83, 'defending': 76, 'physic': 82},
    'Enzo Fernandez': {'overall': 85, 'pace': 71, 'shooting': 73, 'passing': 83, 'dribbling': 82, 'defending': 78, 'physic': 77},
    'Cristian Romero': {'overall': 86, 'pace': 80, 'shooting': 45, 'passing': 60, 'dribbling': 60, 'defending': 86, 'physic': 84},
    'Alexis Mac Allister': {'overall': 85, 'pace': 69, 'shooting': 75, 'passing': 84, 'dribbling': 83, 'defending': 73, 'physic': 76},
    'Nahuel Molina': {'overall': 82, 'pace': 84, 'shooting': 62, 'passing': 74, 'dribbling': 76, 'defending': 79, 'physic': 78},
    'Nicolas Otamendi': {'overall': 82, 'pace': 52, 'shooting': 50, 'passing': 60, 'dribbling': 58, 'defending': 83, 'physic': 83},
    'Alejandro Garnacho': {'overall': 80, 'pace': 91, 'shooting': 75, 'passing': 70, 'dribbling': 84, 'defending': 35, 'physic': 65},
    'Lisandro Martinez': {'overall': 84, 'pace': 70, 'shooting': 48, 'passing': 68, 'dribbling': 68, 'defending': 85, 'physic': 82},
    'Nicolas Tagliafico': {'overall': 80, 'pace': 78, 'shooting': 55, 'passing': 72, 'dribbling': 72, 'defending': 80, 'physic': 76},
    'Leandro Paredes': {'overall': 81, 'pace': 50, 'shooting': 70, 'passing': 83, 'dribbling': 78, 'defending': 74, 'physic': 74},
    'Giovani Lo Celso': {'overall': 80, 'pace': 68, 'shooting': 70, 'passing': 80, 'dribbling': 82, 'defending': 60, 'physic': 64},
    'Angel Di Maria': {'overall': 82, 'pace': 82, 'shooting': 80, 'passing': 84, 'dribbling': 86, 'defending': 32, 'physic': 55},
    'Paulo Dybala': {'overall': 83, 'pace': 76, 'shooting': 83, 'passing': 82, 'dribbling': 87, 'defending': 30, 'physic': 60},
    'Nicolas Gonzalez': {'overall': 80, 'pace': 85, 'shooting': 76, 'passing': 70, 'dribbling': 79, 'defending': 42, 'physic': 75},
    'Gonzalo Montiel': {'overall': 79, 'pace': 76, 'shooting': 55, 'passing': 70, 'dribbling': 70, 'defending': 78, 'physic': 76},
    'Marcos Acuna': {'overall': 80, 'pace': 78, 'shooting': 65, 'passing': 75, 'dribbling': 76, 'defending': 78, 'physic': 80},
    'German Pezzella': {'overall': 79, 'pace': 62, 'shooting': 45, 'passing': 58, 'dribbling': 55, 'defending': 82, 'physic': 80},
    'Exequiel Palacios': {'overall': 80, 'pace': 72, 'shooting': 70, 'passing': 78, 'dribbling': 80, 'defending': 68, 'physic': 72},
    'Franco Armani': {'overall': 80, 'pace': 45, 'shooting': 25, 'passing': 50, 'dribbling': 35, 'defending': 20, 'physic': 72},
    'Geronimo Rulli': {'overall': 82, 'pace': 48, 'shooting': 28, 'passing': 52, 'dribbling': 38, 'defending': 22, 'physic': 75},
    'Thiago Almada': {'overall': 79, 'pace': 78, 'shooting': 72, 'passing': 78, 'dribbling': 83, 'defending': 40, 'physic': 60},
    'Valentin Carboni': {'overall': 76, 'pace': 76, 'shooting': 68, 'passing': 74, 'dribbling': 80, 'defending': 38, 'physic': 55},
    # Brazil
    'Vinicius Junior': {'overall': 92, 'pace': 95, 'shooting': 85, 'passing': 80, 'dribbling': 94, 'defending': 30, 'physic': 68},
    'Rodrygo': {'overall': 86, 'pace': 88, 'shooting': 80, 'passing': 78, 'dribbling': 86, 'defending': 40, 'physic': 65},
    'Alisson': {'overall': 89, 'pace': 52, 'shooting': 25, 'passing': 60, 'dribbling': 42, 'defending': 28, 'physic': 82},
    'Marquinhos': {'overall': 86, 'pace': 72, 'shooting': 52, 'passing': 68, 'dribbling': 70, 'defending': 87, 'physic': 82},
    'Casemiro': {'overall': 82, 'pace': 60, 'shooting': 70, 'passing': 72, 'dribbling': 72, 'defending': 82, 'physic': 84},
    'Raphinha': {'overall': 85, 'pace': 86, 'shooting': 80, 'passing': 78, 'dribbling': 85, 'defending': 45, 'physic': 68},
    'Ederson': {'overall': 88, 'pace': 55, 'shooting': 28, 'passing': 75, 'dribbling': 45, 'defending': 25, 'physic': 80},
    'Bruno Guimaraes': {'overall': 85, 'pace': 65, 'shooting': 72, 'passing': 82, 'dribbling': 83, 'defending': 80, 'physic': 80},
    'Militao': {'overall': 84, 'pace': 80, 'shooting': 48, 'passing': 60, 'dribbling': 62, 'defending': 84, 'physic': 82},
    'Lucas Paqueta': {'overall': 84, 'pace': 72, 'shooting': 75, 'passing': 80, 'dribbling': 84, 'defending': 65, 'physic': 76},
    'Endrick': {'overall': 78, 'pace': 85, 'shooting': 78, 'passing': 62, 'dribbling': 80, 'defending': 32, 'physic': 72},
    'Savinho': {'overall': 80, 'pace': 88, 'shooting': 70, 'passing': 74, 'dribbling': 85, 'defending': 30, 'physic': 58},
    'Gabriel Magalhaes': {'overall': 84, 'pace': 68, 'shooting': 52, 'passing': 55, 'dribbling': 55, 'defending': 85, 'physic': 85},
    'Gabriel Martinelli': {'overall': 82, 'pace': 90, 'shooting': 78, 'passing': 72, 'dribbling': 82, 'defending': 38, 'physic': 70},
    'Danilo': {'overall': 78, 'pace': 72, 'shooting': 55, 'passing': 72, 'dribbling': 70, 'defending': 78, 'physic': 76},
    # France
    'Kylian Mbappe': {'overall': 91, 'pace': 97, 'shooting': 89, 'passing': 80, 'dribbling': 92, 'defending': 36, 'physic': 76},
    'Antoine Griezmann': {'overall': 85, 'pace': 72, 'shooting': 84, 'passing': 83, 'dribbling': 84, 'defending': 56, 'physic': 72},
    'William Saliba': {'overall': 86, 'pace': 78, 'shooting': 40, 'passing': 62, 'dribbling': 60, 'defending': 87, 'physic': 84},
    'Aurelien Tchouameni': {'overall': 85, 'pace': 72, 'shooting': 68, 'passing': 78, 'dribbling': 76, 'defending': 84, 'physic': 82},
    'Mike Maignan': {'overall': 87, 'pace': 55, 'shooting': 28, 'passing': 58, 'dribbling': 40, 'defending': 25, 'physic': 80},
    'Ousmane Dembele': {'overall': 85, 'pace': 92, 'shooting': 76, 'passing': 80, 'dribbling': 90, 'defending': 38, 'physic': 58},
    'Marcus Thuram': {'overall': 85, 'pace': 86, 'shooting': 82, 'passing': 72, 'dribbling': 82, 'defending': 40, 'physic': 82},
    'Theo Hernandez': {'overall': 85, 'pace': 88, 'shooting': 70, 'passing': 76, 'dribbling': 78, 'defending': 80, 'physic': 82},
    'Jules Kounde': {'overall': 85, 'pace': 82, 'shooting': 48, 'passing': 70, 'dribbling': 72, 'defending': 85, 'physic': 78},
    'Dayot Upamecano': {'overall': 82, 'pace': 80, 'shooting': 42, 'passing': 55, 'dribbling': 58, 'defending': 83, 'physic': 85},
    'Eduardo Camavinga': {'overall': 83, 'pace': 78, 'shooting': 62, 'passing': 78, 'dribbling': 82, 'defending': 76, 'physic': 80},
    "N'Golo Kante": {'overall': 82, 'pace': 72, 'shooting': 52, 'passing': 74, 'dribbling': 78, 'defending': 82, 'physic': 76},
    'Ibrahima Konate': {'overall': 83, 'pace': 82, 'shooting': 42, 'passing': 55, 'dribbling': 55, 'defending': 83, 'physic': 84},
    # England
    'Jude Bellingham': {'overall': 89, 'pace': 78, 'shooting': 82, 'passing': 82, 'dribbling': 87, 'defending': 68, 'physic': 80},
    'Harry Kane': {'overall': 89, 'pace': 68, 'shooting': 92, 'passing': 82, 'dribbling': 82, 'defending': 48, 'physic': 82},
    'Phil Foden': {'overall': 88, 'pace': 82, 'shooting': 82, 'passing': 85, 'dribbling': 90, 'defending': 50, 'physic': 62},
    'Bukayo Saka': {'overall': 87, 'pace': 86, 'shooting': 80, 'passing': 82, 'dribbling': 87, 'defending': 62, 'physic': 68},
    'Declan Rice': {'overall': 86, 'pace': 72, 'shooting': 68, 'passing': 78, 'dribbling': 76, 'defending': 85, 'physic': 84},
    'Cole Palmer': {'overall': 85, 'pace': 78, 'shooting': 84, 'passing': 82, 'dribbling': 86, 'defending': 42, 'physic': 60},
    'Trent Alexander-Arnold': {'overall': 84, 'pace': 76, 'shooting': 62, 'passing': 88, 'dribbling': 78, 'defending': 76, 'physic': 72},
    'Jordan Pickford': {'overall': 83, 'pace': 52, 'shooting': 25, 'passing': 58, 'dribbling': 38, 'defending': 22, 'physic': 78},
    'John Stones': {'overall': 84, 'pace': 62, 'shooting': 45, 'passing': 72, 'dribbling': 68, 'defending': 84, 'physic': 80},
    'Kyle Walker': {'overall': 82, 'pace': 88, 'shooting': 55, 'passing': 68, 'dribbling': 72, 'defending': 80, 'physic': 82},
    'Kobbie Mainoo': {'overall': 79, 'pace': 72, 'shooting': 68, 'passing': 76, 'dribbling': 80, 'defending': 72, 'physic': 72},
    'Marc Guehi': {'overall': 82, 'pace': 72, 'shooting': 40, 'passing': 62, 'dribbling': 60, 'defending': 83, 'physic': 80},
    # Spain
    'Rodri': {'overall': 91, 'pace': 62, 'shooting': 76, 'passing': 88, 'dribbling': 84, 'defending': 86, 'physic': 84},
    'Lamine Yamal': {'overall': 83, 'pace': 90, 'shooting': 72, 'passing': 80, 'dribbling': 88, 'defending': 28, 'physic': 48},
    'Dani Carvajal': {'overall': 86, 'pace': 76, 'shooting': 62, 'passing': 78, 'dribbling': 78, 'defending': 85, 'physic': 80},
    'Pedri': {'overall': 86, 'pace': 72, 'shooting': 72, 'passing': 86, 'dribbling': 88, 'defending': 65, 'physic': 65},
    'Nico Williams': {'overall': 83, 'pace': 93, 'shooting': 74, 'passing': 76, 'dribbling': 86, 'defending': 35, 'physic': 68},
    'Dani Olmo': {'overall': 84, 'pace': 76, 'shooting': 80, 'passing': 82, 'dribbling': 85, 'defending': 50, 'physic': 68},
    'Unai Simon': {'overall': 84, 'pace': 52, 'shooting': 28, 'passing': 60, 'dribbling': 42, 'defending': 25, 'physic': 78},
    'Gavi': {'overall': 82, 'pace': 75, 'shooting': 70, 'passing': 80, 'dribbling': 84, 'defending': 72, 'physic': 72},
    'Alvaro Morata': {'overall': 82, 'pace': 76, 'shooting': 82, 'passing': 70, 'dribbling': 76, 'defending': 40, 'physic': 76},
    # Portugal
    'Cristiano Ronaldo': {'overall': 84, 'pace': 72, 'shooting': 90, 'passing': 75, 'dribbling': 82, 'defending': 34, 'physic': 78},
    'Bruno Fernandes': {'overall': 86, 'pace': 72, 'shooting': 82, 'passing': 88, 'dribbling': 84, 'defending': 62, 'physic': 72},
    'Bernardo Silva': {'overall': 87, 'pace': 72, 'shooting': 75, 'passing': 86, 'dribbling': 90, 'defending': 62, 'physic': 65},
    'Rafael Leao': {'overall': 86, 'pace': 94, 'shooting': 80, 'passing': 75, 'dribbling': 88, 'defending': 30, 'physic': 72},
    'Diogo Jota': {'overall': 84, 'pace': 84, 'shooting': 83, 'passing': 72, 'dribbling': 83, 'defending': 45, 'physic': 75},
    'Ruben Dias': {'overall': 86, 'pace': 68, 'shooting': 48, 'passing': 65, 'dribbling': 62, 'defending': 88, 'physic': 84},
    'Diogo Costa': {'overall': 83, 'pace': 52, 'shooting': 25, 'passing': 58, 'dribbling': 40, 'defending': 22, 'physic': 78},
    'Vitinha': {'overall': 84, 'pace': 72, 'shooting': 72, 'passing': 84, 'dribbling': 85, 'defending': 68, 'physic': 65},
    # Germany
    'Jamal Musiala': {'overall': 87, 'pace': 80, 'shooting': 78, 'passing': 82, 'dribbling': 90, 'defending': 40, 'physic': 60},
    'Florian Wirtz': {'overall': 87, 'pace': 78, 'shooting': 80, 'passing': 84, 'dribbling': 88, 'defending': 48, 'physic': 58},
    'Manuel Neuer': {'overall': 85, 'pace': 52, 'shooting': 30, 'passing': 62, 'dribbling': 42, 'defending': 25, 'physic': 82},
    'Toni Kroos': {'overall': 86, 'pace': 48, 'shooting': 78, 'passing': 90, 'dribbling': 82, 'defending': 72, 'physic': 72},
    'Kai Havertz': {'overall': 83, 'pace': 75, 'shooting': 78, 'passing': 76, 'dribbling': 80, 'defending': 52, 'physic': 72},
    'Joshua Kimmich': {'overall': 86, 'pace': 70, 'shooting': 68, 'passing': 85, 'dribbling': 80, 'defending': 83, 'physic': 78},
    'Antonio Rudiger': {'overall': 84, 'pace': 80, 'shooting': 48, 'passing': 58, 'dribbling': 58, 'defending': 85, 'physic': 86},
    'Leroy Sane': {'overall': 83, 'pace': 90, 'shooting': 78, 'passing': 78, 'dribbling': 86, 'defending': 35, 'physic': 62},
    'Niclas Fullkrug': {'overall': 82, 'pace': 72, 'shooting': 84, 'passing': 62, 'dribbling': 72, 'defending': 35, 'physic': 82},
    # Netherlands
    'Virgil van Dijk': {'overall': 88, 'pace': 72, 'shooting': 60, 'passing': 72, 'dribbling': 68, 'defending': 90, 'physic': 86},
    'Frenkie de Jong': {'overall': 85, 'pace': 72, 'shooting': 62, 'passing': 85, 'dribbling': 86, 'defending': 72, 'physic': 68},
    'Memphis Depay': {'overall': 82, 'pace': 80, 'shooting': 82, 'passing': 78, 'dribbling': 84, 'defending': 30, 'physic': 72},
    'Cody Gakpo': {'overall': 83, 'pace': 82, 'shooting': 78, 'passing': 76, 'dribbling': 82, 'defending': 38, 'physic': 72},
    'Xavi Simons': {'overall': 83, 'pace': 82, 'shooting': 76, 'passing': 78, 'dribbling': 85, 'defending': 40, 'physic': 62},
    'Nathan Ake': {'overall': 83, 'pace': 72, 'shooting': 42, 'passing': 65, 'dribbling': 65, 'defending': 84, 'physic': 82},
    # Belgium
    'Kevin De Bruyne': {'overall': 90, 'pace': 72, 'shooting': 86, 'passing': 93, 'dribbling': 88, 'defending': 58, 'physic': 72},
    'Thibaut Courtois': {'overall': 89, 'pace': 50, 'shooting': 25, 'passing': 55, 'dribbling': 38, 'defending': 25, 'physic': 85},
    'Romelu Lukaku': {'overall': 83, 'pace': 82, 'shooting': 85, 'passing': 68, 'dribbling': 78, 'defending': 35, 'physic': 88},
    'Jeremy Doku': {'overall': 82, 'pace': 93, 'shooting': 68, 'passing': 72, 'dribbling': 88, 'defending': 32, 'physic': 58},
    # Croatia
    'Luka Modric': {'overall': 85, 'pace': 62, 'shooting': 72, 'passing': 88, 'dribbling': 86, 'defending': 68, 'physic': 62},
    'Mateo Kovacic': {'overall': 84, 'pace': 72, 'shooting': 68, 'passing': 82, 'dribbling': 85, 'defending': 72, 'physic': 72},
    'Josko Gvardiol': {'overall': 84, 'pace': 78, 'shooting': 50, 'passing': 65, 'dribbling': 65, 'defending': 84, 'physic': 82},
    'Dominik Livakovic': {'overall': 82, 'pace': 50, 'shooting': 25, 'passing': 52, 'dribbling': 38, 'defending': 22, 'physic': 76},
    # Italy
    'Gianluigi Donnarumma': {'overall': 87, 'pace': 55, 'shooting': 28, 'passing': 58, 'dribbling': 42, 'defending': 25, 'physic': 82},
    'Nicolo Barella': {'overall': 86, 'pace': 76, 'shooting': 78, 'passing': 82, 'dribbling': 84, 'defending': 76, 'physic': 80},
    'Federico Chiesa': {'overall': 82, 'pace': 88, 'shooting': 78, 'passing': 72, 'dribbling': 84, 'defending': 38, 'physic': 66},
    'Alessandro Bastoni': {'overall': 85, 'pace': 68, 'shooting': 48, 'passing': 72, 'dribbling': 68, 'defending': 86, 'physic': 82},
    # Other notable players
    'Mohamed Salah': {'overall': 89, 'pace': 90, 'shooting': 87, 'passing': 82, 'dribbling': 88, 'defending': 45, 'physic': 72},
    'Son Heung-min': {'overall': 87, 'pace': 86, 'shooting': 86, 'passing': 82, 'dribbling': 86, 'defending': 42, 'physic': 68},
    'Victor Osimhen': {'overall': 87, 'pace': 88, 'shooting': 85, 'passing': 62, 'dribbling': 80, 'defending': 32, 'physic': 82},
    'Sadio Mane': {'overall': 82, 'pace': 86, 'shooting': 80, 'passing': 72, 'dribbling': 84, 'defending': 42, 'physic': 76},
    'Christian Pulisic': {'overall': 82, 'pace': 82, 'shooting': 76, 'passing': 78, 'dribbling': 84, 'defending': 38, 'physic': 62},
    'Alphonso Davies': {'overall': 83, 'pace': 94, 'shooting': 60, 'passing': 72, 'dribbling': 82, 'defending': 76, 'physic': 76},
    'Achraf Hakimi': {'overall': 85, 'pace': 90, 'shooting': 68, 'passing': 78, 'dribbling': 80, 'defending': 78, 'physic': 76},
    'Granit Xhaka': {'overall': 84, 'pace': 52, 'shooting': 75, 'passing': 82, 'dribbling': 76, 'defending': 78, 'physic': 82},
    'Manuel Akanji': {'overall': 84, 'pace': 72, 'shooting': 42, 'passing': 65, 'dribbling': 65, 'defending': 85, 'physic': 82},
    'Keylor Navas': {'overall': 80, 'pace': 52, 'shooting': 25, 'passing': 50, 'dribbling': 38, 'defending': 22, 'physic': 75},
    'Kim Min-jae': {'overall': 85, 'pace': 76, 'shooting': 42, 'passing': 58, 'dribbling': 55, 'defending': 86, 'physic': 84},
    'Andre Onana': {'overall': 84, 'pace': 52, 'shooting': 25, 'passing': 62, 'dribbling': 45, 'defending': 22, 'physic': 78},
    'Thomas Partey': {'overall': 83, 'pace': 68, 'shooting': 72, 'passing': 78, 'dribbling': 78, 'defending': 82, 'physic': 82},
    'Mohammed Kudus': {'overall': 82, 'pace': 82, 'shooting': 78, 'passing': 72, 'dribbling': 84, 'defending': 52, 'physic': 72},
    'Mehdi Taremi': {'overall': 82, 'pace': 72, 'shooting': 82, 'passing': 72, 'dribbling': 78, 'defending': 42, 'physic': 78},
    'Jonathan David': {'overall': 83, 'pace': 84, 'shooting': 82, 'passing': 68, 'dribbling': 80, 'defending': 32, 'physic': 72},
    'Edouard Mendy': {'overall': 81, 'pace': 50, 'shooting': 25, 'passing': 52, 'dribbling': 38, 'defending': 22, 'physic': 78},
    'Yassine Bounou': {'overall': 83, 'pace': 52, 'shooting': 28, 'passing': 55, 'dribbling': 40, 'defending': 22, 'physic': 78},
    'Hakim Ziyech': {'overall': 82, 'pace': 72, 'shooting': 78, 'passing': 85, 'dribbling': 86, 'defending': 35, 'physic': 58},
    'Sofyan Amrabat': {'overall': 80, 'pace': 68, 'shooting': 58, 'passing': 72, 'dribbling': 72, 'defending': 80, 'physic': 82},
    'Inaki Williams': {'overall': 80, 'pace': 90, 'shooting': 75, 'passing': 62, 'dribbling': 78, 'defending': 38, 'physic': 80},
    'Luis Diaz': {'overall': 84, 'pace': 88, 'shooting': 78, 'passing': 76, 'dribbling': 85, 'defending': 42, 'physic': 68},
    'James Rodriguez': {'overall': 78, 'pace': 60, 'shooting': 78, 'passing': 85, 'dribbling': 82, 'defending': 38, 'physic': 55},
    'Darwin Nunez': {'overall': 84, 'pace': 90, 'shooting': 82, 'passing': 62, 'dribbling': 78, 'defending': 35, 'physic': 78},
    'Federico Valverde': {'overall': 87, 'pace': 82, 'shooting': 80, 'passing': 80, 'dribbling': 82, 'defending': 78, 'physic': 82},
    'Ronald Araujo': {'overall': 85, 'pace': 82, 'shooting': 48, 'passing': 55, 'dribbling': 55, 'defending': 86, 'physic': 86},
    'Moises Caicedo': {'overall': 82, 'pace': 70, 'shooting': 68, 'passing': 76, 'dribbling': 76, 'defending': 82, 'physic': 82},
    'Enner Valencia': {'overall': 78, 'pace': 80, 'shooting': 78, 'passing': 62, 'dribbling': 76, 'defending': 32, 'physic': 75},
    'Christian Eriksen': {'overall': 82, 'pace': 60, 'shooting': 80, 'passing': 85, 'dribbling': 82, 'defending': 50, 'physic': 58},
    'Kasper Schmeichel': {'overall': 80, 'pace': 48, 'shooting': 25, 'passing': 52, 'dribbling': 35, 'defending': 20, 'physic': 76},
    'Rasmus Hojlund': {'overall': 80, 'pace': 84, 'shooting': 78, 'passing': 62, 'dribbling': 76, 'defending': 35, 'physic': 78},
    'Sergej Milinkovic-Savic': {'overall': 84, 'pace': 68, 'shooting': 78, 'passing': 82, 'dribbling': 82, 'defending': 72, 'physic': 82},
    'Aleksandar Mitrovic': {'overall': 82, 'pace': 65, 'shooting': 84, 'passing': 62, 'dribbling': 72, 'defending': 38, 'physic': 84},
    'Dusan Vlahovic': {'overall': 84, 'pace': 78, 'shooting': 85, 'passing': 62, 'dribbling': 76, 'defending': 35, 'physic': 80},
    'Oleksandr Zinchenko': {'overall': 81, 'pace': 68, 'shooting': 62, 'passing': 80, 'dribbling': 78, 'defending': 72, 'physic': 65},
    'Artem Dovbyk': {'overall': 83, 'pace': 72, 'shooting': 84, 'passing': 60, 'dribbling': 76, 'defending': 32, 'physic': 82},
    'Mykhailo Mudryk': {'overall': 79, 'pace': 92, 'shooting': 72, 'passing': 72, 'dribbling': 82, 'defending': 35, 'physic': 60},
    'Andrew Robertson': {'overall': 83, 'pace': 80, 'shooting': 55, 'passing': 80, 'dribbling': 75, 'defending': 80, 'physic': 76},
    'Scott McTominay': {'overall': 81, 'pace': 72, 'shooting': 75, 'passing': 72, 'dribbling': 74, 'defending': 74, 'physic': 82},
    'Chris Wood': {'overall': 78, 'pace': 62, 'shooting': 78, 'passing': 55, 'dribbling': 62, 'defending': 35, 'physic': 80},
    'Alexis Sanchez': {'overall': 79, 'pace': 78, 'shooting': 78, 'passing': 75, 'dribbling': 82, 'defending': 45, 'physic': 68},
    'Arturo Vidal': {'overall': 76, 'pace': 65, 'shooting': 75, 'passing': 72, 'dribbling': 76, 'defending': 72, 'physic': 80},
    'Miguel Almiron': {'overall': 79, 'pace': 88, 'shooting': 72, 'passing': 72, 'dribbling': 82, 'defending': 38, 'physic': 62},
    'Akram Afif': {'overall': 78, 'pace': 82, 'shooting': 75, 'passing': 78, 'dribbling': 82, 'defending': 30, 'physic': 58},
    'Almoez Ali': {'overall': 76, 'pace': 80, 'shooting': 75, 'passing': 60, 'dribbling': 76, 'defending': 30, 'physic': 68},
    'Salem Al-Dawsari': {'overall': 78, 'pace': 82, 'shooting': 75, 'passing': 76, 'dribbling': 82, 'defending': 32, 'physic': 62},
    'Ademola Lookman': {'overall': 83, 'pace': 86, 'shooting': 78, 'passing': 74, 'dribbling': 84, 'defending': 38, 'physic': 65},
    'Omar Marmoush': {'overall': 82, 'pace': 88, 'shooting': 78, 'passing': 72, 'dribbling': 82, 'defending': 35, 'physic': 68},
    'Illia Zabarnyi': {'overall': 80, 'pace': 72, 'shooting': 42, 'passing': 58, 'dribbling': 55, 'defending': 82, 'physic': 80},
    'Piero Hincapie': {'overall': 80, 'pace': 76, 'shooting': 42, 'passing': 62, 'dribbling': 62, 'defending': 82, 'physic': 78},
    'Franck Kessie': {'overall': 79, 'pace': 70, 'shooting': 72, 'passing': 68, 'dribbling': 72, 'defending': 78, 'physic': 82},
    'Wilfried Zaha': {'overall': 78, 'pace': 86, 'shooting': 75, 'passing': 68, 'dribbling': 84, 'defending': 35, 'physic': 72},
    'Victor Boniface': {'overall': 81, 'pace': 82, 'shooting': 80, 'passing': 62, 'dribbling': 80, 'defending': 30, 'physic': 80},
    'Kalidou Koulibaly': {'overall': 80, 'pace': 68, 'shooting': 42, 'passing': 55, 'dribbling': 55, 'defending': 83, 'physic': 84},
    'Guillermo Ochoa': {'overall': 78, 'pace': 48, 'shooting': 25, 'passing': 50, 'dribbling': 35, 'defending': 20, 'physic': 72},
    'Hirving Lozano': {'overall': 80, 'pace': 88, 'shooting': 75, 'passing': 72, 'dribbling': 82, 'defending': 38, 'physic': 62},
    'Santiago Gimenez': {'overall': 81, 'pace': 78, 'shooting': 82, 'passing': 58, 'dribbling': 76, 'defending': 32, 'physic': 78},
    'Edson Alvarez': {'overall': 82, 'pace': 65, 'shooting': 65, 'passing': 72, 'dribbling': 72, 'defending': 82, 'physic': 84},
}


def generate_fc25_ratings():
    """Generate FC25-style ratings for all WC 2026 squad players."""
    print("Generating FC25 ratings...")
    
    squads = pd.read_csv('data/wc2026_squads.csv')
    
    rng = np.random.RandomState(42)
    
    rows = []
    for _, player in squads.iterrows():
        name = player['player_name']
        pos = player['position']
        
        if name in KNOWN_RATINGS:
            r = KNOWN_RATINGS[name]
        else:
            # Generate realistic ratings based on position
            if pos == 'GK':
                ovr = rng.randint(68, 80)
                r = {
                    'overall': ovr, 'pace': rng.randint(40, 55),
                    'shooting': rng.randint(20, 35), 'passing': rng.randint(40, 60),
                    'dribbling': rng.randint(30, 45), 'defending': rng.randint(18, 28),
                    'physic': rng.randint(65, 80)
                }
            elif pos == 'DEF':
                ovr = rng.randint(70, 82)
                r = {
                    'overall': ovr, 'pace': rng.randint(55, 82),
                    'shooting': rng.randint(35, 58), 'passing': rng.randint(50, 72),
                    'dribbling': rng.randint(50, 70), 'defending': rng.randint(72, 85),
                    'physic': rng.randint(70, 85)
                }
            elif pos == 'MID':
                ovr = rng.randint(70, 82)
                r = {
                    'overall': ovr, 'pace': rng.randint(58, 82),
                    'shooting': rng.randint(55, 78), 'passing': rng.randint(65, 82),
                    'dribbling': rng.randint(68, 84), 'defending': rng.randint(50, 78),
                    'physic': rng.randint(60, 80)
                }
            else:  # FWD
                ovr = rng.randint(70, 82)
                r = {
                    'overall': ovr, 'pace': rng.randint(72, 90),
                    'shooting': rng.randint(68, 84), 'passing': rng.randint(55, 75),
                    'dribbling': rng.randint(72, 86), 'defending': rng.randint(25, 42),
                    'physic': rng.randint(58, 78)
                }
        
        rows.append({
            'long_name': name,
            'short_name': name.split()[-1] if len(name.split()) > 1 else name,
            'overall': r['overall'],
            'pace': r['pace'],
            'shooting': r['shooting'],
            'passing': r['passing'],
            'dribbling': r['dribbling'],
            'defending': r['defending'],
            'physic': r['physic'],
            'nationality_name': player['team'],
            'club_position': pos,
        })
    
    df = pd.DataFrame(rows)
    df.to_csv('data/male_players.csv', index=False)
    print(f"Saved data/male_players.csv with {len(df)} player ratings")
    return df


if __name__ == '__main__':
    generate_fc25_ratings()
