# GameDleSolver - Abstract Base Class for Game-Dle Solvers

This project provides an abstract base class that allows you to quickly create solvers for different game-dle variants (like LolDle, PokéDle, etc.) with minimal code.

## Overview

The `GameDleSolver` abstract base class handles all the complex logic for:
- Optimal guessing using entropy-based algorithms
- Filtering possible targets based on feedback
- Handling different types of categories (yes/no, partial matchable, orderable)
- User interaction and discovery mode
- Caching for performance optimization

## Quick Start

### 1. Create Your CSV File

Your CSV should have a header row and include all the categories for your game. Example structure:

```csv
Target,Category1,Category2,Category3,Category4
Item1,Value1,Value2,Value3,Value4
Item2,Value1,Value2,Value3,Value4
```

### 2. Extend the Abstract Base Class

Create a new Python file and extend `GameDleSolver`:

```python
from GameDleSolver import GameDleSolver
from typing import List, Tuple

class MyGameSolver(GameDleSolver):
    def __init__(self):
        super().__init__("MyGame.csv", "Target")
    
    def _define_category_types(self):
        # Define which categories can have partial matches
        self.partial_matchable = ["Category1", "Category2"]
        
        # Define which categories are exact match only
        self.yes_or_no = ["Category3"]
        
        # Define which categories can be compared (before/after/correct)
        self.orderable = ["Category4"]
    
    def get_category_config(self) -> List[Tuple[str, List[str]]]:
        return [
            ('category1', ['correct', 'partial', 'incorrect']),
            ('category2', ['correct', 'partial', 'incorrect']),
            ('category3', ['correct', 'incorrect']),
            ('category4', ['before', 'after', 'correct'])
        ]
    
    def get_display_name(self) -> str:
        return "MyGame"

if __name__ == "__main__":
    solver = MyGameSolver()
    solver.discovery_mode()
```

### 3. Run Your Solver

```bash
python MyGameSolver.py
```

## Category Types

### Partial Matchable Categories
Categories that can have comma-separated values and support partial matches:
- **Example**: "Fire, Flying" types in Pokémon
- **Feedback options**: `correct`, `partial`, `incorrect`
- **Logic**: 
  - `correct`: Exact match only
  - `partial`: Some values match but not exact
  - `incorrect`: No values match

### Yes/No Categories
Categories that are either exactly right or wrong:
- **Example**: Gender, Color, Resource type
- **Feedback options**: `correct`, `incorrect`
- **Logic**: Simple equality check

### Orderable Categories
Categories that can be compared numerically:
- **Example**: Release year, Height, Weight, Generation
- **Feedback options**: `before`, `after`, `correct`
- **Logic**: Numerical comparison

## Examples

### LolDle Solver
See `LolDleSolverV2.py` for a complete implementation.

### PokéDle Solver
See `PokeDleSolver.py` for an example implementation.

## Features

### Automatic Optimal Guessing
The solver uses entropy-based algorithms to find the guess that will provide the most information, minimizing the number of attempts needed.

### Smart Filtering
- Handles comma-separated values automatically
- Supports partial matching for multi-value categories
- Efficient filtering algorithms

### User-Friendly Interface
- Interactive discovery mode
- Clear feedback prompts
- Game history tracking
- "guessed" keyword to quickly end rounds

### Performance Optimized
- Caching for entropy calculations
- Efficient data structures
- Minimal memory usage

## Advanced Usage

### Custom Category Logic
If you need custom logic for specific categories, you can override the filter methods:

```python
def _apply_custom_filter(self, guessed_target, feedback):
    # Your custom filtering logic here
    pass
```

### Custom Feedback Simulation
Override `_simulate_feedback` for custom feedback logic:

```python
def _simulate_feedback(self, guess_target, target):
    # Your custom feedback simulation logic
    return feedback
```

## File Structure

```
├── GameDleSolver.py          # Abstract base class
├── LolDleSolverV2.py         # LolDle implementation
├── PokeDleSolver.py          # Example PokéDle implementation
├── LolDle.csv               # LolDle data
├── requirements.txt          # Dependencies
└── README_GameDleSolver.md   # This file
```

## Dependencies

- pandas
- math (built-in)
- random (built-in)
- abc (built-in)
- typing (built-in)

## Tips for Creating New Solvers

1. **Analyze your game's categories** - Determine which are partial matchable, yes/no, or orderable
2. **Create a comprehensive CSV** - Include all possible values and ensure data quality
3. **Test with simple cases** - Verify your category configurations work correctly
4. **Use the discovery mode** - It's the easiest way to test your solver

## Contributing

Feel free to create solvers for other games and share them! The abstract base class makes it easy to add new game variants. 