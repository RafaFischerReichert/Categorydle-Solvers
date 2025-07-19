import json
import os
from LoldleSolver import LolDleSolver
from NarutodleSolver import MyGameSolver as NarutodleSolver
from OnepiecedleSolver import OnePieceDleSolver
from WarframedleSolver import Warframedle

def main():
    solvers = [
        LolDleSolver(),
        NarutodleSolver(),
        OnePieceDleSolver(),
        Warframedle(),
    ]
    optimal_guesses = {}
    for solver in solvers:
        print(f"Calculating optimal first guess for {solver.get_display_name()}...")
        guess = solver._calculate_optimal_first_guesses()
        optimal_guesses[solver.get_display_name()] = guess
        print(f"  -> {guess}")
    # Overwrite optimal_guesses.json
    with open("optimal_guesses.json", "w") as f:
        json.dump(optimal_guesses, f, indent=2)
    print("\nAll optimal guesses saved to optimal_guesses.json!")

if __name__ == "__main__":
    main() 