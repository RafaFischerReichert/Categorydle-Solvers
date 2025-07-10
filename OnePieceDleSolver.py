from GameDleSolver import GameDleSolver
from typing import List, Tuple, Dict
import pandas as pd
import re

class OnePieceDleSolver(GameDleSolver):
    def __init__(self):
        super().__init__("OnePieceDle.csv", "Character")
    
    def _define_category_types(self):
        # Define which categories can have partial matches
        self.partial_matchable = ["Haki"]
        
        # Define which categories are exact match only
        self.yes_or_no = ["Genre", "Fruit", "Affiliation", "Origin"]
        
        # Define which categories can be compared (before/after/correct)
        self.orderable = ["Bounty", "Height", "Debut Arc"]
    
    def get_category_config(self) -> List[Tuple[str, List[str]]]:
        return [
            ('genre', ['correct', 'incorrect']),
            ('affiliation', ['correct', 'incorrect']),
            ('fruit', ['correct', 'incorrect']),
            ('haki', ['correct', 'partial', 'incorrect']),
            ('bounty', ['lower', 'higher', 'correct']),
            ('height', ['lower', 'higher', 'correct']),
            ('origin', ['correct', 'incorrect']),
            ('debut arc', ['lower', 'higher', 'correct'])
        ]
    
    def get_display_name(self) -> str:
        return "OnePieceDle"
    
    def _extract_arc_number(self, arc_string: str) -> int:
        """Extract the numeric prefix from arc string (e.g., '01. Romance Dawn' -> 1)"""
        if pd.isna(arc_string) or not isinstance(arc_string, str):
            return 0
        match = re.match(r'(\d+)\.', arc_string)
        return int(match.group(1)) if match else 0
    
    def _apply_orderable_filters(self, guessed_target: pd.Series, feedback: Dict[str, str]):
        """Apply filters for orderable categories with special handling for Debut Arc"""
        for category in self.orderable:
            feedback_key = category.lower()
            column_name = category
            if feedback_key in feedback:
                if column_name not in self.possible_targets.columns:
                    continue
                guessed_value = guessed_target[column_name]
                
                if category == "Debut Arc":
                    # Special handling for Debut Arc - compare numeric prefixes
                    guessed_arc_num = self._extract_arc_number(str(guessed_value))
                    
                    if feedback[feedback_key] == 'lower':
                        self.possible_targets = self.possible_targets[
                            self.possible_targets[column_name].apply(
                                lambda x: self._extract_arc_number(x) < guessed_arc_num
                            )
                        ]
                    elif feedback[feedback_key] == 'higher':
                        self.possible_targets = self.possible_targets[
                            self.possible_targets[column_name].apply(
                                lambda x: self._extract_arc_number(x) > guessed_arc_num
                            )
                        ]
                    elif feedback[feedback_key] == 'correct':
                        self.possible_targets = self.possible_targets[self.possible_targets[column_name] == guessed_value]
                else:
                    if feedback[feedback_key] == 'lower':
                        self.possible_targets = self.possible_targets[self.possible_targets[column_name] < guessed_value]
                    elif feedback[feedback_key] == 'higher':
                        self.possible_targets = self.possible_targets[self.possible_targets[column_name] > guessed_value]
                    elif feedback[feedback_key] == 'correct':
                        self.possible_targets = self.possible_targets[self.possible_targets[column_name] == guessed_value]
    
    def _simulate_feedback(self, guess_target: str, target: str) -> Dict[str, str]:
        """Simulate what feedback would be given for a guess against a target"""
        guess_data = self.data[self.data[self.target_column] == guess_target].iloc[0]
        target_data = self.data[self.data[self.target_column] == target].iloc[0]
        
        feedback = {}
        
        # Target name
        feedback[self.target_column.lower()] = 'correct' if guess_target == target else 'incorrect'
        
        # Yes/No categories
        for category in self.yes_or_no:
            feedback[category.lower()] = 'correct' if guess_data[category] == target_data[category] else 'incorrect'
        
        # Orderable categories
        for category in self.orderable:
            if category == "Debut Arc":
                # Special handling for Debut Arc - compare numeric prefixes
                guess_arc_num = self._extract_arc_number(guess_data[category])
                target_arc_num = self._extract_arc_number(target_data[category])
                
                if guess_arc_num < target_arc_num:
                    feedback[category.lower()] = 'higher'
                elif guess_arc_num > target_arc_num:
                    feedback[category.lower()] = 'lower'
                else:
                    feedback[category.lower()] = 'correct'
            else:
                # Corrected logic: compare target to guess
                if target_data[category] < guess_data[category]:
                    feedback[category.lower()] = 'lower'
                elif target_data[category] > guess_data[category]:
                    feedback[category.lower()] = 'higher'
                else:
                    feedback[category.lower()] = 'correct'
        
        # Partial matchable categories
        for category in self.partial_matchable:
            guess_value = guess_data[category]
            target_value = target_data[category]
            
            if ',' in str(guess_value) or ',' in str(target_value):
                guess_values = set(val.strip() for val in str(guess_value).split(','))
                target_values = set(val.strip() for val in str(target_value).split(','))
                
                if guess_values == target_values:
                    feedback[category.lower()] = 'correct'
                elif guess_values & target_values:
                    feedback[category.lower()] = 'partial'
                else:
                    feedback[category.lower()] = 'incorrect'
            else:
                if guess_value == target_value:
                    feedback[category.lower()] = 'correct'
                else:
                    feedback[category.lower()] = 'incorrect'
        
        return feedback

if __name__ == "__main__":
    solver = OnePieceDleSolver()
    solver.discovery_mode()