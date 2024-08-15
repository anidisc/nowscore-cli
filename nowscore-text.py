"""
    New developement of application from curses to APP Textualize
    to start from the version of nowscore-cli 0.47b

"""
VERSION="0.1T"  # canonic version of the application in textualize
CURRENT_SEASON="2023" # current season of the application
APIFOOTBALL_KEYFILE="rapidkey1.key" # file with the api key for the api-football

from textual.app import App,ComposeResult
from textual.widgets import Header,Footer,Button,Static,Input,Tree
from textual import events
from textual import log
from textual.containers import ScrollableContainer

import requests
import json
import datetime
from datetime import datetime as dateT



#define class whit my RapidApi function required
class Apifootball():
    def __init__(self) -> None:
        #read the api key from the file
        with open(APIFOOTBALL_KEYFILE,"r") as f:
            self.api_key=str(f.readline().strip())
        #set the current season
        self.season=CURRENT_SEASON
        self.tz="Europe/Rome"

    def get_events_match(id):
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/events"

        querystring = {"fixture":id}

        headers = {
            "X-RapidAPI-Key": APIFOOTBALL_KEYFILE,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)
        tab=json.loads(response.text)
        return tab["response"]

    #scarica dalla api la lista delle partite nell'intervallo di tempo fissato dagli argomenti
    def get_match_list(idleague,datestart=datetime.date.today(),datestop=datetime.date.today()):
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"

        querystring = {"league": idleague,
                    "season":CURRENT_SEASON,
                    #"timezone":tz,
                    "from":datestart,
                    "to":datestop}
        headers = {
            "X-RapidAPI-Key": APIFOOTBALL_KEYFILE,
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

        querystring = {"season":CURRENT_SEASON,
                    "league":id}

        headers = {
            "X-RapidAPI-Key": APIFOOTBALL_KEYFILE,
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
            "X-RapidAPI-Key": APIFOOTBALL_KEYFILE,
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
            "X-RapidAPI-Key": APIFOOTBALL_KEYFILE,
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
            "X-RapidAPI-Key": APIFOOTBALL_KEYFILE,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        response = requests.get(url, headers=headers, params=querystring)


        remaining_calls = response.headers.get("X-RateLimit-Requests-Remaining")

        tab=json.loads(response.text)
        return tab["response"],remaining_calls

class Match(Apifootball):
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
        list_event=self.get_events_match(self.idfixture)
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
        f1,f2=self.get_start_11(self.idfixture)
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
        f1,f2=self.get_statistic(self.idfixture)
        list_stat=[["Statistic Date","|",self.teamhome,self.teamaway,":",self.goalshome,self.goalsaway],
                   ["--","|","--","--","","",""]]
        for i1,i2 in zip(f1,f2):
            list_stat.append([i1.type,"|",i1.value,i2.value])
        return list_stat


class NowScoreApp(App):

    #tree on sidebar item
    tree: Tree[dict] = Tree("NowScore Panel Championship", name="tree1",id="tree1")
    tree.root.expand()
    italychamp = tree.root.add("Italy", expand=True)
    italychamp.add_leaf("Serie A")
    italychamp.add_leaf("Serie B")
    italychamp.add_leaf("Serie C")
    italychamp.add_leaf("Coppa Italia")
    italychamp.add_leaf("Supercoppa Italiana")
    #scrivi un tree per le competizioni europee in formato dict
    europe=tree.root.add("Europe",expand=True)
    europe.add_leaf("Champions League")
    europe.add_leaf("Europa League")
    europe.add_leaf("SuperCup")
    #scrivi un tree per le competizioni internazionali in formato dict
    world=tree.root.add("World",expand=True)
    world.add_leaf("World Cup")
    world.add_leaf("Confederation Cup")
    world.add_leaf("Olympic Games")
    world.add_leaf("UEFA Nations League")

    BINDINGS=[("q", "quit","Quit the application"),
              ("i", "input","Show/Hide the input widget"),
              ("c","sidebarcontainer","Show/Hide the sidebar tree")]
           
    CSS="""
        Screen {
        align: center middle;
        layers: below above above2;
        }
        #header1 {
            color: red;
        }
        #input1 {
            layer: above;
            color: white;
            background: black;
            align: center middle;
            margin: 1;
            width: 80%;
            border: blue;
            
        }
        #wallpaper {
            color: blue;
            margin: 1;
            layer: below;
        }
        #sidebar {
            dock: left;
            background: $boost;
            color: white;
            width: 35%;
            height: 100%;
            layer: above2;
            margin:1;
            
        }
        #static2 {
            color: red;
            margin: 1;
        }

    """
    ascii_art = """

  ░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓███████▓▒░░▒▓██████▓▒░ ░▒▓██████▓▒░░▒▓███████▓▒░░▒▓████████▓▒░ 
  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓██████▓▒░   
  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
  ░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░ ░▒▓█████████████▓▒░░▒▓███████▓▒░ ░▒▓██████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░ 
                                                                                                                   
                                                                                                                                
                                ░▒▓████████▓▒░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░                                            
                                    ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░                                                
                                    ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░                                                
                                    ░▒▓█▓▒░   ░▒▓██████▓▒░  ░▒▓██████▓▒░   ░▒▓█▓▒░                                                
                                    ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░                                                
                                    ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░                                                
                                    ░▒▓█▓▒░   ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░                                                
                                                                                                                                
                                                                                                                   


"""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.title="NowScoreTEXT"
        self.sub_title=f"Welcome to NowScore {VERSION}"
   


    def compose(self) -> ComposeResult:
        yield Header(show_clock=True,name="h1",id="header1")
        self.wallpaper= Static(self.ascii_art,name="wallpaper",id="wallpaper")
        yield self.wallpaper
        self.input1=Input(placeholder="input command",name="input1",id="input1")
        yield self.input1
        self.static2=Static("This is a static widget",name="static2",id="static2")
        yield self.static2
        self.sidebar=ScrollableContainer(self.tree,name="sidebar",id="sidebar")
        yield self.sidebar
        yield Footer()

    def on_mount(self):
        self.title="NowScoreTEXT"
        self.sub_title=f"Welcome to NowScore {VERSION}"
        self.input1.styles.visibility="hidden"
        self.sidebar.styles.visibility="hidden"
        
    def action_input(self) -> None:
        if self.input1.styles.visibility=="visible":
            self.input1.styles.visibility="hidden"
            self.input1.disabled=True
        else:
            self.input1.styles.visibility="visible"
            self.input1.disabled=False
            self.input1.focus()

    def action_sidebarcontainer(self) -> None:
        if self.sidebar.styles.visibility=="visible":
            self.sidebar.styles.visibility="hidden"
        else:
            self.sidebar.styles.visibility="visible"     
            #focus on container scroll
            self.tree.focus()

    def on_input_submitted(self,event: Input.Submitted):
        # Aggiorna il widget statico con il testo dell'input
        self.static2.update(event.value)
        self.input1.styles.visibility="hidden"
        self.input1.value=""
        self.input1.disabled=True

       
            



    

if __name__ == "__main__":
    app=NowScoreApp()
    app.run()


