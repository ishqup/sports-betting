from scipy.optimize import minimize
import pandas as pd
import numpy as np
import requests

def get_squared_error(params, ratings, home_team, away_team, score_margin):
    home_edge = params[-1]
    home_rating = ratings[home_team]
    away_rating = ratings[away_team]
    forecast = home_rating - away_rating + home_edge
    squared_error = (score_margin - forecast) ** 2
    return squared_error

def objective_function(params, *args):
    team_names = args[0]
    home_teams = args[1]
    away_teams = args[2]
    score_margins = args[3]
    ratings_array = params[:-1]
    ratings = dict(zip(team_names, ratings_array))
    squared_errors = [get_squared_error(params, ratings, home_teams[i], away_teams[i], score_margins[i]) for i in range(len(home_teams))]
    return sum(squared_errors)

def find_optimal_ratings(team_names, home_teams, away_teams, score_margins):
    num_teams = len(team_names)
    initial_params = [0] * (num_teams + 1)
    res = minimize(objective_function, initial_params, args=(team_names, home_teams, away_teams, score_margins))
    optimal_params = res.x
    optimal_ratings_array = optimal_params[:-1]
    optimal_ratings = dict(zip(team_names, optimal_ratings_array))
    optimal_home_edge = optimal_params[-1]
    return optimal_ratings, optimal_home_edge

def get_team_data(data, team_names):
    stats = []
    for team in team_names:
        W = 0
        L = 0
        GS = 0
        GA = 0
        for row in data.iterrows():
            if row[1][2] == 0 and row[1][4] == 0:
                pass
            else:
                if row[1][1] == team:
                    GS += row[1][2]
                    GA += row[1][4]
                    if row[1][2] > row[1][4]:
                        W += 1
                    else:
                        L += 1
                if row[1][3] == team:
                    GS += row[1][4]
                    GA += row[1][2]
                    if row[1][2] < row[1][4]:
                        W += 1
                    else:
                        L += 1
        team_data = [team, W, L, GS, GA]
        stats.append(team_data)
    df = pd.DataFrame(stats, columns=['Team','W','L','GS','GA'])
    return df


nhl_url = 'https://www.hockey-reference.com/leagues/NHL_2023_games.html'
page = requests.get(nhl_url)
nhl_data = pd.read_html(page.content, header=0)[0]
nhl_data = nhl_data[nhl_data['Date'] != 'Date'].iloc[:, :-4]
nhl_data.columns = ['Date','Away','Score2','Home','Score1']
home_teams = nhl_data['Home'].to_list()
away_teams = nhl_data['Away'].to_list()
score_margins = (nhl_data['Score1']-nhl_data['Score2']).to_list()
team_names = np.unique(np.array(home_teams))

optimal_ratings, optimal_home_edge = find_optimal_ratings(team_names, home_teams, away_teams, score_margins)
optimal_ratings = list(map(list, zip(*[list(optimal_ratings.keys()),list(optimal_ratings.values())])))
nhl_power_rankings = pd.DataFrame(optimal_ratings, columns=['Team','Rating'])
stats = get_team_data(nhl_data,team_names)
nhl_power_rankings = pd.merge(nhl_power_rankings, stats, on='Team')
nhl_power_rankings = nhl_power_rankings.sort_values(by='Rating', ascending=False).reset_index(drop=True)
nhl_power_rankings['Rank'] =nhl_power_rankings['Rating'].rank(ascending=False)
nhl_power_rankings = nhl_power_rankings.reindex(columns=['Team','W','L','Rating','Rank','GS','GA']).round(2)
print(f'Home Edge: {optimal_home_edge:.2f}')
print(nhl_power_rankings)
nhl_power_rankings.to_csv('nhl_power_rankings.csv', index=False)

while True:
    while True:
        find_spread = input('Calculate Spreads? (y/n) ')
        if find_spread == 'y' or find_spread == 'n':
            break
        else:
            print('Not a valid response. Try Again.')
    if find_spread == 'n':
        break

    while True:
        home = input('Home Team: ')
        if home in nhl_power_rankings['Team'].values:
            break
        else:
            print("Invalid team. Please try again.")

    while True:
        away = input('Home Team: ')
        if away in nhl_power_rankings['Team'].values:
            break
        else:
            print("Invalid team. Please try again.")

    home_rating = nhl_power_rankings.loc[nhl_power_rankings['Team'] == home]['Rating'].values[0]
    away_rating = nhl_power_rankings.loc[nhl_power_rankings['Team'] == away]['Rating'].values[0]
    print(f'{home} vs {away}: {optimal_home_edge + home_rating - away_rating:.2f}')
