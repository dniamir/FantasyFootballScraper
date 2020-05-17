import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import copy
from matplotlib.ticker import MaxNLocator


class LeagueSettings:

    def __init__(self):
        # League settings are set to the Yahoo Fantasy Football default scoring settings
        # This can be easily changed by the user

        self.passing_yards = 0.04 # points per yard
        self.passing_tds = 4
        self.interceptions = -1

        self.rushing_yards = 0.1 # points per yard
        self.rushing_tds = 6

        self.receptions = 0.5
        self.receiving_yards = 0.1 # points per yard
        self.receiving_tds = 6
        self.two_pt_conversions = 2
        self.fumbles_lost = -2
        self.offensive_fumble_return_tds = 6
        self.yards_40_plus = 0
        self.tds_40_plus = 0

        self.fg_20 = 3
        self.fg_30 = 3
        self.fg_40 = 3
        self.fg_50 = 4
        self.fg_50_plus = 5
        self.extra_point = 1


class PlayerProfile:

    def __init__(self, name):

        self.name = name
        self.player_id = None
        self.current_status = None
        self.years_played = None
        self.number = None
        self.position = None
        self.league_points = None

    def CalculatePlayerPoints(self, df_list, league_settings, include_post_season=False, remove_week17=True):

        first_name, last_name = self.name.split(' ', maxsplit=1)
        name_combo = '%s, %s' % (last_name.title(), first_name.title())

        # Find a dataframe with with the data of this player
        for df_single in df_list:
            name_check = name_combo.upper() in df_single['Name'].str.upper().values
            if name_check:
                break

        df = copy.copy(df_single)

        check1 = df['Name'].str.upper() == name_combo.upper()
        check2 = df['Season'] == 'Regular Season'
        check3 = df['Season'] == 'Postseason'
        check4 = df['Week'] != 17

        # Choose whether to include post-season results
        check_bool = check1
        if include_post_season:
            check_bool = check_bool & (check2 | check3)
        else:
            check_bool = check_bool & check2

        # Choose whether to include week 17
        if remove_week17:
            check_bool = check_bool & check4

        df_player = df[check_bool]

        # Replace dataframe empty cells with 0
        df_player.replace('--', 0, inplace=True)

        exception_cols = ['Longest Reception', 'Longest Rushing Run']
        years = np.unique(df_player['Year'])
        points_per_year = np.array([])

        for year in years:
            df_player_year = df_player[df_player['Year'] == year]
            df_player_year = df_player_year[list(df_player_year)[12:]]
            df_player_year.drop(labels=exception_cols, axis='columns', inplace=True, errors='ignore')
            df_player_year = df_player_year.astype(float)

            player_year_stats = df_player_year.sum()

            points = 0
            for key, value in league_settings.__dict__.items():
                try:
                    new_key = key.replace('_', ' ').title()
                    points += player_year_stats[new_key] * value
                except KeyError:
                    continue
            points_per_year = np.append(points_per_year, points)

        data = {'years': years, 'points': points_per_year}
        df_output = pd.DataFrame(data=data)

        self.league_points = df_output

    def __repr__(self):
        return "<Player: %s>" % self.name


class FFBAnalyzer:

    DLINE_FILENAME = 'Game_Logs_Defensive_Lineman.csv'
    OLINE_FILENAME = 'Game_Logs_Offensive_Line.csv'
    KICKERS_FILENAME = 'Game_Logs_Kickers.csv'
    PUNTERS_FILENAME = 'Game_Logs_Punters.csv'
    QUARTERBACKS_FILENAME = 'Game_Logs_Quarterback.csv'
    RUNNINGBACKS_FILENAME = 'Game_Logs_Runningback.csv'
    WIDE_RECEIVERS_FILENAME = 'Game_Logs_Wide_Receiver_and_Tight_End.csv'

    def __init__(self, filepath=None, league_settings=LeagueSettings()):

        self.players = []
        self.league_settings = league_settings

        self.df_dline = None
        self.df_oline = None
        self.df_k = None
        self.df_p = None
        self.df_qb = None
        self.df_rb = None
        self.df_wr = None

        if filepath is not None:
            self.LoadNflData(filepath)

    def LoadNflData(self, filepath='Data'):

        dline_path = os.path.join(filepath, self.DLINE_FILENAME)
        oline_path = os.path.join(filepath, self.OLINE_FILENAME)
        kickers_path = os.path.join(filepath, self.KICKERS_FILENAME)
        punters_path = os.path.join(filepath, self.PUNTERS_FILENAME)
        qb_path = os.path.join(filepath, self.QUARTERBACKS_FILENAME)
        rb_path = os.path.join(filepath, self.RUNNINGBACKS_FILENAME)
        wr_path = os.path.join(filepath, self.WIDE_RECEIVERS_FILENAME)

        self.df_dline = pd.read_csv(dline_path)
        self.df_oline = pd.read_csv(oline_path)
        self.df_k = pd.read_csv(kickers_path)
        self.df_p = pd.read_csv(punters_path)
        self.df_qb = pd.read_csv(qb_path)
        self.df_rb = pd.read_csv(rb_path)
        self.df_wr = pd.read_csv(wr_path)

        self.dl_list = [self.df_k,
                        self.df_p,
                        self.df_qb,
                        self.df_rb,
                        self.df_wr,
                        self.df_dline,
                        self.df_oline,]

    def UpdatePlayerScores(self):

        if self.players is not None:
            players_new = []
            for player in self.players:
                players_new = players_new + [player.CalculatePlayerPoints(self.dl_list)]
            self.players = players_new

    def ChangeLeagueSettings(self, new_league_settings):
        self.league_settings = new_league_settings
        self.UpdatePlayerScores()

    def AddPlayer(self, player_name):
        player = PlayerProfile(name=player_name)

        if self.dl_list is None:
            raise NameError('NFL data has not been loaded yet, try calling LoadNFLData')

        player.CalculatePlayerPoints(self.dl_list, league_settings=self.league_settings)
        self.players = self.players + [player]
        return player

    def AddPlayers(self, player_names):
        for player in players:
            self.AddPlayer(player)

    def PlotPlayerPoints(self, player_name_list=None):

        added_player_names = [player.name for player in self.players]
        player_names = added_player_names if player_name_list is None else player_name_list

        fig = plt.figure(figsize=(10, 5), facecolor='white')

        for player_name in player_names:

            # Search FantasyCompiled to see if player exists
            player = None
            for player in self.players:
                if player.name == player_name:
                    break
                else:
                    player = None

            if player is None:
                player = self.AddPlayer(player_name)

            years = player.league_points['years']
            points = player.league_points['points']

            plt.plot(years, points, marker='o', markersize=8, markeredgecolor='black', label=player.name)

        plt.grid(True)
        plt.xlabel('Year', fontsize=14)
        plt.ylabel('Points', fontsize=14)
        plt.title('Points Vs. Year in NFL', fontsize=18)
        plt.legend(loc='best')

        # Force tick marks to fall on integers
        ax = plt.gca()
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        plt.tight_layout()
        return fig
