#!/usr/bin/python 


import sys, gc

#Append the parent dir to the module search path
sys.path.append('..')
import AUDLclasses

def load_team_test():
    """
    Tests that the method add_teams can find a single team in the test file 
    and create an instance for it.
    """
    test_league = AUDLclasses.League()
    test_league.add_teams('single_team_info', games = False, players = False, stats = False)
    assert 1 == len(test_league.Teams)

def load_teams_test():
    """
    Tests that the method add_teams can find multiple teams in the test file 
    and create an instance for it.
    """
    test_league = AUDLclasses.League()
    test_league.add_teams('multiple_teams_info', games = False, players = False, stats = False)
    assert 2 == len(test_league.Teams)
    
    
def load_all_team_data_test():
    """
    Tests that the method add_teams can find a single team in the test file, create an
    instance of the team class, and populate its players and their statistics.
    """
    test_league = AUDLclasses.League()
    test_league.add_teams('single_team_info', games= False)
    assert 1 == len(test_league.Teams)


def test_game_merge():
    """
    Creates two team instances that share a game in the same file.
    Upon loading games from this file for both teams,
    there should be only one game in the Python instance 
    if game merging is working properly.
    """

    test_league = AUDLclasses.League()
    test_league.add_teams('multiple_teams_info', games = False, players = False, stats = False)
    
    for team in test_league.Teams:
        test_league.Teams[team].add_games('test_game_data.json')

    num_of_game_classes = 0 
   
    for obj in gc.get_objects():
        if isinstance(obj, AUDLclasses.Game):
            num_of_game_classes+=1

    assert 1 == num_of_game_classes
