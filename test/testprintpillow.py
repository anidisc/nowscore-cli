import curses
from PIL import Image

def print_png(stdscr):
    # Carica l'immagine PNG con Pillow
    image = Image.open("1189.png")

    # Converte l'immagine in scala di grigi e ridimensiona a 10x10
    #image = image.convert("L").resize((10, 10))

    # Ottieni i dati dei pixel
    pixels = list(image.getdata())

    # Inizializza curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    stdscr.clear()

    # Stampa i pixel a schermo
    for i, pixel in enumerate(pixels):
        x = i % 10
        y = i // 10
        stdscr.addstr(y, x, " ", curses.color_pair(1) | curses.A_REVERSE if pixel > 128 else curses.color_pair(1))

    stdscr.refresh()
    stdscr.getch()

# Esegui la funzione con curses
curses.wrapper(print_png)
