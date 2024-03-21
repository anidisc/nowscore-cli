#!/usr/bin/python

#Now score version
version=0.41

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
import openai
import sys
from types import SimpleNamespace

#init curse to blessed way
#import blessed

# Crea un oggetto parser
parser = argparse.ArgumentParser(description="NOWScore Soccer Events CLI")

#select apikey
apikey1file="rapidkey1.key"
openaikeyfile="openai.key"

predictionfile="predictions_history.json"

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
            "X-RapidAPI-Key": "f83fc6c5afmsh8a6fa4ab634b844p1c85b5jsnbd22d812cb4f",
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
    def gpt_call(prompt,squadra1,squadra2,odds):
        openai.api_key = openaikey
        content=f"""Sei un analist di calcio e analizzi le partite nei dettagli, cerca di fornire un prononisto
        in base alla classifica delle due sqadre che si incontrano ovvero {squadra1} contro {squadra2}
        analizza bene nel dettaglio i punti in classifica e i gol fatti generial e subiti 
        e fai attenzioni ai gol fatti in casa e subiti e quelli fatti fuori casa e subiti. 
        Le striscie di vittorie pareggi e sconfigge consecutive. Tieni conto anche della capacita di una squadra di fare punti 
        in casa o fuori casa basandoti sulle statistiche. Calcola una media goal fuori casa e in casa di ogni 
        squadra e basati anche su questo includi nella tua analisi generale delle possibilita'. Calcola una
        media punti delle ultime partite giocate anche questo da tenere in conto.
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
        Tendi ad evitare di suggeriri risultati fissi come 1 o X o 2 singoli, a meno che non altamente probabili, ma 
        cerca di essere prudente quando coprendo i pronostici con doppie tipo 1X o X2 sempre se abbastanza probabili. 
        Ma tendenzialmente suggerisci spesso
        risultati sui gol e sul numero di gol o sul possibile gol di una squadra che gioca, sempre tenendo 
        conto delle difese avversarie e della media di subire gol nel rispettivo campo.
        Cerca sempre di tenerti cauto nelle previsioni ammeno che non 
        credi di averne molte probabilita in quello che prevedi non ti sbilanciare troppo.
        Azzarda anche un probabile risultato esatto, stabilendo con che probabilta possa verificarsi.
        Rifai questo processo almeno 10 volte e poi fai uma media di tutte le tue analisi che ti sono uscite.
        Riassumi sempre tutti i tuoi pronostici alla fine in un tag finele tra parentesi [] esempio se dici 1X e possibile GG scrivi P[1X+GG] o 
        sempre esempio P[X2+NG+U2.5] oppure ancora P[X] in modo che possa recuperali nel testo. Grazie contro su si te"""
        if odds != None:
            content+=f"""Allegando anche questa lista json delle quotazioni della partita, {odds},  cerca di suggerire una possibile
                        vantaggiosa che tu pensi sia possibile e dammi sempre in oltre le quotazioni di tutti i risultati 
                        che mi suggerisci. Se riesci prendi in cosiderazione anche risultati di di vittorie di una squadra o 
                        di un altra con piu goal di scarto e dammi le quotazioni vantaggiose sempre se ce
                        ne puo essere la progabilita"""
        messages = [ {"role": "system", "content":content} ]
        message = f"""data questa classifica {prompt} fammi un pronostico 
        della partita tra {squadra1} contro {squadra2} """
        if message:
            messages.append(
                {"role": "user", "content": message},
            )
            chat = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=messages
            )
        answer = chat.choices[0].message.content
        return answer
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
                    "bookmaker":"6"}

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
        # self.odd={"1":response["bookmakers"][0]["bets"][0]["values"][0]["odd"],
        #           "X":response["bookmakers"][0]["bets"][0]["values"][1]["odd"],
        #           "2":response["bookmakers"][0]["bets"][0]["values"][2]["odd"],
        #           "GG":response["bookmakers"][0]["bets"][2]["values"][0]["odd"],
        #           "NG":response["bookmakers"][0]["bets"][2]["values"][1]["odd"],
        #           "1X":response["bookmakers"][0]["bets"][3]["values"][0]["odd"],
        #           "12":response["bookmakers"][0]["bets"][3]["values"][1]["odd"],
        #           "X2":response["bookmakers"][0]["bets"][3]["values"][2]["odd"]}
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

    #metodo che scarica gli eventi del match.
    def flow_events(self):
        list_event=get_events_match(self.idfixture)
        tabellaeventi=[[self.teamhome,"",self.goalshome,"vs",self.goalsaway,"",self.teamaway]]
        for e in list_event:
            match e["type"]:
                case "Goal":
                    e["detail"]="GOAL" if e["detail"]=="Normal Goal" else "Penalty/GOAL"
            #aggiungi il tempo di recupero
            extratime=e["time"]["extra"] if e["time"]["extra"]!=None else 0

            if e["assist"]["name"]!=None:
                dbrow=str(e["player"]["name"])+"/"+str(e["assist"]["name"])
            else:
                dbrow=e["player"]["name"]
            if e["team"]["name"]==self.teamhome:
                tabellaeventi.append([dbrow,
                                    e["detail"],"",
                                    str(e["time"]["elapsed"]+extratime),"","",""])
            if e["team"]["name"]==self.teamaway:
                tabellaeventi.append(["","","",
                                    str(e["time"]["elapsed"]+extratime),"",
                                    e["detail"],
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
                    event.pronostic=p["pred"]
                    event.analize=p["analize"]
        
    except FileNotFoundError:
        pass  #non fare nulla se il file non esiste
    
    return event
    
            
class Winmenu:
    def __init__(self,events:list,title="select options"):
        self.events=events
        self.title=title
        self.classifica=None
    # Definisci una funzione che prende una lista di liste di # Definisci una funzione che prende una lista di liste di stringhe come parametro
    def formatta_liste(self,eventi):
        liste=[]
        for event in eventi:
            event=load_saved_prediction(event)
            liste.append([event.teamhome,event.teamaway,event.goalshome,event.goalsaway,":",
                       event.status,event.minutes+" " if int(event.minutes)<10 else event.minutes," - ",event.date,event.country," ",event.pronostic])
        # Crea una lista vuota per memorizzare le liste formattate
        liste_formattate = []
        # Trova la lunghezza della parola più lunga nelle prime due posizioni di tutte le liste
        max_len = max(len(lista[i]) for lista in liste for i in range(2))
        # Per ogni lista nella lista di liste
        for lista in liste:
            # Crea una stringa formattata usando il metodo join e il metodo format
            # Usa il parametro <{max_len}> per allineare le prime due parole a sinistra e riempire con spazi
            # Aggiungi il resto delle parole senza formattazione
            stringa = " ".join("{:<{max_len}}".format(lista[i], max_len=max_len) for i in range(2)) + " " + " ".join(lista[2:])
            # Aggiungi la stringa formattata alla lista delle liste formattate
            liste_formattate.append(stringa)
            # Restituisci la lista delle liste formattate
        return liste_formattate

    def tabulate_strings(self,data):
        # Trova il numero massimo di colonne in qualsiasi riga
        max_cols = max(len(row) for row in data)
        # Riempie le righe mancanti con liste vuote
        data_padded = [row + [''] * (max_cols - len(row)) for row in data]
        # Costruisce l'intestazione per la tabella
        headers = [''] * max_cols
        # Tabula i dati
        table = tabulate2.tabulate(data_padded, headers=headers, tablefmt='plain')
        # Splitta la tabella in righe
        table_lines = table.split('\n')
        # Trova la lunghezza massima di qualsiasi riga
        max_length = max(len(line) for line in table_lines)
        # Riempie le righe mancanti con spazi vuoti per uniformare la lunghezza
        table_lines_padded = [line.ljust(max_length) for line in table_lines]

        return table_lines_padded
    # giustifica un testo lungo e ne restuisce una lista di stringhe
    def giustifica_testo(self, testo, lunghezza):
        parole = testo.split()
        righe = []
        riga_corrente = []
        lunghezza_corrente = 0
        
        for parola in parole:
            # Se la lunghezza della parola supera la lunghezza massima consentita, 
            # va direttamente in una nuova riga
            if len(parola) > lunghezza:
                righe.append("".join(riga_corrente))
                riga_corrente = []
                lunghezza_corrente = 0
                while len(parola) > lunghezza:
                    righe.append(parola[:lunghezza])
                    parola = parola[lunghezza:]
            
            # Se la parola non va oltre la lunghezza massima consentita nella riga corrente,
            # la aggiungiamo e aggiorniamo la lunghezza corrente
            if lunghezza_corrente + len(riga_corrente) + len(parola) <= lunghezza:
                riga_corrente.append(parola)
                lunghezza_corrente += len(parola)
            # Altrimenti, creiamo una nuova riga con la parola
            else:
                righe.append(" ".join(riga_corrente))
                riga_corrente = [parola]
                lunghezza_corrente = len(parola)
        
        # Aggiungiamo l'ultima riga, se non vuota
        if riga_corrente:
            righe.append(" ".join(riga_corrente))
        
        return righe
    #definiamo una funzione islive che stabilisce se "1H" o "2H" sono presenti nella lista di options
    #per tanto esiste un evento live in corso
    def isLive(self,lista_di_stringhe):
        # Parole chiave da cercare
        parole_chiave = ["1H", "2H"]    
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

    #display menu della lista eventi e ne processa le varie sotto-opzioni
    def menu(self):        
        options=self.formatta_liste(self.events)
        screen=curses.initscr()
        curses.curs_set(0)
        curses.noecho()
        screen.keypad(1)
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

        height, width = screen.getmaxyx()
        seth=len(options)+2 if (len(options)+3)<height else height-3
        setw=len(max(options))+15 if (len(max(options))+15<width-2) else width-2

        menu_items = len(options)
        max_items = height - 5

        if menu_items > max_items:
            scroll_offset = 0
            selected = 0
        else:
            scroll_offset = 0
            selected = -1
        while True:
            #screen.clear()
            #header striscia titolo eventi scelti
            header_win = curses.newwin(1,width,0,0)
            header_win.bkgd(curses.color_pair(2))
            header_win.addstr(0,5, self.title)
            #main box menu
            menu_win = curses.newwin(seth, setw, 1, 5)
            menu_win.box()
            #footer stricia messaggi di aiutoq
            footer_win=curses.newwin(1,width,height-1,0)
            footer_win.bkgd(curses.color_pair(2))
            try:
                footer_win.addstr(0,3,"PRESS: 'q' exit - 'f' 11-lineups - " 
                                  "'s' match-Stats - 'ENTER' data - 'p' Predictions Match - "
                                  "'r' refresh - 'o' odds")
            except:
                footer_win.clear()
                footer_win.addstr(0,3,"PRESS: 'q' - 'f' - 's' - 'p' -'r' - 'o'")
            for i, option in enumerate(options[scroll_offset:scroll_offset+max_items]):
                if i == selected - scroll_offset:
                    menu_win.attron(curses.color_pair(1))
                else:
                    menu_win.attroff(curses.color_pair(1))
                menu_win.addstr(1 + i, 2, option)
            #striscia di informazioni plus sul match
            info_win=curses.newwin(1,width,seth+1,0)
            info_win.bkgd(curses.color_pair(6))
            try:
                info_win.addstr(0,5,f"City: {self.events[selected].location} | Stadium: {self.events[selected].stadium} |  Ref: {self.events[selected].referee}")
            except:
                info_win.clear()
                info_win.addstr(0,5,"No space ti show info!")
            screen.refresh()
            menu_win.refresh()
            header_win.refresh()
            footer_win.refresh()
            info_win.refresh()

            key = screen.getch()

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
                data_win = curses.newwin(len(data)+3,width-5,4,4)
                data_win.box()
                data_win.bkgd(curses.color_pair(2)) #setta colore verde sullo sfondo
                header_win.clear()
                header_win.addstr(0,5,selected_item)
                footer_win.clear()
                footer_win.addstr(0,5,"PRESS 'q' to close")
                table=self.tabulate_strings(data)
                for r,line in enumerate(table):
                    if "GOAL" in line:
                        data_win.attron(curses.color_pair(7))
                    elif "Yellow Card" in line:
                        data_win.attron(curses.color_pair(8))
                    elif "Red Card" in line:
                        data_win.attron(curses.color_pair(9))
                    else:
                        data_win.attron(curses.color_pair(2)) #setta colore verde sullo sfondo
                    data_win.addstr(r+1,2,line)
                data_win.refresh()
                header_win.refresh()
                footer_win.refresh()
                while True:
                    pausekey=screen.getch() #fa una pausa
                    if pausekey==ord("q"):
                        data_win.erase()
                        screen.clear()
                        break
            #selezione start 11 line up
            elif (key == ord("f")and(self.events[selected].status != "NS") and (self.events[selected].status != "PST")):
                form_win=curses.newwin(20,65,2,2)
                form_win.box()
                form_win.bkgd(curses.color_pair(3))
                header_win.clear()
                header_win.bkgd(curses.color_pair(3))
                header_win.addstr(0,3,f"{self.events[selected].teamhome} VS {self.events[selected].teamaway} Start 11 Line UP")
                footer_win.clear()
                footer_win.bkgd(curses.color_pair(3))
                footer_win.addstr(0,3,"PRESS: 'q' to close")
                dataf=self.events[selected].list_start11()
                tablef=self.tabulate_strings(dataf)
                for r,line in enumerate(tablef):
                    form_win.addstr(r+1,2,line)

                form_win.refresh()
                header_win.refresh()
                footer_win.refresh()
                while True:
                    pausekey=screen.getch() #fa una pausa
                    if pausekey==ord("q"):
                        form_win.erase()
                        screen.clear()
                        break
            #finestra di stampa statistiche partite
            elif (key == ord("s") and (self.events[selected].status != "NS") and (self.events[selected].status != "PST") ):
                form_win=curses.newwin(23,60,2,2)
                form_win.box()
                form_win.bkgd(curses.color_pair(4))
                header_win.clear()
                header_win.bkgd(curses.color_pair(4))
                header_win.addstr(0,3,f"Match Statistic between {self.events[selected].teamhome} VS {self.events[selected].teamaway}")
                footer_win.clear()
                footer_win.bkgd(curses.color_pair(4))
                footer_win.addstr(0,3,"PRESS 'q' to close")
                dataf=self.events[selected].list_statistic()
                tablef=self.tabulate_strings(dataf)
                for r,line in enumerate(tablef):
                    form_win.addstr(r+1,2,line)
                form_win.refresh()
                header_win.refresh()
                footer_win.refresh()
                while True:
                    pausekey=screen.getch() #fa una pausa
                    if pausekey==ord("q"):
                        form_win.erase()
                        screen.clear()
                        #screen.refresh()
                        break
            #richiesta previsioni betting e confronto
            elif (key == ord("p") and (self.events[selected].status == "NS")):
                header_win.clear()
                header_win.bkgd(curses.color_pair(5))
                header_win.addstr(0,3,f"prediction STAT: {self.events[selected].teamhome} VS {self.events[selected].teamaway}")
                header_win.refresh()
                footer_win.clear()
                footer_win.bkgd(curses.color_pair(5))
                footer_win.addstr(0,3,"PRESS 'q' to close - PRESS 'ARROW UP/DOWN' to scroll text")
                footer_win.refresh()
                pred_win=curses.newwin(15,width-2,2,2)
                pred_win.box()
                pred_win.bkgd(curses.color_pair(5))
                pred_win_x,pred_win_y=pred_win.getmaxyx()
                pred_win.addstr(1, 1, f"Analize Match...: {self.events[selected].teamhome} vs {self.events[selected].teamaway}")
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

                predizione=Prediction.gpt_call(tabclassifica,self.events[selected].teamhome,self.events[selected].teamaway,self.events[selected].odd)
                self.events[selected].analize=predizione
                predictiontext=self.giustifica_testo(predizione,pred_win_y-4)
                self.events[selected].pronostic=Prediction.compactOdds(predizione)
                #salva/aggiorna la predizione sul server
                upload_save_prediction(self.events[selected].idfixture,self.events[selected].pronostic,predizione)
                options=self.formatta_liste(self.events)

                altezza = min(len(predictiontext), pred_win_x - 2)
                start_index=0
                while True:
                    # Visualizza le righe correnti
                    for i in range(altezza):
                        if start_index + i < len(predictiontext):
                            pred_win.addstr(i + 1, 1, predictiontext[start_index + i][:width - 4])
                    pred_win.refresh()
                    # Attendi l'input dell'utente
                    tasto = screen.getch()

                    # Gestisci gli input delle frecce
                    if tasto == curses.KEY_UP:
                        start_index = max(0, start_index - 1)
                        pred_win.clear()
                        pred_win.box()
                    elif tasto == curses.KEY_DOWN:
                        start_index = min(len(predictiontext) - altezza, start_index + 1)
                        pred_win.clear()
                        pred_win.box()
                    elif tasto == ord('q'):  # Per uscire, premi 'q'
                        pred_win.erase()
                        screen.clear()
                        break
            #carica le quote per tutti gli eventi selezionati
            elif (key == ord("o") and (self.events[selected].status == "NS")):
                header_win.clear()
                header_win.bkgd(curses.color_pair(6))
                header_win.addstr(0, 5, f"Odds Loading...")
                header_win.refresh()
                odds_win=curses.newwin(3, width-2, 2, 2)
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
                tab_odds=get_match_odds(self.events[selected].idleague, datetime.date.today())
                for todds in tab_odds:
                    for ievents in range(len(self.events)):
                        if self.events[ievents].idfixture==todds.fixture.id:
                            self.events[ievents].odd=todds.odd
                            pl+=1
                            odds_win.clear()
                            odds_win.box()
                            odds_win.addstr(1, 2, f"LOADING ODDS... {pl}/{len(self.events)}")
                            odds_win.refresh()
                            #pause 1 second
                            time.sleep(1)
                            break
                odds_win.clear()
                odds_win.box()
                odds_win.addstr(1, 2, "LOADED!")
                odds_win.refresh()                                
                while True:
                    pausekey=screen.getch() #fa una pausa
                    if pausekey==ord("q"):
                        odds_win.erase()
                        screen.clear()
                        break
            #refresh option            
            elif (key == ord("r") and self.isLive(options)):
                menu_win.clear()
                return 1 #refresh code for now not used
            #read analized match if exist
            elif (key == ord("a") and (self.events[selected].analize != "")):
                header_win.clear()
                header_win.bkgd(curses.color_pair(7))
                header_win.addstr(0, 3, f"Analized Match between {self.events[selected].teamhome} VS {self.events[selected].teamaway}")
                header_win.refresh()
                footer_win.clear()
                footer_win.bkgd(curses.color_pair(7))
                footer_win.addstr(0, 3, "PRESS 'q' to close - PRESS 'ARROW UP/DOWN' to scroll text")
                footer_win.refresh()
                pred_win=curses.newwin(15,width-2,2,2)
                pred_win.box()
                pred_win.bkgd(curses.color_pair(10))
                pred_win_x,pred_win_y=pred_win.getmaxyx()
                pred_win.refresh()
                predictiontext=self.giustifica_testo(self.events[selected].analize,pred_win_y-4)
                #options=self.formatta_liste(self.events)

                altezza = min(len(predictiontext), pred_win_x - 2)
                start_index=0
                while True:
                    # Visualizza le righe correnti
                    for i in range(altezza):
                        if start_index + i < len(predictiontext):
                            pred_win.addstr(i + 1, 1, predictiontext[start_index + i][:width - 4])
                    pred_win.refresh()
                    # Attendi l'input dell'utente
                    tasto = screen.getch()

                    # Gestisci gli input delle frecce
                    if tasto == curses.KEY_UP:
                        start_index = max(0, start_index - 1)
                        pred_win.clear()
                        pred_win.box()
                    elif tasto == curses.KEY_DOWN:
                        start_index = min(len(predictiontext) - altezza, start_index + 1)
                        pred_win.clear()
                        pred_win.box()
                    elif tasto == ord('q'):  # Per uscire, premi 'q'
                        pred_win.erase()
                        screen.clear()
                        break
            #set exit point
            elif key == ord("q"):
                menu_win.erase()
                header_win.erase()
                footer_win.erase()
                screen.clear()
                screen.refresh()
                curses.endwin()

                return -1


if args.version:
    print(f"NowScore - version {version}")
    exit() #chiusura del programma dopo la visualizzazione della versione


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
        tabclassifica=tabulate(classifica,headers="firstrow",tablefmt="rounded_outline")
        print("\n Standing of "+scext[args.league.upper()]+" Championship update at: "+str(datetime.date.today())+" REM:"+str(rem)+"\n"
              +tabclassifica
              +"\n")
        #print(Prediction.gpt_call(tabulato+" analizza questa classifica"))
        exit()
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
                    print(f"NOWScore {version} richiesta di uscita dal programma!")
                    exit()
            except ValueError as error:
                print(f"errore {error}")
                key=input("non ci sono eventi da visualizzare...(press any key)")
                break

try:
    pass
except:
    print("non hai definito codice lega")





