import pandas as pd
import math
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple

class GameDleSolver(ABC):
    """
    Abstract base class for game-dle solvers.
    Extend this class to create solvers for different games.
    """
    
    def __init__(self, csv_file: str, target_column: str):
        """
        Initialize the solver with game data.
        
        Args:
            csv_file (str): Path to the CSV file containing game data
            target_column (str): Name of the column containing the target items to guess
        """
        self.data = pd.read_csv(csv_file, header=0, na_values=[], keep_default_na=False)
        self.target_column = target_column
        self.possible_targets = self.data.copy()
        self.entropy_cache = {}
        
        # Validate that target column exists
        if target_column not in self.data.columns:
            raise ValueError(f"Target column '{target_column}' not found in CSV. Available columns: {self.data.columns.tolist()}")
        
        # Define category types based on the CSV structure
        self._define_category_types()
    
    @abstractmethod
    def _define_category_types(self):
        """
        Define the different types of categories in your game.
        Override this method in subclasses to specify:
        - partial_matchable: Categories that can have partial matches (comma-separated values)
        - yes_or_no: Categories that are exact match or not
        - orderable: Categories that can be compared (before/after/correct)
        """
        pass
    
    @abstractmethod
    def get_category_config(self) -> List[Tuple[str, List[str]]]:
        """
        Return the configuration for user input categories.
        Override this method to define what categories to ask for and their valid options.
        
        Returns:
            List of tuples: (category_name, [valid_options])
        """
        pass
    
    @abstractmethod
    def get_display_name(self) -> str:
        """
        Return the display name for this game.
        Override this method to return the game name (e.g., "LolDle", "PokéDle", etc.)
        """
        pass
    
    def reset(self):
        """Reset the solver to consider all targets"""
        self.possible_targets = self.data.copy()
        self.entropy_cache.clear()
    
    def apply_guess(self, target_name: str, feedback: Dict[str, str]):
        """
        Apply feedback from a guess to narrow down possible targets.
        
        Args:
            target_name (str): The target that was guessed
            feedback (dict): Dictionary with feedback for each category
        """
        guessed_target = self.data[self.data[self.target_column] == target_name].iloc[0]
        
        # Filter based on target name
        if feedback.get(self.target_column.lower()) == 'correct':
            self.possible_targets = self.possible_targets[self.possible_targets[self.target_column] == target_name]
            self.entropy_cache.clear()
            return
        
        # Remove the target column from feedback to avoid KeyError in filters
        filtered_feedback = {k: v for k, v in feedback.items() if k != self.target_column.lower()}
        
        # Apply filters based on category types
        self._apply_yes_or_no_filters(guessed_target, filtered_feedback)
        self._apply_orderable_filters(guessed_target, filtered_feedback)
        self._apply_partial_matchable_filters(guessed_target, filtered_feedback)
        
        # Clear cache since the game state has changed
        self.entropy_cache.clear()
    
    def _apply_yes_or_no_filters(self, guessed_target: pd.Series, feedback: Dict[str, str]):
        """Apply filters for yes/no categories"""
        for category in self.yes_or_no:
            feedback_key = category.lower()
            column_name = category
            if feedback_key in feedback:
                if column_name not in self.possible_targets.columns:
                    continue
                if feedback[feedback_key] == 'correct':
                    self.possible_targets = self.possible_targets[self.possible_targets[column_name] == guessed_target[column_name]]
                elif feedback[feedback_key] == 'incorrect':
                    self.possible_targets = self.possible_targets[self.possible_targets[column_name] != guessed_target[column_name]]
    
    def _apply_orderable_filters(self, guessed_target: pd.Series, feedback: Dict[str, str]):
        """Apply filters for orderable categories"""
        for category in self.orderable:
            feedback_key = category.lower()
            column_name = category
            if feedback_key in feedback:
                if column_name not in self.possible_targets.columns:
                    continue
                if feedback[feedback_key] == 'lower':
                    self.possible_targets = self.possible_targets[self.possible_targets[column_name] < guessed_target[column_name]]
                elif feedback[feedback_key] == 'higher':
                    self.possible_targets = self.possible_targets[self.possible_targets[column_name] > guessed_target[column_name]]
                elif feedback[feedback_key] == 'correct':
                    self.possible_targets = self.possible_targets[self.possible_targets[column_name] == guessed_target[column_name]]
    
    def _apply_partial_matchable_filters(self, guessed_target: pd.Series, feedback: Dict[str, str]):
        """Apply filters for partial matchable categories"""
        for category in self.partial_matchable:
            feedback_key = category.lower()
            column_name = category
            if feedback_key in feedback:
                if column_name not in self.possible_targets.columns:
                    continue
                guessed_value = guessed_target[column_name]
                
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
    
    def get_possible_targets(self) -> List[str]:
        """Get the list of remaining possible targets"""
        return self.possible_targets[self.target_column].tolist()
    
    def get_target_count(self) -> int:
        """Get the number of remaining possible targets"""
        return len(self.possible_targets)
    
    def calculate_entropy(self, probabilities: List[float]) -> float:
        """Calculate entropy given a list of probabilities"""
        entropy = 0
        for p in probabilities:
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy
    
    def _get_cache_key(self, guess_target: str) -> Tuple[str, Tuple[str, ...]]:
        """Generate a cache key for a specific guess and current game state"""
        possible_targets_tuple = tuple(sorted(self.possible_targets[self.target_column].tolist()))
        return (guess_target, possible_targets_tuple)
    
    def get_optimal_guess(self) -> Optional[str]:
        """
        Find the optimal guess by minimizing expected entropy.
        Returns the target that would provide the most information gain.
        """
        if len(self.possible_targets) <= 1:
            return self.possible_targets[self.target_column].iloc[0] if len(self.possible_targets) == 1 else None
        
        all_targets = self.data[self.target_column].tolist()
        best_guess = None
        best_expected_entropy = float('inf')
        
        for guess_target in all_targets:
            cache_key = self._get_cache_key(guess_target)
            if cache_key in self.entropy_cache:
                expected_entropy = self.entropy_cache[cache_key]
            else:
                expected_entropy = self._calculate_expected_entropy(guess_target)
                self.entropy_cache[cache_key] = expected_entropy
            
            if expected_entropy < best_expected_entropy:
                best_expected_entropy = expected_entropy
                best_guess = guess_target
        
        return best_guess
    
    def _calculate_expected_entropy(self, guess_target: str) -> float:
        """Calculate the expected entropy for a specific guess"""
        expected_entropy = 0
        total_outcomes = 0
        
        for target in self.possible_targets[self.target_column]:
            feedback = self._simulate_feedback(guess_target, target)
            
            # Create a temporary solver instance with the same data
            temp_solver = self.__class__()
            temp_solver.data = self.data
            temp_solver.target_column = self.target_column
            temp_solver.possible_targets = self.possible_targets.copy()
            temp_solver._define_category_types()  # Re-define category types
            temp_solver.apply_guess(guess_target, feedback)
            
            remaining_count = temp_solver.get_target_count()
            if remaining_count > 0:
                p = remaining_count / len(self.possible_targets)
                expected_entropy += p * math.log2(remaining_count)
                total_outcomes += 1
        
        if total_outcomes > 0:
            expected_entropy /= total_outcomes
        
        return expected_entropy
    
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
    
    def get_target_info(self, target_name: str) -> Dict[str, Any]:
        """Get information about a specific target"""
        target_data = self.data[self.data[self.target_column] == target_name]
        if target_data.empty:
            return {}
        
        info = {}
        for column in self.data.columns:
            if column != self.target_column:
                info[column] = target_data[column].iloc[0]
        
        return info
    
    def discovery_mode(self):
        """Run discovery mode to help find the correct answer through optimal guessing"""
        print(f"=== {self.get_display_name()} Discovery Mode ===")
        print("This mode helps you find the correct answer by making optimal guesses.")
        print("Play the actual game and input the feedback you receive.")
        print("I'll suggest the best guesses to minimize the number of attempts needed!")
        
        self.reset()
        guess_count = 0
        game_history = []
        
        while True:
            print(f"\n--- Round {guess_count + 1} ---")
            print(f"Possible targets remaining: {self.get_target_count()}")
            print(f"Remaining targets: {self.get_possible_targets()}")
            
            optimal_guess = self.get_optimal_guess()
            if optimal_guess is None:
                print("No more possible targets!")
                break
            
            print(f"\n🎯 SUGGESTED GUESS: {optimal_guess}")
            
            # Show target info for reference
            target_info = self.get_target_info(optimal_guess)
            if target_info:
                print(f"📋 Target Info:")
                for key, value in target_info.items():
                    print(f"   {key}: {value}")
            
            print(f"\n➡️  Now go to the game and guess: {optimal_guess}")
            print("   Then come back and tell me what feedback you got!")
            
            feedback = self._get_user_feedback()
            
            if not feedback:
                print("No feedback provided. Exiting.")
                break
            
            game_history.append({
                'guess': optimal_guess,
                'feedback': feedback.copy()
            })
            
            self.apply_guess(optimal_guess, feedback)
            guess_count += 1
            
            if feedback.get(self.target_column.lower()) == 'correct':
                print(f"\n🎉 CONGRATULATIONS! You found the target: {optimal_guess}")
                print(f"   Solved in {guess_count} guesses!")
                break
            
            if self.get_target_count() == 0:
                print("\n❌ No targets match the feedback. There might be an error in the feedback.")
                break
            
            if self.get_target_count() == 1:
                remaining = self.get_possible_targets()[0]
                print(f"\n🎉 CONGRATULATIONS! The correct answer is: {remaining}")
                print(f"   Solved in {guess_count} guesses!")
                # Add the final correct guess to game history
                game_history.append({
                    'guess': remaining,
                    'feedback': {self.target_column.lower(): 'correct'}
                })
                break
        
        # Show game summary
        if game_history:
            print(f"\n📊 GAME SUMMARY:")
            print(f"   Total guesses: {guess_count}")
            # Determine the final answer
            final_answer = 'Not found'
            if feedback.get(self.target_column.lower()) == 'correct':
                final_answer = optimal_guess
            elif self.get_target_count() == 0 and len(game_history) > 0:
                final_answer = game_history[-1]['guess']
            print(f"   Final answer: {final_answer}")
            print(f"\n📝 Guess History:")
            for i, round_data in enumerate(game_history, 1):
                print(f"   Round {i}: {round_data['guess']}")
                feedback_summary = []
                for category, result in round_data['feedback'].items():
                    if result != 'incorrect':
                        feedback_summary.append(f"{category}: {result}")
                if feedback_summary:
                    print(f"        Feedback: {', '.join(feedback_summary)}")
    
    def _get_user_feedback(self) -> Dict[str, str]:
        """Get feedback from user input"""
        print(f"\nEnter feedback for each category:")
        print("For yes/no categories: 'correct' or 'incorrect'")
        print("For partial categories: 'correct', 'partial', or 'incorrect'")
        print("For orderable categories: 'lower', 'higher', or 'correct'")
        print("(Press Enter to skip a category)")
        print("Type 'guessed' for any category if you found the correct target!")
        
        feedback = {}
        categories = self.get_category_config()
        
        for category, valid_options in categories:
            while True:
                user_input = input(f"{category}: ").strip().lower()
                if user_input == '':
                    break
                elif user_input == 'guessed':
                    feedback[self.target_column.lower()] = 'correct'
                    return feedback
                elif user_input in valid_options:
                    feedback[category] = user_input
                    break
                else:
                    print(f"Invalid input. Please enter one of: {valid_options} or 'guessed'")
        
        return feedback 