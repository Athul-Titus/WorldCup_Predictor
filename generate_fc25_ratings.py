"""
generate_fc25_ratings.py — Generate FC25-style player ratings for WC 2026 squad players.
Creates data/male_players.csv with overall, pace, shooting, passing, dribbling, defending, physic.
Uses known real EA FC 25 ratings for stars, and generates realistic fallback ratings by
position and team tier for unknown players.
"""
import pandas as pd
import numpy as np
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# ══════════════════════════════════════════════════════════════════════════════
# Known FC25 ratings for notable players — as close to real EA FC 25 as possible
# ══════════════════════════════════════════════════════════════════════════════
KNOWN_RATINGS = {
    # ── Argentina ──
    'Lionel Messi': {'overall': 88, 'pace': 75, 'shooting': 87, 'passing': 89, 'dribbling': 93, 'defending': 34, 'physic': 62},
    'Emiliano Martínez': {'overall': 87, 'pace': 50, 'shooting': 30, 'passing': 55, 'dribbling': 40, 'defending': 25, 'physic': 78},
    'Julián Álvarez': {'overall': 86, 'pace': 82, 'shooting': 84, 'passing': 78, 'dribbling': 85, 'defending': 53, 'physic': 74},
    'Lautaro Martínez': {'overall': 87, 'pace': 83, 'shooting': 87, 'passing': 72, 'dribbling': 84, 'defending': 42, 'physic': 78},
    'Rodrigo De Paul': {'overall': 84, 'pace': 72, 'shooting': 72, 'passing': 82, 'dribbling': 83, 'defending': 76, 'physic': 82},
    'Enzo Fernández': {'overall': 85, 'pace': 71, 'shooting': 73, 'passing': 83, 'dribbling': 82, 'defending': 78, 'physic': 77},
    'Cristian Romero': {'overall': 86, 'pace': 80, 'shooting': 45, 'passing': 60, 'dribbling': 60, 'defending': 86, 'physic': 84},
    'Alexis Mac Allister': {'overall': 85, 'pace': 69, 'shooting': 75, 'passing': 84, 'dribbling': 83, 'defending': 73, 'physic': 76},
    'Alejandro Garnacho': {'overall': 80, 'pace': 91, 'shooting': 75, 'passing': 70, 'dribbling': 84, 'defending': 35, 'physic': 65},
    'Lisandro Martínez': {'overall': 84, 'pace': 70, 'shooting': 48, 'passing': 68, 'dribbling': 68, 'defending': 85, 'physic': 82},
    'Paulo Dybala': {'overall': 83, 'pace': 76, 'shooting': 83, 'passing': 82, 'dribbling': 87, 'defending': 30, 'physic': 60},
    'Nicolás González': {'overall': 80, 'pace': 85, 'shooting': 76, 'passing': 70, 'dribbling': 79, 'defending': 42, 'physic': 75},
    # ── Brazil ──
    'Vinícius Júnior': {'overall': 92, 'pace': 95, 'shooting': 85, 'passing': 80, 'dribbling': 94, 'defending': 30, 'physic': 68},
    'Rodrygo': {'overall': 86, 'pace': 88, 'shooting': 80, 'passing': 78, 'dribbling': 86, 'defending': 40, 'physic': 65},
    'Alisson': {'overall': 89, 'pace': 52, 'shooting': 25, 'passing': 60, 'dribbling': 42, 'defending': 28, 'physic': 82},
    'Marquinhos': {'overall': 86, 'pace': 72, 'shooting': 52, 'passing': 68, 'dribbling': 70, 'defending': 87, 'physic': 82},
    'Raphinha': {'overall': 85, 'pace': 86, 'shooting': 80, 'passing': 78, 'dribbling': 85, 'defending': 45, 'physic': 68},
    'Ederson': {'overall': 88, 'pace': 55, 'shooting': 28, 'passing': 75, 'dribbling': 45, 'defending': 25, 'physic': 80},
    'Bruno Guimarães': {'overall': 85, 'pace': 65, 'shooting': 72, 'passing': 82, 'dribbling': 83, 'defending': 80, 'physic': 80},
    'Endrick': {'overall': 78, 'pace': 85, 'shooting': 78, 'passing': 62, 'dribbling': 80, 'defending': 32, 'physic': 72},
    'Savinho': {'overall': 80, 'pace': 88, 'shooting': 70, 'passing': 74, 'dribbling': 85, 'defending': 30, 'physic': 58},
    'Gabriel Martinelli': {'overall': 82, 'pace': 90, 'shooting': 78, 'passing': 72, 'dribbling': 82, 'defending': 38, 'physic': 70},
    # ── France ──
    'Kylian Mbappé': {'overall': 91, 'pace': 97, 'shooting': 89, 'passing': 80, 'dribbling': 92, 'defending': 36, 'physic': 76},
    'Antoine Griezmann': {'overall': 85, 'pace': 72, 'shooting': 84, 'passing': 83, 'dribbling': 84, 'defending': 56, 'physic': 72},
    'William Saliba': {'overall': 86, 'pace': 78, 'shooting': 40, 'passing': 62, 'dribbling': 60, 'defending': 87, 'physic': 84},
    'Aurélien Tchouaméni': {'overall': 85, 'pace': 72, 'shooting': 68, 'passing': 78, 'dribbling': 76, 'defending': 84, 'physic': 82},
    'Mike Maignan': {'overall': 87, 'pace': 55, 'shooting': 28, 'passing': 58, 'dribbling': 40, 'defending': 25, 'physic': 80},
    'Ousmane Dembélé': {'overall': 85, 'pace': 92, 'shooting': 76, 'passing': 80, 'dribbling': 90, 'defending': 38, 'physic': 58},
    'Marcus Thuram': {'overall': 85, 'pace': 86, 'shooting': 82, 'passing': 72, 'dribbling': 82, 'defending': 40, 'physic': 82},
    'Theo Hernández': {'overall': 85, 'pace': 88, 'shooting': 70, 'passing': 76, 'dribbling': 78, 'defending': 80, 'physic': 82},
    'Jules Koundé': {'overall': 85, 'pace': 82, 'shooting': 48, 'passing': 70, 'dribbling': 72, 'defending': 85, 'physic': 78},
    'Eduardo Camavinga': {'overall': 83, 'pace': 78, 'shooting': 62, 'passing': 78, 'dribbling': 82, 'defending': 76, 'physic': 80},
    'Bradley Barcola': {'overall': 82, 'pace': 92, 'shooting': 74, 'passing': 74, 'dribbling': 86, 'defending': 32, 'physic': 60},
    'Michael Olise': {'overall': 84, 'pace': 84, 'shooting': 80, 'passing': 82, 'dribbling': 88, 'defending': 30, 'physic': 62},
    # ── Germany ──
    'Jamal Musiala': {'overall': 87, 'pace': 80, 'shooting': 78, 'passing': 82, 'dribbling': 90, 'defending': 40, 'physic': 60},
    'Florian Wirtz': {'overall': 87, 'pace': 78, 'shooting': 80, 'passing': 84, 'dribbling': 88, 'defending': 48, 'physic': 58},
    'Manuel Neuer': {'overall': 85, 'pace': 52, 'shooting': 30, 'passing': 62, 'dribbling': 42, 'defending': 25, 'physic': 82},
    'Kai Havertz': {'overall': 83, 'pace': 75, 'shooting': 78, 'passing': 76, 'dribbling': 80, 'defending': 52, 'physic': 72},
    'Joshua Kimmich': {'overall': 86, 'pace': 70, 'shooting': 68, 'passing': 85, 'dribbling': 80, 'defending': 83, 'physic': 78},
    'Antonio Rüdiger': {'overall': 84, 'pace': 80, 'shooting': 48, 'passing': 58, 'dribbling': 58, 'defending': 85, 'physic': 86},
    'Leroy Sané': {'overall': 83, 'pace': 90, 'shooting': 78, 'passing': 78, 'dribbling': 86, 'defending': 35, 'physic': 62},
    # ── England ──
    'Jude Bellingham': {'overall': 89, 'pace': 78, 'shooting': 82, 'passing': 82, 'dribbling': 87, 'defending': 68, 'physic': 80},
    'Harry Kane': {'overall': 89, 'pace': 68, 'shooting': 92, 'passing': 82, 'dribbling': 82, 'defending': 48, 'physic': 82},
    'Phil Foden': {'overall': 88, 'pace': 82, 'shooting': 82, 'passing': 85, 'dribbling': 90, 'defending': 50, 'physic': 62},
    'Bukayo Saka': {'overall': 87, 'pace': 86, 'shooting': 80, 'passing': 82, 'dribbling': 87, 'defending': 62, 'physic': 68},
    'Declan Rice': {'overall': 86, 'pace': 72, 'shooting': 68, 'passing': 78, 'dribbling': 76, 'defending': 85, 'physic': 84},
    'Cole Palmer': {'overall': 85, 'pace': 78, 'shooting': 84, 'passing': 82, 'dribbling': 86, 'defending': 42, 'physic': 60},
    'Trent Alexander-Arnold': {'overall': 84, 'pace': 76, 'shooting': 62, 'passing': 88, 'dribbling': 78, 'defending': 76, 'physic': 72},
    # ── Spain ──
    'Rodri': {'overall': 91, 'pace': 62, 'shooting': 76, 'passing': 88, 'dribbling': 84, 'defending': 86, 'physic': 84},
    'Lamine Yamal': {'overall': 83, 'pace': 90, 'shooting': 72, 'passing': 80, 'dribbling': 88, 'defending': 28, 'physic': 48},
    'Dani Carvajal': {'overall': 86, 'pace': 76, 'shooting': 62, 'passing': 78, 'dribbling': 78, 'defending': 85, 'physic': 80},
    'Pedri': {'overall': 86, 'pace': 72, 'shooting': 72, 'passing': 86, 'dribbling': 88, 'defending': 65, 'physic': 65},
    'Nico Williams': {'overall': 83, 'pace': 93, 'shooting': 74, 'passing': 76, 'dribbling': 86, 'defending': 35, 'physic': 68},
    'Dani Olmo': {'overall': 84, 'pace': 76, 'shooting': 80, 'passing': 82, 'dribbling': 85, 'defending': 50, 'physic': 68},
    # ── Portugal ──
    'Cristiano Ronaldo': {'overall': 84, 'pace': 72, 'shooting': 90, 'passing': 75, 'dribbling': 82, 'defending': 34, 'physic': 78},
    'Bruno Fernandes': {'overall': 86, 'pace': 72, 'shooting': 82, 'passing': 88, 'dribbling': 84, 'defending': 62, 'physic': 72},
    'Bernardo Silva': {'overall': 87, 'pace': 72, 'shooting': 75, 'passing': 86, 'dribbling': 90, 'defending': 62, 'physic': 65},
    'Rafael Leão': {'overall': 86, 'pace': 94, 'shooting': 80, 'passing': 75, 'dribbling': 88, 'defending': 30, 'physic': 72},
    'Rúben Dias': {'overall': 86, 'pace': 68, 'shooting': 48, 'passing': 65, 'dribbling': 62, 'defending': 88, 'physic': 84},
    'Diogo Jota': {'overall': 84, 'pace': 84, 'shooting': 83, 'passing': 72, 'dribbling': 83, 'defending': 45, 'physic': 75},
    # ── Netherlands ──
    'Virgil van Dijk': {'overall': 88, 'pace': 72, 'shooting': 60, 'passing': 72, 'dribbling': 68, 'defending': 90, 'physic': 86},
    'Frenkie de Jong': {'overall': 85, 'pace': 72, 'shooting': 62, 'passing': 85, 'dribbling': 86, 'defending': 72, 'physic': 68},
    'Cody Gakpo': {'overall': 83, 'pace': 82, 'shooting': 78, 'passing': 76, 'dribbling': 82, 'defending': 38, 'physic': 72},
    'Xavi Simons': {'overall': 83, 'pace': 82, 'shooting': 76, 'passing': 78, 'dribbling': 85, 'defending': 40, 'physic': 62},
    # ── Belgium ──
    'Kevin De Bruyne': {'overall': 90, 'pace': 72, 'shooting': 86, 'passing': 93, 'dribbling': 88, 'defending': 58, 'physic': 72},
    'Thibaut Courtois': {'overall': 89, 'pace': 50, 'shooting': 25, 'passing': 55, 'dribbling': 38, 'defending': 25, 'physic': 85},
    'Romelu Lukaku': {'overall': 83, 'pace': 82, 'shooting': 85, 'passing': 68, 'dribbling': 78, 'defending': 35, 'physic': 88},
    'Jérémy Doku': {'overall': 82, 'pace': 93, 'shooting': 68, 'passing': 72, 'dribbling': 88, 'defending': 32, 'physic': 58},
    # ── Croatia ──
    'Luka Modrić': {'overall': 85, 'pace': 62, 'shooting': 72, 'passing': 88, 'dribbling': 86, 'defending': 68, 'physic': 62},
    'Mateo Kovačić': {'overall': 84, 'pace': 72, 'shooting': 68, 'passing': 82, 'dribbling': 85, 'defending': 72, 'physic': 72},
    'Joško Gvardiol': {'overall': 84, 'pace': 78, 'shooting': 50, 'passing': 65, 'dribbling': 65, 'defending': 84, 'physic': 82},
    # ── Italy ──
    'Gianluigi Donnarumma': {'overall': 87, 'pace': 55, 'shooting': 28, 'passing': 58, 'dribbling': 42, 'defending': 25, 'physic': 82},
    'Nicolò Barella': {'overall': 86, 'pace': 76, 'shooting': 78, 'passing': 82, 'dribbling': 84, 'defending': 76, 'physic': 80},
    # ── Other notable players ──
    'Mohamed Salah': {'overall': 89, 'pace': 90, 'shooting': 87, 'passing': 82, 'dribbling': 88, 'defending': 45, 'physic': 72},
    'Son Heung-min': {'overall': 87, 'pace': 86, 'shooting': 86, 'passing': 82, 'dribbling': 86, 'defending': 42, 'physic': 68},
    'Victor Osimhen': {'overall': 87, 'pace': 88, 'shooting': 85, 'passing': 62, 'dribbling': 80, 'defending': 32, 'physic': 82},
    'Christian Pulisic': {'overall': 82, 'pace': 82, 'shooting': 76, 'passing': 78, 'dribbling': 84, 'defending': 38, 'physic': 62},
    'Alphonso Davies': {'overall': 83, 'pace': 94, 'shooting': 60, 'passing': 72, 'dribbling': 82, 'defending': 76, 'physic': 76},
    'Achraf Hakimi': {'overall': 85, 'pace': 90, 'shooting': 68, 'passing': 78, 'dribbling': 80, 'defending': 78, 'physic': 76},
    'Granit Xhaka': {'overall': 84, 'pace': 52, 'shooting': 75, 'passing': 82, 'dribbling': 76, 'defending': 78, 'physic': 82},
    'Manuel Akanji': {'overall': 84, 'pace': 72, 'shooting': 42, 'passing': 65, 'dribbling': 65, 'defending': 85, 'physic': 82},
    'Jonathan David': {'overall': 83, 'pace': 84, 'shooting': 82, 'passing': 68, 'dribbling': 80, 'defending': 32, 'physic': 72},
    'Federico Valverde': {'overall': 87, 'pace': 82, 'shooting': 80, 'passing': 80, 'dribbling': 82, 'defending': 78, 'physic': 82},
    'Darwin Núñez': {'overall': 84, 'pace': 90, 'shooting': 82, 'passing': 62, 'dribbling': 78, 'defending': 35, 'physic': 78},
    'Ronald Araújo': {'overall': 85, 'pace': 82, 'shooting': 48, 'passing': 55, 'dribbling': 55, 'defending': 86, 'physic': 86},
    'Moisés Caicedo': {'overall': 82, 'pace': 70, 'shooting': 68, 'passing': 76, 'dribbling': 76, 'defending': 82, 'physic': 82},
    'Luis Díaz': {'overall': 84, 'pace': 88, 'shooting': 78, 'passing': 76, 'dribbling': 85, 'defending': 42, 'physic': 68},
    'Erling Haaland': {'overall': 91, 'pace': 89, 'shooting': 93, 'passing': 65, 'dribbling': 80, 'defending': 45, 'physic': 88},
    'Martin Ødegaard': {'overall': 88, 'pace': 72, 'shooting': 80, 'passing': 90, 'dribbling': 88, 'defending': 55, 'physic': 60},
    'Omar Marmoush': {'overall': 82, 'pace': 88, 'shooting': 78, 'passing': 72, 'dribbling': 82, 'defending': 35, 'physic': 68},
    'Ademola Lookman': {'overall': 83, 'pace': 86, 'shooting': 78, 'passing': 74, 'dribbling': 84, 'defending': 38, 'physic': 65},
    'Mehdi Taremi': {'overall': 82, 'pace': 72, 'shooting': 82, 'passing': 72, 'dribbling': 78, 'defending': 42, 'physic': 78},
    'Artem Dovbyk': {'overall': 83, 'pace': 72, 'shooting': 84, 'passing': 60, 'dribbling': 76, 'defending': 32, 'physic': 82},
    'Hakan Çalhanoğlu': {'overall': 85, 'pace': 60, 'shooting': 82, 'passing': 86, 'dribbling': 82, 'defending': 72, 'physic': 76},
    'Arda Güler': {'overall': 80, 'pace': 76, 'shooting': 78, 'passing': 82, 'dribbling': 86, 'defending': 28, 'physic': 52},
    'Kenan Yıldız': {'overall': 79, 'pace': 82, 'shooting': 74, 'passing': 76, 'dribbling': 84, 'defending': 30, 'physic': 58},
    'Folarin Balogun': {'overall': 79, 'pace': 82, 'shooting': 78, 'passing': 65, 'dribbling': 76, 'defending': 30, 'physic': 72},
    'Weston McKennie': {'overall': 78, 'pace': 72, 'shooting': 68, 'passing': 72, 'dribbling': 74, 'defending': 76, 'physic': 80},
    'Tyler Adams': {'overall': 76, 'pace': 74, 'shooting': 58, 'passing': 72, 'dribbling': 72, 'defending': 78, 'physic': 76},
    'Giovanni Reyna': {'overall': 78, 'pace': 78, 'shooting': 72, 'passing': 78, 'dribbling': 82, 'defending': 40, 'physic': 60},
    'Timothy Weah': {'overall': 77, 'pace': 88, 'shooting': 72, 'passing': 66, 'dribbling': 78, 'defending': 38, 'physic': 70},
    'Ricardo Pepi': {'overall': 76, 'pace': 78, 'shooting': 76, 'passing': 60, 'dribbling': 72, 'defending': 28, 'physic': 72},
    'Brenden Aaronson': {'overall': 77, 'pace': 76, 'shooting': 68, 'passing': 76, 'dribbling': 78, 'defending': 55, 'physic': 65},
    'Antonee Robinson': {'overall': 80, 'pace': 86, 'shooting': 55, 'passing': 72, 'dribbling': 72, 'defending': 78, 'physic': 78},
    'Chris Richards': {'overall': 74, 'pace': 72, 'shooting': 42, 'passing': 60, 'dribbling': 58, 'defending': 76, 'physic': 78},
    'Miles Robinson': {'overall': 81, 'pace': 76, 'shooting': 45, 'passing': 58, 'dribbling': 55, 'defending': 82, 'physic': 82},
    'Matt Turner': {'overall': 78, 'pace': 48, 'shooting': 25, 'passing': 52, 'dribbling': 38, 'defending': 22, 'physic': 76},
    'Malik Tillman': {'overall': 76, 'pace': 74, 'shooting': 72, 'passing': 74, 'dribbling': 78, 'defending': 50, 'physic': 68},
    # ── Turkey ──
    'Barış Alper Yılmaz': {'overall': 79, 'pace': 90, 'shooting': 72, 'passing': 68, 'dribbling': 80, 'defending': 30, 'physic': 65},
    # ── Norway ──
    'Sander Berge': {'overall': 79, 'pace': 68, 'shooting': 72, 'passing': 76, 'dribbling': 72, 'defending': 76, 'physic': 82},
    # ── Uruguay ──
    'José María Giménez': {'overall': 83, 'pace': 72, 'shooting': 48, 'passing': 58, 'dribbling': 55, 'defending': 84, 'physic': 82},
    # ── Colombia ──
    'James Rodríguez': {'overall': 78, 'pace': 60, 'shooting': 78, 'passing': 85, 'dribbling': 82, 'defending': 38, 'physic': 55},
    'Jhon Durán': {'overall': 79, 'pace': 84, 'shooting': 78, 'passing': 60, 'dribbling': 72, 'defending': 28, 'physic': 76},
    # ── Japan ──
    'Takefusa Kubo': {'overall': 81, 'pace': 82, 'shooting': 74, 'passing': 78, 'dribbling': 84, 'defending': 38, 'physic': 58},
    'Kaoru Mitoma': {'overall': 82, 'pace': 86, 'shooting': 74, 'passing': 76, 'dribbling': 84, 'defending': 40, 'physic': 62},
    # ── Morocco ──
    'Achraf Hakimi': {'overall': 85, 'pace': 90, 'shooting': 68, 'passing': 78, 'dribbling': 80, 'defending': 78, 'physic': 76},
    'Youssef En-Nesyri': {'overall': 80, 'pace': 82, 'shooting': 80, 'passing': 58, 'dribbling': 72, 'defending': 35, 'physic': 80},
    'Hakim Ziyech': {'overall': 82, 'pace': 72, 'shooting': 78, 'passing': 85, 'dribbling': 86, 'defending': 35, 'physic': 58},
    'Sofyan Amrabat': {'overall': 80, 'pace': 68, 'shooting': 58, 'passing': 72, 'dribbling': 72, 'defending': 80, 'physic': 82},
    # ── Senegal ──
    'Sadio Mané': {'overall': 82, 'pace': 86, 'shooting': 80, 'passing': 72, 'dribbling': 84, 'defending': 42, 'physic': 76},
    # ── South Korea ──
    'Kim Min-jae': {'overall': 85, 'pace': 76, 'shooting': 42, 'passing': 58, 'dribbling': 55, 'defending': 86, 'physic': 84},
    # ── Mexico ──
    'Edson Álvarez': {'overall': 82, 'pace': 65, 'shooting': 65, 'passing': 72, 'dribbling': 72, 'defending': 82, 'physic': 84},
    'Santiago Giménez': {'overall': 81, 'pace': 78, 'shooting': 82, 'passing': 58, 'dribbling': 76, 'defending': 32, 'physic': 78},
    # ── Ecuador ──
    'Moisés Caicedo': {'overall': 82, 'pace': 70, 'shooting': 68, 'passing': 76, 'dribbling': 76, 'defending': 82, 'physic': 82},
    # ── Paraguay ──
    'Miguel Almirón': {'overall': 79, 'pace': 88, 'shooting': 72, 'passing': 72, 'dribbling': 82, 'defending': 38, 'physic': 62},
    'Julio Enciso': {'overall': 76, 'pace': 80, 'shooting': 74, 'passing': 68, 'dribbling': 78, 'defending': 28, 'physic': 60},
}

# ══════════════════════════════════════════════════════════════════════════════
# Team tiers for generating unknown player ratings
# ══════════════════════════════════════════════════════════════════════════════
TIER_1 = {'France', 'England', 'Spain', 'Germany', 'Brazil', 'Argentina', 'Portugal', 'Netherlands', 'Belgium'}
TIER_2 = {'Croatia', 'Colombia', 'Uruguay', 'Japan', 'South Korea', 'Morocco', 'Senegal', 'Turkey',
          'Switzerland', 'Ecuador', 'Norway', 'Mexico', 'Egypt', 'Scotland', 'Sweden', 'Iran',
          'Algeria', 'Austria'}
# TIER_3 = everyone else


def get_team_tier(team):
    if team in TIER_1:
        return 1
    elif team in TIER_2:
        return 2
    return 3


def generate_fc25_ratings():
    """Generate FC25-style ratings for all WC 2026 squad players."""
    print("Generating FC25 ratings...")

    squads = pd.read_csv('data/wc2026_squads.csv')
    rng = np.random.RandomState(42)

    # Build a normalised lookup (accent-stripped, lowered) for fuzzy name matching
    from unicodedata import normalize, category
    def strip_accents(s):
        return ''.join(c for c in normalize('NFD', s) if category(c) != 'Mn')

    known_norm = {strip_accents(k).lower(): v for k, v in KNOWN_RATINGS.items()}
    known_orig = {strip_accents(k).lower(): k for k in KNOWN_RATINGS}

    rows_out = []
    matched = 0

    for _, player in squads.iterrows():
        name = player['player_name']
        pos = player['position']
        team = player['team']
        tier = get_team_tier(team)

        # Try exact match first
        name_norm = strip_accents(name).lower()
        surname_norm = name_norm.split()[-1] if ' ' in name_norm else name_norm

        r = None
        if name in KNOWN_RATINGS:
            r = KNOWN_RATINGS[name]
        elif name_norm in known_norm:
            r = known_norm[name_norm]
        else:
            # Try surname match (for accent mismatches)
            for k, v in known_norm.items():
                k_surname = k.split()[-1] if ' ' in k else k
                if surname_norm == k_surname and len(surname_norm) > 3:
                    r = v
                    break

        if r:
            matched += 1
        else:
            # Generate based on position and tier
            tier_offset = {1: 6, 2: 2, 3: 0}[tier]
            if pos == 'GK':
                ovr = rng.randint(68 + tier_offset, 78 + tier_offset)
                r = {'overall': ovr, 'pace': rng.randint(40, 55), 'shooting': rng.randint(20, 35),
                     'passing': rng.randint(40, 60), 'dribbling': rng.randint(30, 45),
                     'defending': rng.randint(18, 28), 'physic': rng.randint(65, 80)}
            elif pos == 'DEF':
                ovr = rng.randint(68 + tier_offset, 80 + tier_offset)
                r = {'overall': ovr, 'pace': rng.randint(55, 82), 'shooting': rng.randint(35, 58),
                     'passing': rng.randint(50, 72), 'dribbling': rng.randint(50, 70),
                     'defending': rng.randint(72, 85), 'physic': rng.randint(70, 85)}
            elif pos == 'MID':
                ovr = rng.randint(68 + tier_offset, 80 + tier_offset)
                r = {'overall': ovr, 'pace': rng.randint(58, 82), 'shooting': rng.randint(55, 78),
                     'passing': rng.randint(65, 82), 'dribbling': rng.randint(68, 84),
                     'defending': rng.randint(50, 78), 'physic': rng.randint(60, 80)}
            else:  # FWD
                ovr = rng.randint(68 + tier_offset, 80 + tier_offset)
                r = {'overall': ovr, 'pace': rng.randint(72, 90), 'shooting': rng.randint(68, 84),
                     'passing': rng.randint(55, 75), 'dribbling': rng.randint(72, 86),
                     'defending': rng.randint(25, 42), 'physic': rng.randint(58, 78)}

        rows_out.append({
            'long_name': name,
            'short_name': name.split()[-1] if ' ' in name else name,
            'overall': r['overall'],
            'pace': r['pace'],
            'shooting': r['shooting'],
            'passing': r['passing'],
            'dribbling': r['dribbling'],
            'defending': r['defending'],
            'physic': r['physic'],
            'nationality_name': team,
            'club_position': pos,
        })

    df = pd.DataFrame(rows_out)
    df.to_csv('data/male_players.csv', index=False)
    print(f"Saved data/male_players.csv with {len(df)} player ratings")
    print(f"Matched {matched}/{len(df)} players with known ratings")
    return df


if __name__ == '__main__':
    generate_fc25_ratings()
