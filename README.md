# nowscore-cli

# Football Results Viewer (Command Line Interface)

This is a command line interface (CLI) application for accessing and viewing football match results in the major European and international leagues. The application requires a Rapid Api key to be installed in a file named `rapidkey1.key` in order to access the service.

## Installation

To use this CLI application, you will need to obtain a Rapid Api key and install it in a file named `rapidkey1.key`. Insert the token on the first line of the file.

## Usage

You can use the following options to interact with the application:

- `-h, --help`: Show help message and exit
- `-l LEAGUE, --league LEAGUE`: Show league options (e.g., Italy Serie A=SA, England Premier League=PL, Germany Bundesliga=BL, etc.)
- `-v, --version`: Print version of the program and exit
- `-s [{0,1,2,3,4,5,6,7}], --standing [{0,1,2,3,4,5,6,7}]`: Show standing of selected league or tournament group
- `-t TIME_DELTA, --time_delta TIME_DELTA`: Set time range to show fixtures by day (e.g., t=-3 for fixtures starting 3 days ago, t=7 for fixtures up to 7 days from today)

## Examples of Usage

1. Show current results of the Premier League:
   
   ```bash
   nowscore-cli -l pl
   ```

2. Show the standings of the Spanish La Liga:
   
   ```bash
   nowscore-cli -l liga -s
   ```

3. Show all matches in the Premier League from today to 30 days ahead:
   
   ```bash
   nowscore-cli -l pl -t=30
   ```

4. Show all matches in the UEFA Europa League from the past week:
   
   ```
   nowscore-cli -l uel -t=-7
   ```

5. Show standing of single season of Uefa Champions League

6. ```bash
   nowscore-cli -l ucl -s 0 "season A" 1 "season B" 2 "season C"...
   ```

## Supported League Codes

You can use the following league codes to access information for the desired football leagues using the application:

| Code | League                 |
| ---- | ---------------------- |
| SA   | Italy Serie A          |
| PL   | England Premier League |
| BL   | Germany Bundesliga     |
| LIGA | Spain La Liga          |
| L1   | France Ligue 1         |
| ER   | Netherlands Eredivisie |
| SL   | Turkey Süper Lig       |
| PPL  | Portugal Primeira Liga |
| UCL  | UEFA Champions League  |
| UEL  | UEFA Europa League     |
| SB   | Italy Serie B          |

Use these codes to view results, standings, and fixtures for your desired football leagues.

We hope this table helps you effectively utilize the application!

## Support

For any issues or questions, please contact our support team at aniello@discala.org

We hope you find the Football Results Viewer CLI app useful for staying updated on the latest football action!
