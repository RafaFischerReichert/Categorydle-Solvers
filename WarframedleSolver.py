from GameDleSolver import GameDleSolver
from typing import List, Tuple

class Warframedle(GameDleSolver):
    def __init__(self):
        super().__init__("Warframedle.csv", "Frame")
        self.preprocess_data()
    
    def preprocess_data(self):
        """Modify the Release field to only use the first four characters (year)."""
        if "Release" in self.data.columns:
            self.data["Release"] = self.data["Release"].astype(str).str[:4]
    
    def _define_category_types(self):
        # Define which categories can have partial matches
        self.partial_matchable = ["Roles"]
        
        # Define which categories are exact match only
        self.yes_or_no = ["Gender", "Progenitor", "Prime", "Exalted", "Protoframe"]
        
        # Define which categories can be compared (before/after/correct)
        self.orderable = ["Release"]
    
    def get_category_config(self) -> List[Tuple[str, List[str]]]:
        return [
            ('gender', ['correct', 'incorrect']),
            ('progenitor', ['correct', 'incorrect']),
            ('prime', ['correct', 'incorrect']),
            ('exalted', ['correct', 'incorrect']),
            ('roles', ['correct', 'partial', 'incorrect']),
            ('protoframe', ['correct', 'incorrect']),
            ('release', ['lower', 'higher', 'correct'])
        ]
    
    def get_display_name(self) -> str:
        return "Warframedle"

if __name__ == "__main__":
    solver = Warframedle()
    solver.discovery_mode()