#!/usr/bin/env python3
"""
Test script to verify that when there are only 2 possibilities, the solver chooses one of them.
"""

from LoldleSolver import LolDleSolver

def test_two_possibilities():
    """Test that when there are only 2 possibilities, the solver chooses one of them"""
    print("Testing two possibilities scenario...")
    
    try:
        solver = LolDleSolver()
        print("✓ LolDleSolver initialized successfully")
        
        # Get all possible targets
        all_targets = solver.get_possible_targets()
        print(f"✓ Total targets: {len(all_targets)}")
        
        # Take the first two targets
        target1, target2 = all_targets[0], all_targets[1]
        print(f"✓ Selected targets: {target1}, {target2}")
        
        # Manually set possible_targets to only these two
        solver.possible_targets = solver.data[solver.data[solver.target_column].isin([target1, target2])]
        
        # Verify we now have exactly 2 possibilities
        remaining_targets = solver.get_possible_targets()
        print(f"✓ Remaining targets: {remaining_targets}")
        assert len(remaining_targets) == 2, f"Expected 2 targets, got {len(remaining_targets)}"
        
        # Get the optimal guess
        optimal_guess = solver.get_optimal_guess()
        print(f"✓ Optimal guess: {optimal_guess}")
        
        # Verify the optimal guess is one of the two remaining targets
        assert optimal_guess in remaining_targets, f"Optimal guess {optimal_guess} is not in remaining targets {remaining_targets}"
        
        print("✓ SUCCESS: When there are only 2 possibilities, the solver chooses one of them!")
        return True
        
    except Exception as e:
        print(f"✗ Error in test: {e}")
        return False

def main():
    """Run the test"""
    print("Testing Two Possibilities Scenario")
    print("=" * 50)
    
    success = test_two_possibilities()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ TEST PASSED: Solver correctly chooses from 2 remaining possibilities")
    else:
        print("✗ TEST FAILED: Solver does not choose from 2 remaining possibilities")

if __name__ == "__main__":
    main() 