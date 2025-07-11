import pandas as pd
import math
import random
import json
import os
import concurrent.futures
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple

# Top-level function for parallel entropy calculation
def calculate_entropy_for_guess_parallel(args):
    """
    Calculate entropy for a single guess in a separate process.
    This function must be at module level for multiprocessing.
    """
    data, target_column, yes_or_no, orderable, partial_matchable, guess_target, all_targets = args
    
    expected_entropy = 0
    total_outcomes = 0
    
    for target in all_targets:
        feedback = simulate_feedback_parallel(data, target_column, yes_or_no, orderable, partial_matchable, guess_target, target)
        remaining_count = count_remaining_targets_after_feedback_parallel(data, target_column, yes_or_no, orderable, partial_matchable, guess_target, feedback, all_targets)
        
        if remaining_count > 0:
            p = remaining_count / len(all_targets)
            expected_entropy += p * math.log2(remaining_count)
            total_outcomes += 1
    
    if total_outcomes > 0:
        expected_entropy /= total_outcomes
    
    return guess_target, expected_entropy

def simulate_feedback_parallel(data, target_column, yes_or_no, orderable, partial_matchable, guess_target, target):
    """Simulate feedback for parallel processing"""
    guess_data = data[data[target_column] == guess_target].iloc[0]
    target_data = data[data[target_column] == target].iloc[0]
    
    feedback = {}
    
    # Target name
    feedback[target_column.lower()] = 'correct' if guess_target == target else 'incorrect'
    
    # Yes/No categories
    for category in yes_or_no:
        feedback[category.lower()] = 'correct' if guess_data[category] == target_data[category] else 'incorrect'
    
    # Orderable categories
    for category in orderable:
        if target_data[category] < guess_data[category]:
            feedback[category.lower()] = 'lower'
        elif target_data[category] > guess_data[category]:
            feedback[category.lower()] = 'higher'
        else:
            feedback[category.lower()] = 'correct'
    
    # Partial matchable categories
    for category in partial_matchable:
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

def count_remaining_targets_after_feedback_parallel(data, target_column, yes_or_no, orderable, partial_matchable, guess_target, feedback, possible_targets):
    """Count remaining targets for parallel processing"""
    remaining_count = 0
    
    for target in possible_targets:
        if target_compatible_with_feedback_parallel(data, target_column, yes_or_no, orderable, partial_matchable, target, guess_target, feedback):
            remaining_count += 1
    
    return remaining_count

def target_compatible_with_feedback_parallel(data, target_column, yes_or_no, orderable, partial_matchable, target, guess_target, feedback):
    """Check target compatibility for parallel processing"""
    target_data = data[data[target_column] == target].iloc[0]
    guess_data = data[data[target_column] == guess_target].iloc[0]
    
    # Check target name feedback
    if feedback.get(target_column.lower()) == 'correct':
        return target == guess_target
    elif feedback.get(target_column.lower()) == 'incorrect':
        if target == guess_target:
            return False
    
    # Check yes/no categories
    for category in yes_or_no:
        feedback_key = category.lower()
        if feedback_key in feedback:
            if feedback[feedback_key] == 'correct':
                if target_data[category] != guess_data[category]:
                    return False
            elif feedback[feedback_key] == 'incorrect':
                if target_data[category] == guess_data[category]:
                    return False
    
    # Check orderable categories
    for category in orderable:
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
    for category in partial_matchable:
        feedback_key = category.lower()
        if feedback_key in feedback:
            target_value = target_data[category]
            guess_value = guess_data[category]
            
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
        self.optimal_first_guesses = None
        
        # Validate that target column exists
        if target_column not in self.data.columns:
            raise ValueError(f"Target column '{target_column}' not found in CSV. Available columns: {self.data.columns.tolist()}")
        
        # Define category types based on the CSV structure
        self._define_category_types()
        
        # Load optimal first guesses
        self._load_optimal_first_guesses()
    
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
        Uses parallel processing for faster calculation.
        """
        if len(self.possible_targets) <= 1:
            return self.possible_targets[self.target_column].iloc[0] if len(self.possible_targets) == 1 else None
        
        # Check if we're at the initial state and have preloaded first guesses
        if len(self.possible_targets) == len(self.data):
            first_guess = self.get_optimal_first_guess_for_current_state()
            if first_guess:
                return first_guess
        
        # Use parallel processing for optimal guess calculation
        return self._get_optimal_guess_parallel()
    
    def _get_optimal_guess_parallel(self) -> Optional[str]:
        """
        Find the optimal guess using parallel processing.
        """
        all_targets = self.data[self.target_column].tolist()
        current_possible_targets = self.possible_targets[self.target_column].tolist()
        
        # If we have very few possible targets, use the original method for speed
        if len(current_possible_targets) <= 10:
            return self._get_optimal_guess_sequential()
        
        # Prepare arguments for parallel processing
        args_list = []
        for guess in all_targets:
            args = (
                self.data,
                self.target_column,
                self.yes_or_no,
                self.orderable,
                self.partial_matchable,
                guess,
                current_possible_targets  # Use current possible targets, not all targets
            )
            args_list.append(args)
        
        best_guess = None
        best_expected_entropy = float('inf')
        
        # Use ProcessPoolExecutor for parallel processing
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Submit all tasks and collect results
            future_to_guess = {executor.submit(calculate_entropy_for_guess_parallel, args): args[5] for args in args_list}
            
            for future in concurrent.futures.as_completed(future_to_guess):
                guess, expected_entropy = future.result()
                
                # Check cache first
                cache_key = self._get_cache_key(guess)
                if cache_key in self.entropy_cache:
                    expected_entropy = self.entropy_cache[cache_key]
                else:
                    self.entropy_cache[cache_key] = expected_entropy
                
                if expected_entropy < best_expected_entropy:
                    best_expected_entropy = expected_entropy
                    best_guess = guess
        
        return best_guess
    
    def _get_optimal_guess_sequential(self) -> Optional[str]:
        """
        Find the optimal guess using the original sequential method.
        Used for small target pools where parallel overhead isn't worth it.
        """
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
            
            # Manually apply the feedback to count remaining targets without creating solver instances
            remaining_count = self._count_remaining_targets_after_feedback(guess_target, feedback, self.possible_targets[self.target_column].tolist())
            
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

    def _get_optimal_guesses_filename(self) -> str:
        """Get the filename for storing optimal first guesses"""
        return "optimal_guesses.json"

    def _load_optimal_first_guesses(self):
        filename = self._get_optimal_guesses_filename()
        game_name = self.get_display_name()
        
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    all_guesses = json.load(f)
                
                if isinstance(all_guesses, dict) and game_name in all_guesses:
                    self.optimal_first_guesses = all_guesses[game_name]
                    if isinstance(self.optimal_first_guesses, str):
                        print(f"Loaded optimal first guess for {game_name}: {self.optimal_first_guesses}")
                    else:
                        print(f"Optimal guess for {game_name} is not a string. Recalculating.")
                        self.optimal_first_guesses = None
                else:
                    print(f"Optimal guess for {game_name} not found in {filename}. Will calculate on first run.")
                    self.optimal_first_guesses = None
            except Exception as e:
                print(f"Error loading optimal guesses from {filename}: {e}")
                self.optimal_first_guesses = None
        else:
            print(f"Optimal guesses file {filename} not found. Will calculate on first run.")
            self.optimal_first_guesses = None

    def _save_optimal_first_guesses(self):
        if self.optimal_first_guesses is None:
            return
            
        filename = self._get_optimal_guesses_filename()
        game_name = self.get_display_name()
        
        try:
            # Load existing guesses or create new dict
            all_guesses = {}
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    all_guesses = json.load(f)
            
            # Update with new guess
            all_guesses[game_name] = self.optimal_first_guesses
            
            # Save back to file
            with open(filename, 'w') as f:
                json.dump(all_guesses, f, indent=2)
            print(f"Saved optimal first guess for {game_name}: {self.optimal_first_guesses}")
        except Exception as e:
            print(f"Error saving optimal guesses to {filename}: {e}")
    
    def _calculate_optimal_first_guesses(self) -> str:
        """
        Calculate the optimal first guess that works well across all targets.
        This is computationally expensive and should only be done once.
        Uses parallel processing for significant speedup.
        """
        print("Calculating optimal first guess using parallel processing... This may take a while.")
        
        all_targets = self.data[self.target_column].tolist()
        print(f"Total targets to evaluate: {len(all_targets)}")
        
        # Prepare arguments for parallel processing
        args_list = []
        for guess in all_targets:
            args = (
                self.data,
                self.target_column,
                self.yes_or_no,
                self.orderable,
                self.partial_matchable,
                guess,
                all_targets
            )
            args_list.append(args)
        
        best_guess = None
        best_overall_entropy = float('inf')
        
        # Use ProcessPoolExecutor for parallel processing
        with concurrent.futures.ProcessPoolExecutor() as executor:
            print(f"Starting parallel processing with {executor._max_workers} workers...")
            
            # Submit all tasks and collect results
            future_to_guess = {executor.submit(calculate_entropy_for_guess_parallel, args): args[5] for args in args_list}
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_guess):
                guess, avg_entropy = future.result()
                completed += 1
                print(f"Completed {completed}/{len(all_targets)}: '{guess}' - entropy: {avg_entropy:.2f}")
                
                if avg_entropy < best_overall_entropy:
                    best_overall_entropy = avg_entropy
                    best_guess = guess
                    print(f"    NEW BEST GUESS: {best_guess} (entropy: {best_overall_entropy:.2f})")
        
        print(f"Best overall first guess: {best_guess} (avg entropy: {best_overall_entropy:.2f})")
        return best_guess
    
    def _calculate_expected_entropy_isolated(self, guess_target: str) -> float:
        """
        Calculate expected entropy for a guess without creating temporary solver instances.
        This method is isolated and doesn't trigger loading/saving logic.
        """
        expected_entropy = 0
        total_outcomes = 0
        
        # Use the current state of possible_targets (should be all targets during precompute)
        current_possible_targets = self.possible_targets[self.target_column].tolist()
        
        for idx, target in enumerate(current_possible_targets):
            if idx % 50 == 0:
                print(f"      [debug] Entropy calc for guess '{guess_target}': {idx+1}/{len(current_possible_targets)} targets")
            feedback = self._simulate_feedback(guess_target, target)
            
            # Manually apply the feedback to count remaining targets
            remaining_count = self._count_remaining_targets_after_feedback(guess_target, feedback, current_possible_targets)
            
            if remaining_count > 0:
                p = remaining_count / len(current_possible_targets)
                expected_entropy += p * math.log2(remaining_count)
                total_outcomes += 1
        
        if total_outcomes > 0:
            expected_entropy /= total_outcomes
        
        return expected_entropy
    
    def _count_remaining_targets_after_feedback(self, guess_target: str, feedback: Dict[str, str], possible_targets: List[str]) -> int:
        """
        Count how many targets would remain after applying feedback, without creating solver instances.
        """
        remaining_count = 0
        
        for target in possible_targets:
            # Check if this target is compatible with the feedback
            if self._target_compatible_with_feedback(target, guess_target, feedback):
                remaining_count += 1
        
        return remaining_count
    
    def _target_compatible_with_feedback(self, target: str, guess_target: str, feedback: Dict[str, str]) -> bool:
        """
        Check if a target is compatible with the given feedback for a guess.
        """
        # Get the data for both target and guess
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
                
                if feedback[feedback_key] == 'correct':
                    if target_value != guess_value:
                        return False
                elif feedback[feedback_key] == 'incorrect':
                    # Check if there's any overlap
                    if ',' in str(target_value) and ',' in str(guess_value):
                        target_values = set(val.strip() for val in str(target_value).split(','))
                        guess_values = set(val.strip() for val in str(guess_value).split(','))
                        if target_values & guess_values:  # If there's any overlap
                            return False
                    elif target_value == guess_value:
                        return False
                elif feedback[feedback_key] == 'partial':
                    # Check if there's partial overlap but not exact match
                    if ',' in str(target_value) and ',' in str(guess_value):
                        target_values = set(val.strip() for val in str(target_value).split(','))
                        guess_values = set(val.strip() for val in str(guess_value).split(','))
                        overlap = target_values & guess_values
                        if not overlap or target_values == guess_values:  # No overlap or exact match
                            return False
                    else:
                        # For single values, partial is not possible
                        return False
        
        return True
    
    def get_optimal_first_guess(self) -> Optional[str]:
        if self.optimal_first_guesses is None:
            self.optimal_first_guesses = self._calculate_optimal_first_guesses()
            self._save_optimal_first_guesses()
        
        return self.optimal_first_guesses
    
    def get_optimal_first_guess_for_current_state(self) -> Optional[str]:
        """
        Get the optimal first guess for the current game state.
        If we're at the beginning (all targets possible), use preloaded guess.
        Otherwise, fall back to the regular optimal guess calculation.
        """
        # Check if we're at the initial state (all targets possible)
        if len(self.possible_targets) == len(self.data):
            # We're at the beginning, use preloaded optimal first guess
            optimal_guess = self.get_optimal_first_guess()
            if optimal_guess:
                print(f"Using preloaded optimal first guess: {optimal_guess}")
                return optimal_guess
        
        # Not at initial state or no preloaded guesses, use regular optimal guess calculation
        # Avoid recursive call by directly using the parallel or sequential method
        if len(self.possible_targets) <= 10:
            return self._get_optimal_guess_sequential()
        else:
            return self._get_optimal_guess_parallel() 