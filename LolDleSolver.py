from GameDleSolver import GameDleSolver
from typing import List, Tuple, Dict, Set
import pandas as pd

def normalize_range_value(value: str) -> str:
    """
    Normalize range values to handle the special case where "Both" is equivalent to "Melee, Ranged".
    
    Args:
        value (str): The range value to normalize
        
    Returns:
        str: The normalized value
    """
    if value == "Both":
        return "Melee, Ranged"
    return value

def normalize_range_values_for_comparison(value: str) -> Set[str]:
    """
    Normalize range values and split into a set for comparison.
    
    Args:
        value (str): The range value to normalize and split
        
    Returns:
        set: Set of normalized range values
    """
    normalized = normalize_range_value(value)
    if ',' in normalized:
        return set(val.strip() for val in normalized.split(','))
    else:
        return {normalized}

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
        return "Loldle"
    
    def _apply_partial_matchable_filters(self, guessed_target: pd.Series, feedback: Dict[str, str]):
        """Apply filters for partial matchable categories with special handling for Range field"""
        for category in self.partial_matchable:
            feedback_key = category.lower()
            column_name = category
            if feedback_key in feedback:
                if column_name not in self.possible_targets.columns:
                    continue
                guessed_value = guessed_target[column_name]
                
                # Special handling for Range field
                if category == "Range":
                    if feedback[feedback_key] == 'correct':
                        # Keep only exact matches (considering "Both" normalization)
                        guessed_values = normalize_range_values_for_comparison(guessed_value)
                        self.possible_targets = self.possible_targets[
                            self.possible_targets[column_name].apply(
                                lambda x: normalize_range_values_for_comparison(x) == guessed_values
                            )
                        ]
                    
                    elif feedback[feedback_key] == 'incorrect':
                        # Remove all partial and complete matches
                        guessed_values = normalize_range_values_for_comparison(guessed_value)
                        self.possible_targets = self.possible_targets[
                            ~self.possible_targets[column_name].apply(
                                lambda x: bool(normalize_range_values_for_comparison(x) & guessed_values)
                            )
                        ]
                    
                    elif feedback[feedback_key] == 'partial':
                        # Remove exact matches and remove targets where no value matches
                        guessed_values = normalize_range_values_for_comparison(guessed_value)
                        self.possible_targets = self.possible_targets[
                            self.possible_targets[column_name].apply(
                                lambda x: normalize_range_values_for_comparison(x) != guessed_values and 
                                        bool(normalize_range_values_for_comparison(x) & guessed_values)
                            )
                        ]
                else:
                    # Original logic for other partial matchable categories
                    if feedback[feedback_key] == 'correct':
                        # Keep only exact matches
                        self.possible_targets = self.possible_targets[self.possible_targets[column_name] == guessed_value]
                    
                    elif feedback[feedback_key] == 'incorrect':
                        # Remove all partial and complete matches
                        if ',' in str(guessed_value):
                            guessed_values = set(val.strip() for val in str(guessed_value).split(','))
                            self.possible_targets = self.possible_targets[
                                ~self.possible_targets[column_name].apply(
                                    lambda x: bool(set(val.strip() for val in str(x).split(',')) & guessed_values)
                                )
                            ]
                        else:
                            self.possible_targets = self.possible_targets[self.possible_targets[column_name] != guessed_value]
                    
                    elif feedback[feedback_key] == 'partial':
                        # Remove exact matches and remove targets where no value matches
                        if ',' in str(guessed_value):
                            guessed_values = set(val.strip() for val in str(guessed_value).split(','))
                            self.possible_targets = self.possible_targets[
                                self.possible_targets[column_name].apply(
                                    lambda x: x != guessed_value and bool(set(val.strip() for val in str(x).split(',')) & guessed_values)
                                )
                            ]
                        else:
                            # For single values, partial is not possible, so treat as incorrect
                            self.possible_targets = self.possible_targets[self.possible_targets[column_name] != guessed_value]
    
    def _simulate_feedback(self, guess_target: str, target: str) -> Dict[str, str]:
        """Simulate what feedback would be given for a guess against a target with special Range handling"""
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
            
            # Special handling for Range field
            if category == "Range":
                guess_values = normalize_range_values_for_comparison(guess_value)
                target_values = normalize_range_values_for_comparison(target_value)
                
                if guess_values == target_values:
                    feedback[category.lower()] = 'correct'
                elif guess_values & target_values:
                    feedback[category.lower()] = 'partial'
                else:
                    feedback[category.lower()] = 'incorrect'
            else:
                # Original logic for other partial matchable categories
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
    
    def _target_compatible_with_feedback(self, target: str, guess_target: str, feedback: Dict[str, str]) -> bool:
        """Check if a target is compatible with given feedback with special Range handling"""
        target_data = self.data[self.data[self.target_column] == target].iloc[0]
        guess_data = self.data[self.data[self.target_column] == guess_target].iloc[0]
        
        # Check target name feedback
        if feedback.get(self.target_column.lower()) == 'correct':
            return target == guess_target
        elif feedback.get(self.target_column.lower()) == 'incorrect':
            if target == guess_target:
                return False
        
        # Check yes/no categories
        for category in self.yes_or_no:
            feedback_key = category.lower()
            if feedback_key in feedback:
                if feedback[feedback_key] == 'correct':
                    if target_data[category] != guess_data[category]:
                        return False
                elif feedback[feedback_key] == 'incorrect':
                    if target_data[category] == guess_data[category]:
                        return False
        
        # Check orderable categories
        for category in self.orderable:
            feedback_key = category.lower()
            if feedback_key in feedback:
                if feedback[feedback_key] == 'lower':
                    if target_data[category] >= guess_data[category]:
                        return False
                elif feedback[feedback_key] == 'higher':
                    if target_data[category] <= guess_data[category]:
                        return False
                elif feedback[feedback_key] == 'correct':
                    if target_data[category] != guess_data[category]:
                        return False
        
        # Check partial matchable categories
        for category in self.partial_matchable:
            feedback_key = category.lower()
            if feedback_key in feedback:
                target_value = target_data[category]
                guess_value = guess_data[category]
                
                # Special handling for Range field
                if category == "Range":
                    target_values = normalize_range_values_for_comparison(target_value)
                    guess_values = normalize_range_values_for_comparison(guess_value)
                    
                    if feedback[feedback_key] == 'correct':
                        if target_values != guess_values:
                            return False
                    elif feedback[feedback_key] == 'incorrect':
                        if target_values & guess_values:
                            return False
                    elif feedback[feedback_key] == 'partial':
                        overlap = target_values & guess_values
                        if not overlap or target_values == guess_values:
                            return False
                else:
                    # Original logic for other partial matchable categories
                    if feedback[feedback_key] == 'correct':
                        if target_value != guess_value:
                            return False
                    elif feedback[feedback_key] == 'incorrect':
                        if ',' in str(target_value) and ',' in str(guess_value):
                            target_values = set(val.strip() for val in str(target_value).split(','))
                            guess_values = set(val.strip() for val in str(guess_value).split(','))
                            if target_values & guess_values:
                                return False
                        elif target_value == guess_value:
                            return False
                    elif feedback[feedback_key] == 'partial':
                        if ',' in str(target_value) and ',' in str(guess_value):
                            target_values = set(val.strip() for val in str(target_value).split(','))
                            guess_values = set(val.strip() for val in str(guess_value).split(','))
                            overlap = target_values & guess_values
                            if not overlap or target_values == guess_values:
                                return False
                        else:
                            return False
        
        return True

if __name__ == "__main__":
    # Run discovery mode
    solver = LolDleSolver()
    solver.discovery_mode() 