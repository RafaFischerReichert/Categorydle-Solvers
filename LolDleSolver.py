from GameDleSolver import GameDleSolver
from typing import List, Tuple
import pandas as pd

class LolDleSolver(GameDleSolver):
    """
    LolDle solver implementation extending the abstract GameDleSolver base class.
    """
    
    def __init__(self, csv_file="LolDle.csv", target_column="Champion"):
        """Initialize the LolDle solver with the LolDle.csv file"""
        super().__init__(csv_file, target_column)
        self.data = pd.read_csv(csv_file, header=0, na_values=[], keep_default_na=False)
    
    def _define_category_types(self):
        """Define the different types of categories for LolDle"""
        # Categories that can have partial matches (comma-separated values)
        self.partial_matchable = ["Roles", "Species", "Regions", "Range"]
        
        # Categories that are exact match or not
        self.yes_or_no = ["Gender", "Resource"]
        
        # Categories that can be compared (before/after/correct)
        self.orderable = ["Release Year"]
    
    def get_category_config(self) -> List[Tuple[str, List[str]]]:
        """Return the configuration for user input categories"""
        return [
            ('gender', ['correct', 'incorrect']),
            ('roles', ['correct', 'partial', 'incorrect']),
            ('species', ['correct', 'partial', 'incorrect']),
            ('resource', ['correct', 'incorrect']),
            ('range', ['correct', 'partial', 'incorrect']),
            ('regions', ['correct', 'partial', 'incorrect']),
            ('release_year', ['lower', 'higher', 'correct'])
        ]
    
    def get_display_name(self) -> str:
        """Return the display name for this game"""
        return "LolDle"

if __name__ == "__main__":
    # Run discovery mode
    solver = LolDleSolver()
    solver.discovery_mode() 