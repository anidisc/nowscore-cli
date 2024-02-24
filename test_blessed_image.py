import blessed
import requests

# Importa il link all'SVG
link = "https://media.api-sports.io/flags/al.svg"

# Richiedi l'SVG dal link
response = requests.get(link)

# Estrai il contenuto dell'SVG dalla risposta
svg = response.content.decode('utf-8')
print(type(svg))

# Crea un oggetto Terminal
term = blessed.Terminal()

# Disegna l'SVG
term.draw_svg(svg)

# Mostra il terminale
term.show()
