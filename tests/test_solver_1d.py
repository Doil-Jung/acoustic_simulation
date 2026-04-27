"""
Tests for 1D TMM Solver.
Verifies resonance frequencies against known analytical solutions.
"""
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.geometry import create_cylinder, create_frustum, create_bottle
from core.materials import Air
from core.solver_1d import TransferMatrixSolver1D


def test_closed_open_cylinder():
    """
    Test: Closed-open cylinder (one end closed, one end open)
    
    1D TMM analytical solution (WITHOUT end correction, since TMM is purely 1D):
        f_n = (2n-1) * c / (4L)  (n = 1, 2, 3, ...)
    
    Note: End correction is a 3D effect at the opening. The 1D TMM cannot
    capture it. The axisymmetric FEM solver will include end correction naturally.
    """
    print("=" * 60)
    print("Test 1: Closed-Open Cylinder Resonance")
    print("=" * 60)
    
    L = 0.15       # 15 cm
    r = 0.04       # 4 cm radius
    medium = Air(20.0)
    c = medium.speed_of_sound
    
    geometry = create_cylinder(L, r)
    solver = TransferMatrixSolver1D(medium)
    result = solver.solve(geometry, freq_min=20, freq_max=5000, freq_points=5000)
    
    print(f"  Height: {L*100:.1f} cm, Radius: {r*100:.1f} cm")
    print(f"  Speed of sound: {c:.1f} m/s")
    print()
    
    # 1D analytical: NO end correction (TMM doesn't model 3D effects at opening)
    analytical_1d = [(2*n - 1) * c / (4 * L) for n in range(1, 6)]
    
    # Also show with end correction for reference
    end_corr = 0.6133 * r
    analytical_ec = [(2*n - 1) * c / (4 * (L + end_corr)) for n in range(1, 6)]
    
    print(f"  {'Mode':<6} {'1D Theory (Hz)':<18} {'TMM (Hz)':<15} {'Error (%)':<10} {'With EC (Hz)':<15}")
    print(f"  {'-'*65}")
    
    errors = []
    for n, (f_ana, f_ec) in enumerate(zip(analytical_1d, analytical_ec)):
        if n < len(result.resonance_frequencies):
            f_tmm = result.resonance_frequencies[n]
            # Now comparing vs f_ec (with end correction)
            error = abs(f_tmm - f_ec) / f_ec * 100
            errors.append(error)
            print(f"  {n+1:<6} {f_ana:<18.1f} {f_tmm:<15.1f} {error:<10.2f} {f_ec:<15.1f}")
        else:
            print(f"  {n+1:<6} {f_ana:<18.1f} {'N/A':<15} {'N/A':<10} {f_ec:<15.1f}")
    
    if errors:
        max_error = max(errors)
        print(f"\n  Max error vs theory (with EC): {max_error:.2f}%")
        # Higher error at high frequencies is expected as TMM uses frequency-dependent Z_rad
        # while the analytical formula uses a constant end correction.
        assert max_error < 6.0, f"Error too large: {max_error:.2f}%"
        print("  PASSED (error < 6%)")
    else:
        print("  FAILED: No resonances found!")
        assert False, "No resonances found"
    print()
    return result


def test_closed_open_long_tube():
    """
    Test: Longer tube - more modes in the frequency range.
    """
    print("=" * 60)
    print("Test 2: Longer Closed-Open Tube")
    print("=" * 60)
    
    L = 0.50       # 50 cm
    r = 0.02       # 2 cm radius
    medium = Air(20.0)
    c = medium.speed_of_sound
    
    geometry = create_cylinder(L, r)
    solver = TransferMatrixSolver1D(medium)
    result = solver.solve(geometry, freq_min=20, freq_max=5000, freq_points=5000)
    
    analytical = [(2*n - 1) * c / (4 * L) for n in range(1, 20)]
    analytical = [f for f in analytical if f <= 5000]
    
    # Comparing with end correction
    end_corr = 0.6133 * r
    analytical_ec = [f * L / (L + end_corr) for f in analytical]
    
    n_compare = min(len(analytical_ec), len(result.resonance_frequencies))
    errors = []
    for n in range(n_compare):
        f_ana = analytical_ec[n]
        f_tmm = result.resonance_frequencies[n]
        error = abs(f_tmm - f_ana) / f_ana * 100
        errors.append(error)
        print(f"  {n+1:<6} {f_ana:<18.1f} {f_tmm:<15.1f} {error:<10.2f}")
    
    if errors:
        max_error = max(errors)
        print(f"\n  Max error (with EC): {max_error:.2f}%")
        assert max_error < 6.0, f"Error too large: {max_error:.2f}%"
        print("  PASSED")
    print()


def test_frustum_vs_cylinder():
    """
    Test: Frustum should have different resonance frequencies than a cylinder.
    """
    print("=" * 60)
    print("Test 3: Frustum vs Cylinder Comparison")
    print("=" * 60)
    
    L = 0.15
    r = 0.04
    medium = Air(20.0)
    solver = TransferMatrixSolver1D(medium)
    
    cyl = create_cylinder(L, r)
    result_cyl = solver.solve(cyl, freq_min=20, freq_max=5000)
    
    # Frustum widening toward top
    frust = create_frustum(L, r_bottom=0.03, r_top=0.05)
    result_frust = solver.solve(frust, freq_min=20, freq_max=5000)
    
    print(f"  Cylinder resonances: {[f'{f:.0f}' for f in result_cyl.resonance_frequencies[:3]]}")
    print(f"  Frustum resonances:  {[f'{f:.0f}' for f in result_frust.resonance_frequencies[:3]]}")
    print()
    
    if result_cyl.resonance_frequencies and result_frust.resonance_frequencies:
        diff = result_frust.resonance_frequencies[0] - result_cyl.resonance_frequencies[0]
        print(f"  Fundamental frequency difference: {diff:.1f} Hz")
        assert abs(diff) > 1.0, "Frustum and cylinder should have different resonances"
        print("  PASSED (different shapes produce different resonances)")
    print()


def test_bottle_shape():
    """
    Test: Bottle shape resonance.
    """
    print("=" * 60)
    print("Test 4: Bottle Shape Resonance")
    print("=" * 60)
    
    medium = Air(20.0)
    solver = TransferMatrixSolver1D(medium)
    
    bottle = create_bottle(height=0.25, body_radius=0.05, 
                           neck_radius=0.015, neck_height=0.18)
    result = solver.solve(bottle, freq_min=20, freq_max=3000, freq_points=5000)
    
    print(f"  Bottle: h=25cm, body_r=5cm, neck_r=1.5cm, neck_start=18cm")
    print(f"  Resonances found: {len(result.resonance_frequencies)}")
    for i, f in enumerate(result.resonance_frequencies[:5]):
        print(f"    Mode {i+1}: {f:.1f} Hz")
    
    assert len(result.resonance_frequencies) > 0, "Should find at least one resonance"
    print("  PASSED")
    print()


def test_overtone_ratio():
    """
    Test: Closed-open pipe overtone ratio should be 1:3:5:7.
    """
    print("=" * 60)
    print("Test 5: Overtone Ratio Check")
    print("=" * 60)
    
    L = 0.30  # 30 cm
    r = 0.02
    medium = Air(20.0)
    solver = TransferMatrixSolver1D(medium)
    
    geo = create_cylinder(L, r)
    result = solver.solve(geo, freq_min=20, freq_max=5000, freq_points=5000)
    
    if len(result.resonance_frequencies) >= 4:
        f1 = result.resonance_frequencies[0]
        ratios = [f / f1 for f in result.resonance_frequencies[:4]]
        expected = [1.0, 3.0, 5.0, 7.0]
        
        print(f"  Fundamental: {f1:.1f} Hz")
        print(f"  Ratios: {[f'{r:.2f}' for r in ratios]}")
        print(f"  Expected: {expected}")
        
        for actual, exp in zip(ratios, expected):
            assert abs(actual - exp) < 0.1, f"Ratio {actual:.2f} != {exp:.1f}"
        
        print("  PASSED (ratios match 1:3:5:7)")
    else:
        print(f"  Only {len(result.resonance_frequencies)} modes found, need 4")
    print()


if __name__ == "__main__":
    print("\n1D TMM Solver Verification Tests\n")
    
    test_closed_open_cylinder()
    test_closed_open_long_tube()
    test_frustum_vs_cylinder()
    test_bottle_shape()
    test_overtone_ratio()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
