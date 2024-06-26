#!/usr/bin/python

#Now score version
version="0.47b"

import argparse
import datetime
import os
import requests
import json
import curses
from datetime import datetime as dateT
import time
from tabulate import tabulate
import tabulate as tabulate2
#import openai
import sys
from types import SimpleNamespace
from openai import OpenAI

from rich.console import Console
from rich.markdown import Markdown

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Markdown
from textual.containers import ScrollableContainer

import sys
import platform

#classe per la gestione della visualizzazione dei dati in modo markdown facendo uso della libreria textual
class AnalizeViewerApp(App):
    """A Textual app to manage stopwatches."""

    def __init__(self, markdown_text,color="white"):
        super().__init__()
        self.markdown_text = markdown_text
        self.color=color

    BINDINGS = [("q", "quit", "Quit and back selection")] 

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        # aggiungi un oggetto che permetta la scrittura di un testo scrollabile
        yield ScrollableContainer(Markdown(self.markdown_text))

    # def action_toggle_dark(self) -> None:
    #     """An action to toggle dark mode."""
    #     self.dark = not self.dark

    def action_quit(self) -> None:
        """An action to quit the app."""
        self.app.exit()

    def on_mount(self) -> None:
        #self.screen.styles.background = "black" if self.dark else "white"
        #modifica il titolo della app
        self.title = f"NOWScore Soccer Events CLI v.{version}"
        #self.query_one(Static).styles.background = "green"
        self.query_one(Markdown).styles.color = self.color
        #cambia il colore della scrollbar
        self.query_one(ScrollableContainer).styles.scrollbar_color = self.color
        #cambio il colore di sfondo del Footer
        self.query_one(Footer).styles.background = self.color
        


#cattura l'input da tastiera di un singolo carattere e verifica la piattaforma per la gestione del tasto q
def pauseKeyQ():
    if platform.system() == 'Windows':
        import msvcrt
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8')
                if key == 'q': break
    else:
        import termios
        import tty
        def getch():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch
        while True:
            key = getch()
            if key == 'q': break

#init curse to blessed way
#import blessed

# Crea un oggetto parser
parser = argparse.ArgumentParser(description="NOWScore Soccer Events CLI")

#select apikey
apikey1file="rapidkey1.key"
openaikeyfile="openai.key"

predictionfile="predictions_history.json"

#is the max char to view syntetize prediction
maxlenprediction=20

# Apri il file in modalità lettura
with open(apikey1file, 'r') as file:
    # Leggi il primo rigo
    apikey = str(file.readline().strip())
with open(openaikeyfile, 'r') as file2:
    openaikey=str(file2.readline().strip())


#set timezone
tz="europe/rome"
#set league's ids dictonary
season_year="2023"
#season code list
sc={"SA":135,
    "PL":39,
    "BL":78,
    "LIGA":140,
    "L1":61,
    "ER":88,
    "SL":203,
    "PPL":94,
    "UCL":2,
    "UEL":3,
    "UECL":848,
    "SB":136,
    "SC-A":138,
    "SC-B":942,
    "SC-C":943,
    "JUP":144,
    "SLD":119,
    "BLA":218,
    "SLG":9,
    "J1":98,
    "SAB":71,
    "MLS":253,
    "SPL":307,
    "LIVE":0}

scext={"SA":"Italy Serie A",
       "PL":"England Premier League",
       "BL":"Germay BundesLiga",
       "LIGA":"Spain La Liga",
       "L1":"France Legue 1",
       "ER":"Netherlands EreDivisie",
       "SL":"Turkey Süper Lig",
       "PPL":"Portugal Primeira Liga",
       "UCL":"UEFA Champions League Cup",
       "UEL":"UEFA Europa League Cup",
       "UECL":"EUFA Europa Conference League",
       "SB":"Italy Serie B",
       "SC-A":"Italy Serie C Girone A",
       "SC-B":"Italy Serie C Girone B",
       "SC-C":"Italy Serie C Girone C",
       "JUP":"Belgium Jupyter League",
       "SLD":"Denmark Superlegue",
       "BLA":"Austria Bundeliga",
       "SLG":"Greek Super League",
       "J1":"Japan J1 League",
       "SAB":"Brazil Serie A",
       "MLS":"USA Major League Soccer",
       "SPL":"Saudi-Arabia Pro League",
       "LIVE":"Live all Match of the day"}

scl=list(sc.keys()) #convertiamo il dizionario in lista in modo da poter meglio gestire
sclv=list(scext.values())


parser.add_argument("-l", "--league", help=f"""Show league options:{''.join([f"- {key}={value} " for key, value in zip(sclv, scl)])}""", default=None)

parser.add_argument("-v", "--version", help="Print version of the program and exit",action="store_true")
#parser.add_argument("-live", "--live", help="Show all live match of the day", action="store_true")
parser.add_argument("-s", "--standing", help="""Show standing of selected league\n
                                                if you want show stand of tournament group Uefa
                                                select index of the group.\n
                                                Example: GROUP A=0 GROUP B=1 ....\n""",type=int, choices=range(8), default=-1, nargs="?")
parser.add_argument("noshort", nargs="?", const="noshort", default=None,
                        help="Opzione per visualizzare la classifica dettagliata")
parser.add_argument("-t", "--time_delta", help="""set time from-to show fixtures by day\n
                                                  example: t=-3 set start date to 3 day ago\n
                                                  example: t=7 set stop date from today to 7 days away\n
                                                  example nowscore.py -l PL -t=30 (show all match in premierLeague from today to 30days away)""", default=0)

def get_events_match(id):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/events"

    querystring = {"fixture":id}

    headers = {
        "X-RapidAPI-Key": apikey,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    tab=json.loads(response.text)
    return tab["response"]

#scarica dalla api la lista delle partite nell'intervallo di tempo fissato dagli argomenti
def get_match_list(idleague,datestart=datetime.date.today(),datestop=datetime.date.today()):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"

    querystring = {"league": idleague,
                   "season":season_year,
                   "timezone":tz,
                   "from":datestart,
                   "to":datestop}
    headers = {
        "X-RapidAPI-Key": apikey,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    t=requests.request("GET", url, headers=headers, params=querystring)

    remaining_calls = t.headers.get("X-RateLimit-Requests-Remaining")
    reset_time = t.headers.get("X-RateLimit-Reset")

    tab=json.loads(t.text)
    return tab["response"],remaining_calls
#scarica la classifica della lega ID e eventuale gruppo se multi girone
def get_standing_season(id,gruop=0):
    url = "https://api-football-v1.p.rapidapi.com/v3/standings"

    querystring = {"season":season_year,
                "league":id}

    headers = {
        "X-RapidAPI-Key": apikey,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    remaining_calls = response.headers.get("X-RateLimit-Requests-Remaining")
    reset_time = response.headers.get("X-RateLimit-Reset")

    tab=json.loads(response.text)
    return tab["response"][0]["league"]["standings"][gruop],remaining_calls
#scarica la lista degli 11 iniziali di line-up
def get_start_11(id):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/lineups"

    querystring = {"fixture":id}

    headers = {
        "X-RapidAPI-Key": apikey,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    tab=json.loads(response.text)
    thname,taname=tab["response"][0]["team"]["name"],tab["response"][1]["team"]["name"]
    start11home,start11away=[],[]
    for team1 in tab["response"][0]["startXI"]:
        player=Player(team1["player"]["name"],
                      thname,team1["player"]["number"],team1["player"]["pos"],
                      tab["response"][0]["coach"]["name"],tab["response"][0]["formation"])
        start11home.append(player)
    for team2 in tab["response"][1]["startXI"]:
         player=Player(team2["player"]["name"],
                      taname,team2["player"]["number"],team2["player"]["pos"],
                      tab["response"][1]["coach"]["name"],tab["response"][1]["formation"])
         start11away.append(player)
    start11=[start11home,start11away]
    return start11
#richiede la statistiche dell'evento ID in corso o terminato
def get_statistic(id):

    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics"

    querystring = {"fixture":id}

    headers = {
        "X-RapidAPI-Key": apikey,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    tab=json.loads(response.text)
    teamh=tab["response"][0]["team"]["name"]
    teama=tab["response"][1]["team"]["name"]
    stathome,stataway=[],[]
    for team1 in tab["response"][0]["statistics"]:
        s=TeamStat(teamh,team1["type"],team1["value"])
        stathome.append(s)
    for team2 in tab["response"][1]["statistics"]:
        s=TeamStat(teama,team2["type"],team2["value"])
        stataway.append(s)
    return [stathome,stataway]
#richiede la lista di tutte le partite live per ora poi svulippioamo per settori
def get_live_match():
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"

    querystring = {"live":"all","timezone":"Europe/Rome"}

    headers = {
        "X-RapidAPI-Key": apikey,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
    response = requests.get(url, headers=headers, params=querystring)


    remaining_calls = response.headers.get("X-RateLimit-Requests-Remaining")

    tab=json.loads(response.text)
    return tab["response"],remaining_calls


#richiede all'avvio le prediction e le analisi comparative dell'evento ID
class Prediction():
    def __init__(self,idmatch) -> None:
        self.idmatch=idmatch
        url = "https://api-football-v1.p.rapidapi.com/v3/predictions"
        querystring = {"fixture":self.idmatch}

        headers = {
            "X-RapidAPI-Key": apikey,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        tab=json.loads(response.text)["response"][0]
        self.teamhome=tab["teams"]["home"]["name"]
        self.teamaway=tab["teams"]["away"]["name"]
        self.predictionadv=tab["predictions"]["advice"]
        self.predictionstat={"home":tab["predictions"]["percent"]["home"],
                             "draw":tab["predictions"]["percent"]["draw"],
                             "away":tab["predictions"]["percent"]["away"]}
        self.comparison={"home":tab["comparison"]["total"]["home"],
                         "away":tab["comparison"]["total"]["away"]}
        
    #create a method that receive as parameter a text and call api openai whit apikey variable and retur a text as output
    def gpt_call(prompt,squadra1,squadra2,odds,mode=1,elapsetime=None):
        #openai.api_key = openaikey
        #modulizziamo i prompt in modo da poter far scegliere all'user che tipo di pronostico vuole
        #TODO: aggiungere altri tipi di pronostici
        #TODO:rivedere la possobilita di creare un unico prompt generale che ricalcoli tutti
        #i tipi di pronostici in modo da non dover richiamare ogni volta una nuova funzione e suddivida
        #i tipi di pronostici in base al tipo di analisi che si vuole fare
        content=f"""Sei un analista di calcio e analizzi le partite nei dettagli, cerca di fornire un pronostico
            in base alla classifica delle due squadre che si incontrano ovvero {squadra1} contro {squadra2}.
            analizza bene nel dettaglio i punti in classifica e i gol generali fatti e subiti 
            e fai attenzione ai gol fatti in casa e subiti e quelli fatti fuori casa e subiti. 
            Le striscie di vittorie pareggi e sconfigge consecutive. Tieni conto anche della capacita di una squadra di fare punti 
            in casa o fuori casa basandoti sulle statistiche di ognua di esse. Calcola una media goal fuori casa e in casa di ogni 
            squadra e basati anche su questo includi nella tua analisi generale delle possibilita'. Calcola una
            media punti delle ultime partite giocate anche questo da tenere in conto.
            Crea tebelle sempre verticali di comparazione tra le due squadre in modello grafico markdown e confronta i valori delle statistiche
            che hai calcolato in modo da poter fare un pronostico piu accurato.
            Utilizza uno stile markdown per formattare il testo e crea tabelle di confronto tra le due squadre
            """
        #calcola il pronostico della partita semplice 1 X 2 o combo-bet
        content1="""
            Cerca di dare un pronostico sul possbile esito 1 X 2 o 1X o X2 o se ulteriormente GG se credi
            possano segnare entrambe le squadre o NG se non prevedi che una sqaudra possa non segnare. O1.5 
            se segnano piu di un gol in totale o piu di 2
            che sarebbe over 2,5 o piu' O.3.5 etc. Analogamente U1,5 o U2,5 o U3,5 tipo se pensi
            non facciano piu di 3 gol e via discorrendo. puoi anche combinare piu pronostici se 
            pensi ci siano buono probabilita,
            ma cerca di essere dettagliato nella motivazione che ti spinge a credere
            in quello che prevedi. 
            Basandoti sulle statistiche calcola la possibilita che la squadra di casa segni almeno 1 
            gol e fai lo stesso con la squadra che gioca fuori casa, e se ce un alta probabilita oltre 
            il 65% segnalalo.
            Tendi ad evitare di suggerire risultati fissi come 1 o X o 2 singoli come singolo pronostico, a meno che non altamente probabili, ma 
            cerca di essere prudente quando coprendo i pronostici con doppie tipo 1X o X2 sempre se abbastanza probabili. 
            Dopo aver fatto uno schema di analisi generale,
            se riesci crea una tabella comparativa delle due squadre a confronto con tutti i dati che prendi in analisi,
            ma nel costruire eventuale tabella usa sempre abbreviazioni per gli headers dei valori che stai indicando in modo da non 
            generare una tabella ricca ma formattata bene,esempio PUNTI usa P oppure tipo mediaGol fatti in casa MGH e fuoricasa MGA,
            confronto di posizione in classifica posto in classifica POS_C, e via discorrendo. Abbrevia tu il resto hai capito cosa intendo.
            Magari dopo la tabella crea se puoi, 
            una legenda dei headers delle stats che hai sintetizzato e che potrebbero non essere chiari,
            ma non specificare mai il testo degli headers completi nella tabella ma solo le abbreviazioni, 
            questo e' molto importante.
            Poi tendenzialmente suggerisci spesso
            risultati sui gol e sul numero di gol o sul possibile gol di una squadra che gioca, sempre tenendo 
            conto delle difese avversarie e della media di subire gol nel rispettivo campo.
            Cerca sempre di tenerti cauto nelle previsioni ammeno che non 
            credi di averne molte probabilita in quello che prevedi non ti sbilanciare troppo.
            Cosa molto importate, calcola quante partite mancano al termine del campionato e se una delle due squadre
            si trova in una posizione di classifica che la possa portare a retrocedere o a vincere il campionato, 
            e se ci sono altre squadre che insiduano come punteggio la squadra in question evidenzialla e
            calcola che potrebbe portare preessione su di essa, che possono influenzare il risultato finale del campionato. 
            Probabilmente quella squadra sara' piu motivata a vincere o a non perdere, e questo potrebbe influenzare il risultato della partita, 
            e quindi il tuo pronostico deve tenerne conto. Allo stesso modo se una squadra e' gia retrocessa (calcolando quante partite mancano e se matematicamente puo ancora salvarsi) o ha gia vinto il campionato
            (fai lo stesso ragionamento matematico sulla squadra seconda in classifica), potrebbe
            avere meno motivazione a vincere e quindi il tuo pronostico dovrebbe riflettere questa situazione. Calcolando il punteggio
            delle squadre sottostanti o soprastanti in classifica, e quindi se hanno possibilita di insidiare 
            o compromettere la posizione di una delle due squadre in campo a fine campionato, tenendo presento
            che un squadra che lotta per la salvezza e fortemente motivata nelle fasi finali del torneo
            a vincere o a fare punti se pero ne ha ancora la speranza, altrimenti di solito molla. Stesso vorra
            dire se una squadra ha magari gia vinto lo scudetto non avrea tanta tensione a vincere e potrebbe,
            concedere qualcosa agli avversari.
            Vanno anche considerati i posizionamenti per accedere alla coppe che in genere sono nelle prime posizioni della classifica, e che
            quindi creano motivazioni aggiuntive per le squadre. Per tanto considera sempre la situazione generale del campionato e delle squadre
            Riassumi sempre tutti i tuoi pronostici alla fine in un tag finele tra parentesi [] esempio se dici 1X e possibile GG scrivi P[1X+GG] o 
            sempre esempio P[X2+NG+U2.5] oppure ancora P[X] in modo che possa recuperali nel testo. Grazie contro su si te.
            Fornisci sempre un solo pronostico e non un usare mai nel testo le parentesi quadre se non esclusivamente per generare il risultato come ti ho chiesto,
            ed all'interno delle parentesi non aggiungere decorazioni come asterisci o altro non necessario per permettere la lettura ad una funzione esterna.
            Formatta il tutto utilizzando schemi e tabelle in stile simil markdown.
            """
        #probabilita di segnare di ogni squadra
        content2=f"""
            Analizzare le probabilità di {squadra1} di segnare quanti gol nella partita e anche di {squadra2}. 

            Probabilità di Gol con la Distribuzione di Poisson:
            La distribuzione di Poisson è spesso utilizzata per modellare il numero di gol segnati in una partita di calcio. Questo modello si basa sulla frequenza media di gol segnati da una squadra.
            Per calcolare la probabilità che una squadra segni un certo numero di gol, puoi utilizzare la distribuzione di Poisson con il parametro corrispondente alla media dei gol segnati dalla squadra.
            Ad esempio, se la squadra A ha una media di 1,5 gol segnati per partita, puoi calcolare la probabilità che segnino esattamente 1 gol utilizzando la formula della distribuzione di Poisson.
            Ricorda che la distribuzione di Poisson assume che gli eventi (i gol in questo caso) siano indipendenti e che la frequenza media sia costante.
            Expected Goals (xG):
            Gli Expected Goals (xG) sono un altro approccio statistico per valutare la probabilità di un tiro di diventare un gol.
            Si basano su un modello che analizza centinaia di migliaia di tiri e assegna a ciascuno di essi un valore compreso tra 0 (impossibile segnare) e 1 (gol certo) in base alla posizione del tiro.
            Puoi utilizzare gli xG per valutare la probabilità di segnare da una determinata posizione sul campo.
            Analisi delle Statistiche delle Squadre:
            Considera le statistiche delle squadre, come la media dei gol segnati e subiti in casa e in trasferta.
            Calcola la probabilità che una squadra segni un certo numero di gol in base alle medie e alle condizioni specifiche della partita (ad esempio, l’avversario, la forma attuale della squadra, ecc.).
            Descriivi il risultato in una forma sintetica in modo che possa essere letta da una funzione autometica ad esempio se prevedi che la squadra di casa segni 1 gol
            sintetizza con la formula [S1-1] oppure [S1-numero_di_gol:percentuale_di_probabilita] e se la squadra ospite [S2-numeroi_di_gol:percetuale_di_probabilita],
            per tanto ad esempio se prevedi che la squadra di casa segni 1 gol sintetizza con la formula [S1-1:70%] e se la squadra ospite [S2-0:65%], oltertutto se 
            vuoi segnalare entambe preferisco che il risultato sia sempre sintetizzato come [S1-1:70%,S2-0:65%], la cosa importante
            e che tieni in considerazione solo percentuali superiori o uguali a 65%.
            Descrivi tutto in formato simil markdown e crea delle tabelle con tutti le possibili probabilita di numero di gol 
            segnati da ogni squadra.
            """
        content3=f"""
            Dato le statistiche delle squadre {squadra1} e {squadra2}, calcola la probabilità di vittoria di una delle due squadre utilizzando solo la doppia chance. Ad esempio, 
            se le statistiche mostrano che la squadra A ha vinto il 60% delle partite e la squadra B il 40%, calcola la probabilità di vittoria della {squadra1} con 
            la doppia chance 1X e della squadra {squadra2} con la doppia chance X2. 
            Sintetizza il risultato nella formila tra parentesi quadre DC[risultato] dove risultato puo essere 1X 12 X2,
            e non aggiungere altro nelle parentesi qaudre in modo che possa essere letto da una funzione esterna.
            Crea una tabella dei risultati possobili doppia chance ovvero 1X 12 X2 con le relative probabilita ed eventuali quote scommesse.
            stile markdown
            """
        #prompt che mi restituisca il risultato esatto
        content4=f"""
            Basandoti sulle statistiche dettagliate delle squadre {squadra1} e {squadra2}, considera le prestazioni recenti, 
            la forma in casa e in trasferta, i gol fatti e subiti, e qualsiasi altra informazione rilevante, 
            analizza le probabilità di diversi risultati esatti della partita. Considera anche l'importanza della partita 
            per entrambe le squadre e come questo potrebbe influenzare il loro approccio al gioco.

            Utilizza le informazioni disponibili per calcolare le probabilità di diversi risultati esatti, come 1-0, 2-1, 0-0, ecc., 
            e fornisci una breve spiegazione su come hai raggiunto queste conclusioni. Se disponibili, includi anche le quote 
            delle scommesse per questi risultati esatti per vedere se ci sono discrepanze significative tra le tue analisi 
            e le aspettative del mercato.

            Infine, basandoti sulle tue analisi e le quote disponibili, suggerisci uno o più risultati esatti che ritieni 
            più probabili o che offrono il miglior valore in termini di scommessa. Riassumi il tuo pronostico finale 
            in una formula sintetica, ad esempio [RE:2-1], che possa essere facilmente interpretata. 
            O anche eventualmente piu di un risultato esatto se lo ritieni altamente probabile come [RE:2-1,1-2] ma l'unica condizione e che sia sempre sintetizzato come [RE:risultato_esatto1,risultato_esatto2,risultato_esatto3,..].
            Anche qui stilizza una tabella dei possibili risultati esatti in style markdown
            """
        #prompt che analizza il pronostico in live in base alla situazione attuale
        content5=f"""
            Analizza la partita in corso tra {squadra1} e {squadra2} e cerca di fornire un pronostico in tempo reale
            basato sulla situazione attuale del gioco. 
            Guarda il tempo trascorso nella partita attuale che e' di {elapsetime} minuti, calcola quanto manca alla fine della partita
            dei 90 minuti e considera la situazione attuale del punteggio e delle statistiche delle squadre.
            Considera i gol segnati, le espulsioni, i cartellini gialli,
            le sostituzioni e qualsiasi altra informazione rilevante che potrebbe influenzare il risultato finale.
            Utilizza le statistiche della partita in corso e le prestazioni recenti delle squadre per calcolare le probabilità
            di diversi risultati e fornire un pronostico accurato. Analizza la situazione attuale del gioco e cerca di prevedere
            come si evolverà nei prossimi minuti. Fornisci una breve spiegazione su come hai raggiunto le tue conclusioni e
            suggerisci essenzialmente chi vincera la partita o chi dovrebbe segnare il prossimo gol."""
        
        #on selction on user compose pormpt by set mode parameter
        #content+=content1 if mode==1 else content2
        message = f"""data questa classifica {prompt} attuale 
                della partita tra {squadra1} contro {squadra2} """
        match mode:
            case 1:
                content+=content1
            case 2:
                content+=content2
            case 3:
                content+=content3
            case 4:
                content+=content4
            case 5:
                content+=content5
                message = f"""data la situazione attuale della partita tra {squadra1} contro {squadra2} 
                            con questi dati attuali{prompt}"""
                
        #se abbiamo le quote della partita allegale al prompt
    
        
        if odds != None:
            content+=f"""Allegando anche questa lista json delle quotazioni della partita, {odds},  cerca di suggerire una possibile
                        vantaggiosa che tu pensi sia possibile e dammi sempre in oltre le quotazioni di tutti i risultati 
                        che mi suggerisci. Se riesci prendi in cosiderazione anche risultati di di vittorie di una squadra o 
                        di un altra con piu goal di scarto e dammi le quotazioni vantaggiose sempre se ce
                        ne puo essere la progabilita"""
        # messages = [ {"role": "system", "content":content} ]
       

        client = OpenAI(api_key=openaikey)

        completion=client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":message},
                {"role":"user","content":content}
            ]
        )
        return completion.choices[0].message.content
    #definiamo un medoto che estre il pronostico e lo sintetizza 
    def compactOdds(testo):
        inizio = testo.find("[")
        fine = testo.find("]")
        
        if inizio != -1 and fine != -1:
            testo_tra_parentesi = testo[inizio + 1 : fine]
            return testo_tra_parentesi
        else:
            return None
        


#richiede quote per eventi nel campionato richiesto alla data richiesta
def get_match_odds(idleague,date):

    url = "https://api-football-v1.p.rapidapi.com/v3/odds"

    querystring = {"league":idleague,
                    "season":"2023",
                    "date":date,
                    "bookmaker":"1"}

    headers = {
        "X-RapidAPI-Key": apikey,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    tab=json.loads(response.text)
    odds=[]
    for r in tab["response"]:
        odds.append(Odds(r))
    return odds

#classe dati per odds     
class Odds():
    def __init__(self,response: dict) -> None:
        #self.response=SimpleNamespace(**response)
        self.bookmaker=response["bookmakers"][0]["name"]
        self.league=SimpleNamespace(**response["league"])
        self.fixture=SimpleNamespace(**response["fixture"])
        self.odd=dict(response["bookmakers"][0])


# Leggi gli argomenti dalla riga di comando
args = parser.parse_args()

#creiamo una classe per la catalogalizzazione degli incontri
class Player:
    def __init__(self,name,team,number,position,coach,scheme) -> None:
        self.name=name
        self.team=team
        self.num=number
        self.pos=position
        self.coach=coach
        self.scheme=scheme

#classe che cataloga le statistiche dell'incontro stabilite da rapidapi
#esempio shot on goal, total shot, corner, etc
class TeamStat:
    def __init__(self,teamName,tipo,value):
        self.teamName=teamName
        self.type=tipo
        self.value=value

class Match:
    def __init__(self,idleague,idmatch,thome,taway,ghome,gaway,status,min,datematch,referee,stadium,city,country):
        self.idleague=idleague
        self.idfixture=idmatch
        self.teamhome=str(thome)
        self.teamaway=taway
        self.goalshome=str(ghome) if ghome!=None else "-"
        self.goalsaway=str(gaway) if gaway!=None else "-"
        self.status=status
        self.minutes=str(min) if min!=None else "0"
        #self.extratime=extratime if extratime!=None else 0
        self.date=dateT.fromisoformat(datematch).strftime("%H:%M %d/%m/%Y")
        self.referee=referee
        self.stadium=stadium
        self.location=city
        self.country=str(country).upper()

        #proprietá globali di statisthe eventi
        self.homestat=None
        self.awaystat=None
        #propieta che popola l'evento con un altra classe dall'esterno che si 
        #occupera delle statistiche
        self.odd=None
        self.pronostic=""
        self.analize="" #testo della analisi del match
        #regista la data in formato anno-mese-giorno valido per eventuali query
        self.date_req_format=dateT.fromisoformat(datematch).strftime("%Y-%m-%d") # formato data valido per query
    #metodo che scarica gli eventi del match.
    def flow_events(self):
        list_event=get_events_match(self.idfixture)
        tabellaeventi=[[self.teamhome,"",self.goalshome,"vs",self.goalsaway,"",self.teamaway]]
        for e in list_event:
            edetail=e["detail"]
            abbrev={"Normal Goal":"G","Red Card":"RC","Yellow Card":"YC","subst":"SUB","Var":"V","Penalty":"P","Missed Penalty":"MP","Own Goal":"OG"}
            icon=""
            if e["type"]=="Goal":
                if e["detail"]=="Normal Goal":
                    edetail="GOAL"
                    icon=abbrev["Normal Goal"] 
                elif e["detail"]=="Penalty":
                    edetail="Penalty/GOAL"
                    icon=abbrev["Penalty"]
                elif e["detail"]=="Missed Penalty":
                    edetail="Missed/Penalty"
                    icon=abbrev["Missed Penalty"]
                elif e["detail"]=="Own Goal":
                    edetail="Own/Goal <="
                    icon=abbrev["Own Goal"]
            if e["type"]=="Var":
                edetail="VAR: "+e["detail"]
                icon=abbrev["Var"]
            if e["type"]=="subst":
                edetail=str(e["detail"])
                icon=abbrev["subst"]
            if e["detail"]=="Yellow Card":
                icon=abbrev["Yellow Card"]
            if e["detail"]=="Red Card":
                icon=abbrev["Red Card"]
        
            #aggiungi il tempo di recupero
            extratime=e["time"]["extra"] if e["time"]["extra"]!=None else 0

            if e["assist"]["name"]!=None:
                dbrow=str(e["player"]["name"])+"/"+str(e["assist"]["name"])
            else:
                dbrow=e["player"]["name"]
            if e["team"]["name"]==self.teamhome:
                tabellaeventi.append([dbrow,
                                    edetail,icon,
                                    str(e["time"]["elapsed"]+extratime),"","",""])
            if e["team"]["name"]==self.teamaway:
                tabellaeventi.append(["","","",
                                    str(e["time"]["elapsed"]+extratime),icon,
                                    edetail,
                                    dbrow])
        #return tabulate(tabellaeventi,headers="firstrow")
        return tabellaeventi
    #metodo che scarica la lista degli 11 di partenza
    def list_start11(self):
        f1,f2=get_start_11(self.idfixture)
        lista11=[["","",self.teamhome,self.goalshome,self.goalsaway,self.teamaway],
                 ["","",f1[0].scheme,"","",f2[0].scheme],
                 ["N","P","--","--","N","P",""]]
        for i1,i2 in zip(f1,f2):
            lista11.append([i1.num,i1.pos,i1.name,i2.num,i2.pos,i2.name])
        lista11.append(["--","--","--","--","--","--"])
        lista11.append(["Coach",":",f1[0].coach,"Coach",":",f2[0].coach])
        return lista11

    #metodo che scarica la lista delle statistiche del match
    def list_statistic(self):
        f1,f2=get_statistic(self.idfixture)
        list_stat=[["Statistic Date","|",self.teamhome,self.teamaway,":",self.goalshome,self.goalsaway],
                   ["--","|","--","--","","",""]]
        for i1,i2 in zip(f1,f2):
            list_stat.append([i1.type,"|",i1.value,i2.value])
        return list_stat
#salva la predizione nei file di archivio
def upload_save_prediction(idmatch,prediction,analize):
    #carichiamo il file se esiste
    if not(os.path.exists(predictionfile)): # se non esiste
        load={"id":idmatch,"pred":prediction,"analize":analize}
        with open(predictionfile,"w") as file:
            json.dump(load,file)
    else:
        with open(predictionfile,"r") as file:
            load=json.load(file)
            if isinstance(load, dict):
                load = [load]  # Se è un dizionario, convertilo in una lista
            find=False
            for p in load:
                if p["id"]==idmatch:  
                    p["pred"]=prediction
                    p["analize"]=analize
                    find=True
                    break
            if not(find): #il record e viene aggiunto al file
                load.append({"id":idmatch,"pred":prediction,"analize":analize})
        with open(predictionfile, "w") as file:        
            json.dump(load,file,indent=4)
#carica predizioni dallo storico salvato
def load_saved_prediction(event):
    try:
        with open(predictionfile, "r") as file:
            load=json.load(file)
            if isinstance(load, dict):
                load = [load]  # Se è un dizionario, convertilo in una lista
            for p in load:
                if p["id"]==event.idfixture:
                    event.pronostic=p["pred"] if isinstance(p["pred"],str) and (len(p["pred"])<=maxlenprediction-2) else "press [A] ToView"
                    event.analize=p["analize"]
        
    except FileNotFoundError:
        pass  #non fare nulla se il file non esiste
    
    return event
    
            
class Winmenu:
    def __init__(self,events:list,title="select options"):
        self.events=events
        self.title=title
        self.classifica=None
        #inizializza il curses windows
        self.screen=curses.initscr()
        curses.curs_set(0)
        curses.noecho()
        self.screen.keypad(1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_MAGENTA)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_YELLOW)
        curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        #pair color per segnalazione GOAL
        curses.init_pair(7, curses.COLOR_GREEN, curses.COLOR_BLUE)
        #pair color per segnalazione Yellow Card
        curses.init_pair(8,curses.COLOR_YELLOW, curses.COLOR_BLUE)
        #pai color per segnalazione Red Card
        curses.init_pair(9,curses.COLOR_RED, curses.COLOR_BLUE)
        curses.init_pair(10, curses.COLOR_CYAN, curses.COLOR_BLACK)
        #pair color per segnalazione HELP
        curses.init_pair(11, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(12, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(13, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        self.height, self.width = self.screen.getmaxyx()
    # Definisci una funzione che prende una lista di liste di # Definisci una funzione che prende una lista di liste di stringhe come parametro
    def formatta_liste(self,eventi):
        dict_country={"ARGENTINA":"🇦🇷",
                    "DOMINICAN-REPUBLIC":"🇩🇴",  
                    "AUSTRALIA":"🇦🇺",
                    "BELGIUM":"🇧🇪",
                    "BRAZIL":"🇧🇷",
                    "COLOMBIA":"🇨🇴",
                    "CROATIA":"🇭🇷",
                    "DENMARK":"🇩🇰",
                    "FINLAND":"🇫🇮",
                    "ENGLAND":"🇬🇧",
                    "FRANCE":"🇫🇷",
                    "GERMANY":"🇩🇪",
                    "GREECE":"🇬🇷",
                    "REP. IRELAND":"🇮🇪",
                    "REPUBULIC CZECH":"🇨🇿",
                    "MEXICO":"🇲🇽",
                    "NETHERLANDS":"🇳🇱",
                    "POLAND":"🇵🇱",
                    "PORTUGAL":"🇵🇹",
                    "SPAIN":"🇪🇸",
                    "SWITZERLAND":"🇨🇭",
                    "TURKEY":"🇹🇷",
                    "ITALY":"🇮🇹",
                    "USA":"🇺🇸",
                    "CHILE":"🇨🇱",
                    "CHINA":"🇨🇳",
                    "AUSTRIA":"🇦🇹",
                    "ALBANIA":"🇦🇱",
                    "BULGARIA":"🇧🇬",
                    #tutte le nazioni africane
                    "NIGERIA":"🇳🇬",
                    "EGYPT":"🇪🇬",
                    "TANZANIA":"🇹🇿",
                    "KENYA":"🇰🇪",
                    "UGANDA":"🇺🇬",
                    "DRC":"🇩🇲",
                    "SOMALIA":"🇸🇴",
                    "ETHIOPIA":"🇪🇹",
                    "MOROCCO":"🇲🇦",
                    "SUDAN":"🇸🇩",
                    "CAMERUN":"🇨🇲",
                    "MALI":"🇲🇱",
                    "SENEGAL":"🇸🇳",
                    "TUNISIA":"🇹🇳",
                    #tutte le nazioni asiatiche   
                    "INDIA":"🇮🇳",
                    "PAKISTAN":"🇵🇰",
                    "BANGLADESH":"🇧🇩",
                    "MYANMAR":"🇲🇲",
                    "JAPAN":"🇯🇵",
                    "CHINA":"🇨🇳",
                    "SOUTH-KOREA":"🇰🇷",
                    "VIETNAM":"🇻🇳",
                    "MONGOLIA":"🇲🇳",
                    "THAILAND":"🇹🇭",
                    "PHILIPPINES":"🇵🇭",
                    "INDONESIA":"🇮🇩",
                    "MALAYSIA":"🇲🇾",
                    "SINGAPORE":"🇸🇬",
                    "CYPRUS":"🇨🇾",
                    "TURKIY":"🇹🇷",
                    "UKRAINE":"🇺🇦",
                    "WORLD":"🌍"}
        #calcoliamo la lunghezza massima di ogni della chiave in dict_country
        max_len_country=max(len(key) for key in dict_country.keys())    

        liste=[]
        for event in eventi:
            event=load_saved_prediction(event)
            liste.append([event.teamhome,event.teamaway,event.goalshome,event.goalsaway,":",
                       event.status,event.minutes+" " if int(event.minutes)<10 else event.minutes," - ",
                       event.date,event.country.ljust(max_len_country)," : ",event.pronostic])
        # Crea una lista vuota per memorizzare le liste formattate
        liste_formattate = []
        # Trova la lunghezza della parola più lunga nelle prime due posizioni di tutte le liste
        max_len = max(len(lista[i]) for lista in liste for i in range(2))
        #creaiamo un dict di chiave come il nome delle nazioni dei campionai e valore come emoji della bandiera della nazione rappresentante
        # Per ogni lista nella lista di liste
        for lista in liste:
            # Crea una stringa formattata usando il metodo join e il metodo format
            # Usa il parametro <{max_len}> per allineare le prime due parole a sinistra e riempire con spazi
            # Aggiungi il resto delle parole senza formattazione
        
            stringa = " ".join("{:<{max_len}}".format(lista[i], max_len=max_len) for i in range(2)) + " " + " ".join(lista[2:])
            #aggiungi la bandiera della nazione se esiste il nome della chiave del dict nella lista 
            found=False
            for country in stringa.split():
                if country in dict_country:
                    stringa=dict_country[country]+" "+stringa
                    found=True
                    break
            if not(found):
                stringa=dict_country["WORLD"]+" "+stringa
            #Aggiungi la stringa formattata alla lista delle liste formattate
            liste_formattate.append(stringa)
            # Restituisci la lista delle liste formattate
        return liste_formattate

    def tabulate_data(self,data):
        # Trova il numero massimo di colonne in qualsiasi riga
        max_cols = max(len(row) for row in data)
        # Riempie le righe mancanti con liste vuote
        data_padded = [row + [''] * (max_cols - len(row)) for row in data]
        # Costruisce l'intestazione per la tabella
        headers = [''] * max_cols
        # Tabula i dati
        #table = tabulate2.tabulate(data_padded, headers=headers, tablefmt='plain')
        table=tabulate(data_padded, headers=headers, tablefmt='mixed')

        return table
    def tabulate_strings(self,data,typetable="plain"):
        # Trova il numero massimo di colonne in qualsiasi riga
        max_cols = max(len(row) for row in data)
        # Riempie le righe mancanti con liste vuote
        data_padded = [row + [''] * (max_cols - len(row)) for row in data]
        # Costruisce l'intestazione per la tabella
        headers = [''] * max_cols
        # Tabula i dati
        table = tabulate2.tabulate(data_padded, headers="firstrow", tablefmt=typetable)
        # Splitta la tabella in righe
        table_lines = table.split('\n')
        #rimuove il '\n' finale alla fine di ogni riga
        table_lines=[line.replace("\n","") for line in table_lines]
        
        # Trova la lunghezza massima di qualsiasi riga
        max_length = max(len(line) for line in table_lines)
        # Riempie le righe mancanti con spazi vuoti per uniformare la lunghezza
        table_lines_padded = [line.ljust(max_length) for line in table_lines]

        return table_lines_padded
     #definiamo una funzione islive che stabilisce se "1H" o "2H" sono presenti nella lista di options
    #per tanto esiste un evento live in corso
    def isLive(self,lista_di_stringhe):
        # Parole chiave da cercare
        parole_chiave = ["1H", "2H","HT"]    
        # Itera attraverso la lista di stringhe
        for stringa in lista_di_stringhe:
            # Normalizza le stringhe a maiuscole per rendere la ricerca insensibile al maiuscolo/minuscolo
            stringa_normalizzata = stringa.upper()
            # Verifica la presenza delle parole chiave
            for parola in parole_chiave:
                if parola in stringa_normalizzata:
                    return True  # Restituisce True al primo ritrovamento
        # Se nessuna delle parole chiave viene trovata, restituisce False
        return False
    #creare una funzione che crean una finestrra nello schermo nelle cordinate e la dimensione da specificare con la coppia colori da specificare e il testo da visualizzare
    def create_window(self,y,x,row,col,virtualscreenRow,virtualscreenCol,color_pair,text,title="",control_scroll=True):
        win=curses.newwin(row,col,y,x)
        win.bkgd(curses.color_pair(color_pair))
        win.box()
        if title != "":
            win.addstr(0,(len(title)+col)//2-len(title),f"[ {title.upper()} ]")
        win.refresh()
        pad=curses.newpad(virtualscreenRow,virtualscreenCol)
        pad.bkgd(curses.color_pair(color_pair))
        pad.addstr(text)
        if not control_scroll:
            pad.refresh(0,0,y+1,x+1,y+row-2,x+col-2)
            return pad
        #definiamo il pad all'interno del box win
        xpad=0
        ypad=0
        #ciclo di controllo scroll
        while True:
            pad.refresh(ypad,xpad,y+1,x+1,y+row-2,x+col-2)

            key=self.screen.getch()
            if key==curses.KEY_UP and ypad>0:
                ypad-=1
            elif key==curses.KEY_DOWN and ypad<virtualscreenRow:
                ypad+=1
            elif key==curses.KEY_LEFT and xpad>0:
                xpad-=1
            elif key==curses.KEY_RIGHT and xpad<virtualscreenCol:
                xpad+=1
            elif key==ord("q"):
                pad.erase()
                win.erase()
                self.screen.clear()
                break
            pad.refresh(0,0,y+1,x+1,y+row-2,x+col-2)
        return pad
    #display menu della lista eventi e ne processa le varie sotto-opzioni
    def menu(self):        
        #TODO: da rivedere la funzione menu per la visualizzazione delle opzioni
        #perche se lo schermo e troppo piccolo non visualizza correttamente le opzioni
        #e cade in errore, si cosiglia anche qui l'uso di un pad per la visualizzazione delle opzioni
        #e la gestione dello scroll, oppure si puo usare try except per gestire l'errore
        #controllo se ci sono eventi altrimenti esco con codice -1
        if len(self.events)==0:
            curses.endwin()
            #STAMPA MESSAGGIO DI ERRORE CON RICH
            Console().print(Markdown(f"# No events to show today in the selected league! {self.title}"))
            exit()
        
        options=self.formatta_liste(self.events)
        seth=len(options)+2 if (len(options)+3)<self.height else self.height-3
        menu_items = len(options)
        max_items = self.height - 5

        if menu_items > max_items:
            scroll_offset = 0
            selected = 0
        else:
            scroll_offset = 0
            selected = -1
        
        header_win = curses.newwin(1,self.width,0,0)
        footer_win=curses.newwin(1,self.width,self.height-1,0)
        info_win=curses.newwin(1,self.width,seth+1,0)
        #menu_win=curses.newwin(seth,len(max(options))+maxlenprediction,1,2)
        #definiamo la finestra menu_win con le dimensioni massime di options e la lunghezza massima di ogni stringa
        menu_win=curses.newwin(seth,len(max(options,key=len))+maxlenprediction,1,2)
        while True:
            header_win.clear()
            footer_win.clear()
            header_win.bkgd(curses.color_pair(2))
            footer_win.bkgd(curses.color_pair(2))
            try:
                header_win.addstr(0,5, self.title)
                footer_win.addstr(0,3,"PRESS: [Q]uit - [F]orm.Start11 -" 
                                   "[S]tats match - [<-|]data - [P]redictions - "
                                "[R]efresh - [O]dds - [A]nalized")
            except:
                footer_win.addstr(0,3,"PRESS: '[Q]uit - [H]elp")

            menu_win.clear()
            menu_win.box()
            options=self.formatta_liste(self.events)
            for i, option in enumerate(options[scroll_offset:scroll_offset+max_items]):
                if i == selected - scroll_offset:
                    menu_win.attron(curses.color_pair(1))
                else:
                    menu_win.attroff(curses.color_pair(1))
                try:
                    menu_win.addstr(1 + i, 2, option)
                except:
                    menu_win.clear()
                    menu_win.addstr(0,5,"No space to show options!")
                    menu_win.refresh()
                    #chiudiamo il programma alla pressione di un tasto
                    key=self.screen.getch()
                    exit()
        
            #striscia di informazioni plus sul match
            
            info_win.bkgd(curses.color_pair(6))
            info_win.clear()
            try:
                info_win.addstr(0,5,f"City: {self.events[selected].location} | Stadium: {self.events[selected].stadium} |  Ref: {self.events[selected].referee}")
            except:
                info_win.addstr(0,5,"No space to show info!")
            self.screen.refresh()
            menu_win.refresh()
            header_win.refresh()
            footer_win.refresh()
            info_win.refresh()
            menu_win.attroff(curses.color_pair(1))
            key = self.screen.getch()

            if key == curses.KEY_UP:
                if selected > 0:
                    selected -= 1
                    if selected < scroll_offset:
                        scroll_offset -= 1
            elif key == curses.KEY_DOWN:
                if selected < menu_items - 1:
                    selected += 1
                    if selected >= scroll_offset + max_items:
                        scroll_offset += 1
            #selezione data match
            elif (key == ord("\n") and (self.events[selected].status != "NS") and (self.events[selected].status != "PST")):
                selected_item = options[selected]
                data=self.events[selected].flow_events()
                header_win.clear()
                header_win.addstr(0,5,selected_item)
                footer_win.clear()
                footer_win.addstr(0,5,"PRESS 'q' to close")
                
                table=self.tabulate_strings(data,typetable="fancy_outline")
                
                max_len=max([len(line) for line in table])
                if max_len+4>self.width:
                    max_len=self.width-1

                header_win.refresh()
                footer_win.refresh()
                #creiamo una finestra di visualizzazione degli eventi pad all'interno della finestra data_win 
                #quindi scaliamo la finestra data_win per visualizzare il pad all'interno
                data_pad=curses.newpad(200,200)
                data_pad.bkgd(curses.color_pair(2))
                
                for r,line in enumerate(table):
                    if ("GOAL" in line) or ("Own/Goal" in line):
                        data_pad.attron(curses.color_pair(7))
                    elif "Yellow Card" in line:
                        data_pad.attron(curses.color_pair(8))
                    elif "Red Card" in line:
                        data_pad.attron(curses.color_pair(9))
                    else:
                        data_pad.attron(curses.color_pair(2)) #setta colore verde sullo sfondo
                    data_pad.addstr(r,1,line)
                row=0
                col=0

                while True:
                    try:
                        data_pad.refresh(row,col,3,3,len(data)+5,max_len+4)
                        key=self.screen.getch()
                        if key==curses.KEY_UP and row>0:
                            row-=1
                        elif key==curses.KEY_DOWN and row<len(data)-1:
                            row+=1
                        elif key==curses.KEY_LEFT and col>0:
                            col-=1
                        elif key==curses.KEY_RIGHT and col<len(max(data)):
                            col+=1
                        elif key==ord("q"):
                            #data_win.erase()
                            self.screen.clear()
                            break
                    except:
                        data_pad.erase()
                        self.create_window(self.height-5,2,3,60,60,60,1,"Error in data loading",title="Error occurred")
                        break
            # #selezione start 11 line up
            elif (key == ord("f")and(self.events[selected].status != "NS") and (self.events[selected].status != "PST")):
                try:
                    dataf=self.events[selected].list_start11()
                    tablef=self.tabulate_data(dataf)
                    self.create_window(5,2,20,65,80,100,3,tablef,title="Start 11 Line UP")
                    self.screen.clear()
                except:
                    self.create_window(5,2,6,50,50,50,3,"Error in data loading",title="Error occurred")
                    self.screen.clear()
            #finestra di stampa statistiche partite
            elif (key == ord("s") and (self.events[selected].status != "NS") and (self.events[selected].status != "PST") ):
                header_win.clear()
                header_win.bkgd(curses.color_pair(4))
                header_win.addstr(0,3,f"Match Statistic between {self.events[selected].teamhome} VS {self.events[selected].teamaway}")
                footer_win.clear()
                footer_win.bkgd(curses.color_pair(4))
                footer_win.addstr(0,3,"PRESS 'q' to close")
                try:
                    dataf=self.events[selected].list_statistic()
                    tablef=self.tabulate_data(dataf)
                    self.create_window(5,2,self.height-7,60,80,100,4,tablef,title="Stats of the match")
                except:
                    self.create_window(5,2,6,50,50,50,4,"Error in data loading",title="Error occurred")
                self.screen.clear()

            #previsioni per incontri live
            elif (key==ord("l")and (self.isLive(options))):
                
                try:
                    header_win.clear()
                    header_win.bkgd(curses.color_pair(13))
                    header_win.addstr(0,3,f"prediction STAT: {self.events[selected].teamhome} VS {self.events[selected].teamaway}")
                    header_win.refresh()
                    footer_win.clear()
                    footer_win.bkgd(curses.color_pair(13))
                    footer_win.addstr(0,3,"PRESS 'q' to close - PRESS 'ARROW UP/DOWN' to scroll text")
                    footer_win.refresh()
                    title=f"Analize LIVE-Match...: {self.events[selected].teamhome} vs {self.events[selected].teamaway}"
                    pred_win=curses.newwin(3,len(title)+2,self.height//2,self.width//2-(len(title)//2))
                    pred_win.box()
                    pred_win.bkgd(curses.color_pair(13))           
                    pred_win.addstr(1, 1, title)
                    pred_win.refresh()
                    datalivescore=self.events[selected].list_statistic()
                    
                    if datalivescore!=None:
                        # Console().clear()
                        # Console().print(Markdown((f"## Live Match Statistic and Prediction {self.events[selected].teamhome} VS {self.events[selected].teamaway}")))
                        #tabella delle statistiche
                        #tablef=self.tabulate_data(datalivescore)
                        #tablef=tabulate(datalivescore,headers="columns")
                        predizione=Prediction.gpt_call(datalivescore,
                                                       self.events[selected].teamhome,self.events[selected].teamaway,
                                                       self.events[selected].odd,mode=5,
                                                       elapsetime=self.events[selected].minutes)
                        pred_win.clear()
                        pred_win.refresh()  
                        curses.endwin()
                        #addpredizione=f"{tablef}\n\n< {predizione}"
                        #Console().print(Markdown(predizione))
                        #Console.clear()
                        AnalizeViewerApp(predizione,color="white").run()
                    else:
                        #Console().print(Markdown("## No data to show"))
                        #AnalizeViewerApp("## No data to show").run()
                        self.create_window(5,2,6,50,50,50,3,"NO data to load",title="Error occurred")
                except Exception as e:
                    #stampa lerrore in caso di errore e il tipo di errore intercettato
                    # Console().print(Markdown(f"## Error in prediction {e}"))
                    # Console().print(Markdown("## Press [Q] to exit"))
                    self.create_window(5,2,6,50,50,50,3,"Error in data loading",title="Error occurred")
                    #pauseKeyQ()
            #selezione data match               
                
            #richiesta previsioni betting e confronto
            elif ((key == ord("p") or (key==ord('g') or (key==ord('d')or (key==ord('e'))))) and (self.events[selected].status == "NS")):
                header_win.clear()
                header_win.bkgd(curses.color_pair(5))
                header_win.addstr(0,3,f"prediction STAT: {self.events[selected].teamhome} VS {self.events[selected].teamaway}")
                header_win.refresh()
                footer_win.clear()
                footer_win.bkgd(curses.color_pair(5))
                footer_win.addstr(0,3,"PRESS 'q' to close - PRESS 'ARROW UP/DOWN' to scroll text")
                footer_win.refresh()
                title=f"Analize Match...: {self.events[selected].teamhome} vs {self.events[selected].teamaway}"
                pred_win=curses.newwin(3,len(title)+2,self.height//2,self.width//2-(len(title)//2))
                pred_win.box()
                pred_win.bkgd(curses.color_pair(5))           
                pred_win.addstr(1, 1, title)
                pred_win.refresh()
                #inizia la predizione
                if self.classifica == None :
                    list_stand,rem=get_standing_season(self.events[selected].idleague)
                    self.classifica=[["POS","TEAM","PO","RO","W","D","L","WH","DH","LH","WA","DA","LA","GF","GS","GFH","GSH","GFA","GSA","FORM","STATUS"]]
                    for t in list_stand:
                        row=[t["rank"],t["team"]["name"],t["points"],t["all"]["played"],
                            t["all"]["win"],t["all"]["draw"],t["all"]["lose"],
                            t["home"]["win"],t["home"]["draw"],t["home"]["lose"],
                            t["away"]["win"],t["away"]["draw"],t["away"]["lose"],
                            t["all"]["goals"]["for"],t["all"]["goals"]["against"],
                            t["home"]["goals"]["for"],t["home"]["goals"]["against"],t["away"]["goals"]["for"],t["away"]["goals"]["against"],
                            ' '.join(t["form"]),t["status"]]
                        self.classifica.append(row)
                tabclassifica=tabulate(self.classifica,headers="firstrow")
                               
                if key==ord('p'):
                    #chiamata GPT mode 1
                    predizione=Prediction.gpt_call(tabclassifica,self.events[selected].teamhome,self.events[selected].teamaway,self.events[selected].odd)
                elif key==ord('g'):
                    #chiamata GPT mode 2
                    predizione=Prediction.gpt_call(tabclassifica, self.events[selected].teamhome, self.events[selected].teamaway, self.events[selected].odd,mode=2)
                elif key==ord('d'):
                    #chiamata GPT mode 3
                    predizione=Prediction.gpt_call(tabclassifica, self.events[selected].teamhome, self.events[selected].teamaway, self.events[selected].odd,mode=3)
                elif key==ord('e'):
                    #chiamata GPT mode 4
                    predizione=Prediction.gpt_call(tabclassifica, self.events[selected].teamhome, self.events[selected].teamaway, self.events[selected].odd,mode=4)
                
                self.events[selected].analize=predizione
                self.events[selected].pronostic=Prediction.compactOdds(predizione)
                #salva/aggiorna la predizione sul server
                upload_save_prediction(self.events[selected].idfixture,self.events[selected].pronostic,predizione)
                #self.create_window(4,4,self.height-6,self.width-6,150,self.width-10,5,predizione,title=f"Prevision: {self.events[selected].teamhome} VS {self.events[selected].teamaway}")
                pred_win.clear()
                pred_win.refresh()
                pred_win.erase()
                curses.endwin()
                AnalizeViewerApp(predizione,color="green").run()
                
            #carica le quote per tutti gli eventi selezionati
            #TODO: non carica le quote per gli eventi diversi della data corrente
            elif (key == ord("o") and (self.events[selected].status == "NS")):
                header_win.clear()
                header_win.bkgd(curses.color_pair(6))
                header_win.addstr(0, 5, f"Odds Loading...")
                header_win.refresh()
                #draw odds window center screen
                odds_win=curses.newwin(3, self.width-2, self.height//2-2, 2) #crea una finestra per le quote
                odds_win.box()
                odds_win.bkgd(curses.color_pair(6))
                odds_win.addstr(1, 2, "LOADING ALL SELECTED ODDS...")
                odds_win.refresh()
                footer_win.clear()
                footer_win.bkgd(curses.color_pair(6))
                footer_win.addstr(0, 5, "PRESS 'q' to close")
                footer_win.refresh()
                #load odds 
                pl=0
                tab_odds=get_match_odds(self.events[selected].idleague, self.events[selected].date_req_format)
                for todds in tab_odds:
                    for ievents in range(len(self.events)):
                        if self.events[ievents].idfixture==todds.fixture.id:
                            self.events[ievents].odd=todds.odd
                            pl+=1
                            odds_win.clear()
                            odds_win.box()
                            # odds_win.addstr(1, 2, f"LOADING ODDS... {pl}/{len(self.events)}")
                            # odds_win.refresh()
                            #draw a progress bar for loading
                            odds_win.addstr(0, 6, f"[ LOADING ODDS... {pl}/{len(self.events)} ]")
                            odds_win.addstr(1, 2, f"{'#' * (pl*100//len(self.events))}")
                            odds_win.refresh()

                            #pause 1 second
                            time.sleep(0.7)
                            break
                odds_win.clear()
                odds_win.box()
                odds_win.addstr(1, 2, "LOADED!")
                odds_win.refresh()                                
                while True:
                    pausekey=self.screen.getch() #fa una pausa
                    if pausekey==ord("q"):
                        odds_win.erase()
                        self.screen.clear()
                        break
            #refresh option            
            elif (key == ord("r") and self.isLive(options)):
                menu_win.clear()
                return 1 #refresh code for now not used
            #read analized match if exist
            elif (key == ord("a") and (self.events[selected].analize != "")):
                #close curses and show app analizeviewer
                curses.endwin()
                analize_app=AnalizeViewerApp(self.events[selected].analize)
                analize_app.run()

            #help option window key h
            elif (key == ord("h")):
                header_win.clear()
                header_win.bkgd(curses.color_pair(8))
                header_win.addstr(0, 3, f"Help")
                header_win.refresh()
                footer_win.clear()
                footer_win.bkgd(curses.color_pair(8))
                footer_win.addstr(0, 3, "PRESS 'q' to close")
                footer_win.refresh()
                #crea una finestra per la visualizzazione delle opzioni al centro dello schermo stampando
                #una lista di opzioni
                optionshelp=["Press 'S' Statistics of the Match",
                             "Press 'A' Analyze Match only preloaded",
                             "Press 'O' Load Odds","Press 'R' Refresh",
                             "Press 'P' Prediction Basic",
                             "Press 'G' Prediction Teams goals",
                             "Press 'D' Prediction DC only prevision",
                             "Press 'E' Prediction Expected Results",
                             "Press 'F' Start 11 Line UP",
                             "Press 'C' Show Standing",
                             "Press 'L' Prediction Live Events",
                             "Press 'H' Help",
                             "Press 'Q' Exit"]
                start_y=(self.height-len(optionshelp))//2
                start_x=(self.width-max(len(x) for x in optionshelp))//2
                help_win=curses.newwin(len(optionshelp)+2, max(len(x) for x in optionshelp)+2, start_y, start_x)
                help_win.box()
                help_win.bkgd(curses.color_pair(11))
                for ri,so in enumerate(optionshelp):
                    help_win.addstr(ri+1, 1, so)
                help_win.addstr(0, 2, "HOT KEYS")
                help_win.refresh()

                while True:
                    pausekey=self.screen.getch() #fa una pausa
                    if pausekey==ord("q"):
                        help_win.erase()
                        self.screen.clear()
                        break
            #show windows con classifica su richiesta del tasto c
            elif key == ord("c"):
                header_win.clear()
                header_win.bkgd(curses.color_pair(4))
                header_win.addstr(0, 3, f"STANDING")
                header_win.refresh()
                footer_win.clear()
                footer_win.bkgd(curses.color_pair(4))
                footer_win.addstr(0, 3, "PRESS 'q' to close - PRESS 'ARROW UP/DOWN' to scroll text")
                footer_win.refresh()
                #genera la classifica se non è stata generata
                if self.classifica==None:
                    list_stand,rem=get_standing_season(self.events[selected].idleague)
                    self.classifica=[["POS","TEAM","PO","RO","W","D","L","WH","DH","LH","WA","DA","LA","GF","GS","GFH","GSH","GFA","GSA","FORM","STATUS"]]
                    for t in list_stand:
                        row=[t["rank"],t["team"]["name"],t["points"],t["all"]["played"],
                            t["all"]["win"],t["all"]["draw"],t["all"]["lose"],
                            t["home"]["win"],t["home"]["draw"],t["home"]["lose"],
                            t["away"]["win"],t["away"]["draw"],t["away"]["lose"],
                            t["all"]["goals"]["for"],t["all"]["goals"]["against"],
                            t["home"]["goals"]["for"],t["home"]["goals"]["against"],t["away"]["goals"]["for"],t["away"]["goals"]["against"],
                            ' '.join(t["form"]),t["status"]]
                        self.classifica.append(row)
                tabclassifica=self.tabulate_strings(self.classifica)
                #stampa riga per riga la classifica nella var tabclassifica ma cambia colore di sfondo per la riga selezionata se la selezione e self.events[selected].teamhome o self.events[selected].teamaway    
                padclassifica=curses.newpad(40,200)
                #sfondo nero e testo bianco
                padclassifica.bkgd(curses.color_pair(12))
                #padclassifica.box()
                #padclassifica.addstr(0,0,f"[ STANDING ]")
                for r,line in enumerate(tabclassifica):
                    if (self.events[selected].teamhome in line) or (self.events[selected].teamaway in line):
                        padclassifica.attron(curses.A_REVERSE)
                    else:
                        padclassifica.attroff(curses.A_REVERSE)
                    padclassifica.addstr(r,1,line)
                padmaxY=len(tabclassifica)+5 if len(tabclassifica)+5<self.height-3 else self.height-3
                
                row=0
                col=0
                while True:
                    padclassifica.refresh(row,col,4,4,padmaxY,self.width-6)
                    #scroll control up e down
                    pausekey=self.screen.getch()
                    if pausekey==curses.KEY_UP and row>0:
                        row-=1
                    elif pausekey==curses.KEY_DOWN and row<padmaxY:
                        row+=1
                    elif pausekey==curses.KEY_LEFT and col>0:
                        col-=1
                    elif pausekey==curses.KEY_RIGHT and col<150:
                        col+=1
                    elif pausekey==ord("q"):
                        padclassifica.erase()
                        self.screen.clear()
                        break
            
                header_win.erase()
                footer_win.erase()
                self.screen.clear()
            
            #set exit point
            elif key == ord("q"):
                #exit to main 
                curses.endwin()
                return -1

def main(stdscr):
    if args.version:
        #usciamo dal programma dopo la visualizzazione della versione ma non cancelliamo la finestra
        return "version"


    if (args.league!=None) and (args.league.upper() in scl):
        if args.standing !=-1 :
            if args.standing is None :
                args.standing=0

            list_stand,rem=get_standing_season(sc[args.league.upper()],args.standing)
            #versione classifica semplice
            if not (args.noshort=="noshort"):	
                classifica=[["POS","TEAM","PO","RO","W","D","L","GF","GS","FORM"]]
                for t in list_stand:
                    row=[t["rank"],t["team"]["name"],t["points"],t["all"]["played"],
                        t["all"]["win"],t["all"]["draw"],t["all"]["lose"],
                        t["all"]["goals"]["for"],t["all"]["goals"]["against"],
                        ' '.join(t["form"])]
                    classifica.append(row)
            else:
                    
                #versione dettagliata della classifica
                classifica=[["POS","TEAM","PO","RO","W","D","L","GF","GS","GFH","GSH","GFA","GSA","FORM","STATUS"]]
                for t in list_stand:
                    row=[t["rank"],t["team"]["name"],t["points"],t["all"]["played"],
                        t["all"]["win"],t["all"]["draw"],t["all"]["lose"],
                        t["all"]["goals"]["for"],t["all"]["goals"]["against"],
                        t["home"]["goals"]["for"],t["home"]["goals"]["against"],t["away"]["goals"]["for"],t["away"]["goals"]["against"],
                        ' '.join(t["form"]),t["status"]]
                    classifica.append(row)
            #stampa la classifica
            curses.endwin()
            tabclassifica=tabulate(classifica,headers="firstrow",tablefmt="rounded_outline")
            Console().print("\nStanding of "+scext[args.league.upper()]+" Championship update at: "+str(datetime.date.today())+" REM:"+str(rem)+"\n"
                +tabclassifica
                +"\n")
            #print(Prediction.gpt_call(tabulato+" analizza questa classifica"))
            #pause=input("Press any key to continue...")
            return "standing"
        else:
            tdelta=int(args.time_delta)
            if tdelta>=0:
                tdeltafrom=datetime.date.today()
                tdeltato=datetime.date.today()+datetime.timedelta(tdelta)
            else:
                tdeltafrom=datetime.date.today()+datetime.timedelta(tdelta)
                tdeltato=datetime.date.today()
            
            selection=0
            while selection != -1:
 
                #verifica se viene invocata la funzione livescore di tutti i match 
                if (args.league.upper()=="LIVE"):
                    p,rem=get_live_match()
                else:
                    p,rem=get_match_list(sc[args.league.upper()],datestart=tdeltafrom,datestop=tdeltato)
                ev=[]
                for m in p:
                    #carichiamo i dati del match nella classe
                    ev.append(Match(m["league"]["id"],m["fixture"]["id"],m["teams"]["home"]["name"],m["teams"]["away"]["name"],
                                m["goals"]["home"],m["goals"]["away"],m["fixture"]["status"]["short"],
                                m["fixture"]["status"]["elapsed"],m["fixture"]["date"],
                                m["fixture"]["referee"],m["fixture"]["venue"]["name"],
                                m["fixture"]["venue"]["city"],m["league"]["country"]))
                    # voglio sapere quale e il response delléxtratime di un match 
                    ev.sort(key=lambda match: match.country)

                try:
                    selection=Winmenu(ev,f"{scext[args.league.upper()]} From {tdeltafrom} to {tdeltato} REM:{rem}").menu()
                    if selection == -1:
                        #print(f"NOWScore {version} richiesta di uscita dal programma!")
                        return "exit"
                except ValueError as error:
                    curses.endwin()
                    Console().print(f"errore {error}")
                    key=input("...(press any key)")
                    #break
                    return "nodata"

    try:
        pass
    except:
        return "error"

match curses.wrapper(main):
    case "version":
               
        Console().print(f"NowScore - version [bold]{version}[/bold]")
        
    case "error":
        Console().print(Markdown("## non hai definito codice lega"))
    case "nodata":
        Console().print(Markdown("## non ci sono eventi da visualizzare..."))
    case "standing":
        Console().print(Markdown("### classifica visualizzata"))
    case "exit":
        Console().print(Markdown(f"# NOWScore {version} Exit Request!"))
    case _:
        Console().print("[red]Generic ERROR!![/red]")
        Console().print("[bold]Exit Program[/bold]")






