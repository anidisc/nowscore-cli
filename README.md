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
   
   ```
   nowscore -l pl
   ```

2. Show the standings of the Spanish La Liga:
   
   ```
   nowscore -l liga -s
   ```

3. Show all matches in the Premier League from today to 30 days ahead:
   
   ```
   nowscore -l pl -t=30
   ```

## Support

For any issues or questions, please contact our support team at aniello@discala.org

We hope you find the Football Results Viewer CLI app useful for staying updated on the latest football action!
