from blessed import Terminal

def center_window(term, width, height):
    # Calcola le coordinate per posizionare la finestra al centro
    x = term.width // 2 - width // 2
    y = term.height // 2 - height // 2
    return x, y

def draw_centered_window(term, title, options, selected_option):
    window_width = len(max(options, key=len)) + 4  # Calcola la larghezza in base alla opzione più lunga
    window_height = len(options) + 4  # Calcola l'altezza in base al numero di opzioni
    window_x, window_y = center_window(term, window_width, window_height)
    
    with term.location(window_x, window_y):
        with term.location(0, 0):
            # Disegna il bordo esterno
            print(term.green + term.bold('┌' + '─' * (window_width - 2) + '┐'))
            print('│' + term.center(title, window_width - 2) + '│')
            print('├' + '─' * (window_width - 2) + '┤')
            
            # Disegna le opzioni
            for i, option in enumerate(options):
                with term.location(0, i + 3):
                    if i == selected_option:
                        print('│' + term.reverse(term.bold(option.ljust(window_width - 4))) + '│')
                    else:
                        print('│' + option.ljust(window_width - 4) + '│')
            
            # Disegna il bordo inferiore
            print('└' + '─' * (window_width - 2) + '┘' + term.normal)

def main():
    term = Terminal()
    
    with term.fullscreen(), term.cbreak():
        title = "Menu"
        options = ["Opzione 1", "Opzione 2", "Opzione 3", "Opzione 4", "Opzione 5"]
        selected_option = 0
        
        while True:
            # Disegna la finestra al centro dello schermo
            draw_centered_window(term, title, options, selected_option)
            
            # Legge l'input dell'utente
            key = term.inkey()
            
            # Gestisce la navigazione tra le opzioni
            if key.name == 'KEY_UP':
                selected_option = max(0, selected_option - 1)
            elif key.name == 'KEY_DOWN':
                selected_option = min(len(options) - 1, selected_option + 1)
            elif key.name == 'q':
                break
            
            # Esegui azione sulla selezione
            # (puoi personalizzare questa parte in base alle tue esigenze)
            if key.code==10 or key.code==32:
                print(f"Hai selezionato: {options[selected_option]}")
                # Aggiungi qui la logica per l'azione associata all'opzione selezionata

if __name__ == "__main__":
    main()
