#!/usr/bin/env python3
"""
Test script to verify optimal first guess functionality for all solvers.
"""

from LolDleSolver import LolDleSolver
from NarutodleSolver import MyGameSolver as NarutodleSolver
from OnePieceDleSolver import OnePieceDleSolver
from WarframedleSolver import Warframedle as WarframedleSolver

def test_solver(solver_class, solver_name):
    """Test a specific solver's optimal first guess functionality"""
    print(f"\n{'='*50}")
    print(f"Testing {solver_name}")
    print(f"{'='*50}")
    
    try:
        solver = solver_class()
        print(f"✓ {solver_name} initialized successfully")
        
        # Test optimal first guess
        print(f"Getting optimal first guess...")
        optimal_guess = solver.get_optimal_first_guess()
        
        if optimal_guess:
            print(f"✓ Optimal first guess: {optimal_guess}")
            
            # Show some info about the optimal guess
            target_info = solver.get_target_info(optimal_guess)
            if target_info:
                print(f"  Target info:")
                for key, value in list(target_info.items())[:3]:  # Show first 3 attributes
                    print(f"    {key}: {value}")
        else:
            print("✗ No optimal first guess found")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing {solver_name}: {e}")
        return False

def main():
    """Test all solvers"""
    print("Testing Optimal First Guess Functionality")
    print("This will calculate optimal first guesses for each solver on first run.")
    
    solvers = [
        (LolDleSolver, "LolDle"),
        (NarutodleSolver, "Narutodle"),
        (OnePieceDleSolver, "OnePieceDle"),
        (WarframedleSolver, "Warframedle")
    ]
    
    results = []
    for solver_class, solver_name in solvers:
        success = test_solver(solver_class, solver_name)
        results.append((solver_name, success))
    
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    
    for solver_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{solver_name}: {status}")
    
    all_passed = all(success for _, success in results)
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

if __name__ == "__main__":
    main() 