"""
Frequency response visualization.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from typing import Optional, List, Tuple


def plot_frequency_response(frequencies: np.ndarray, response: np.ndarray,
                            resonance_frequencies: Optional[List[float]] = None,
                            title: str = "Frequency Response",
                            ylabel: str = "Magnitude",
                            db_scale: bool = True,
                            figsize: Tuple[float, float] = (10, 5)) -> plt.Figure:
    """
    Plot frequency response with optional resonance markers.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    if db_scale:
        ref = np.max(response) if np.max(response) > 0 else 1.0
        y_data = 20 * np.log10(response / ref + 1e-30)
        ylabel = f"{ylabel} (dB)"
    else:
        y_data = response
    
    ax.plot(frequencies, y_data, 'b-', linewidth=1.0)
    
    if resonance_frequencies:
        for f_res in resonance_frequencies:
            idx = np.argmin(np.abs(frequencies - f_res))
            ax.axvline(x=f_res, color='r', linestyle='--', alpha=0.5, linewidth=0.8)
            ax.plot(frequencies[idx], y_data[idx], 'rv', markersize=8)
            ax.annotate(f'{f_res:.0f} Hz', xy=(f_res, y_data[idx]),
                       xytext=(5, 10), textcoords='offset points',
                       fontsize=8, color='red')
    
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(frequencies[0], frequencies[-1])
    
    fig.tight_layout()
    return fig


def plot_impedance(frequencies: np.ndarray, impedance: np.ndarray,
                   resonance_frequencies: Optional[List[float]] = None,
                   figsize: Tuple[float, float] = (10, 8)) -> plt.Figure:
    """
    Plot input impedance (magnitude and phase).
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
    
    mag = np.abs(impedance)
    phase = np.angle(impedance, deg=True)
    
    # Magnitude (log scale)
    ax1.semilogy(frequencies, mag, 'b-', linewidth=1.0)
    if resonance_frequencies:
        for f_res in resonance_frequencies:
            ax1.axvline(x=f_res, color='r', linestyle='--', alpha=0.5, linewidth=0.8)
    ax1.set_ylabel('|Z| (Pa·s/m³)')
    ax1.set_title('Input Impedance')
    ax1.grid(True, alpha=0.3)
    
    # Phase
    ax2.plot(frequencies, phase, 'g-', linewidth=1.0)
    if resonance_frequencies:
        for f_res in resonance_frequencies:
            ax2.axvline(x=f_res, color='r', linestyle='--', alpha=0.5, linewidth=0.8)
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Phase (°)')
    ax2.set_ylim(-180, 180)
    ax2.grid(True, alpha=0.3)
    
    fig.tight_layout()
    return fig


def plot_mode_shape(z_values: np.ndarray, pressure: np.ndarray,
                    frequency: float,
                    geometry_profile: Optional[Tuple[np.ndarray, np.ndarray]] = None,
                    figsize: Tuple[float, float] = (10, 5)) -> plt.Figure:
    """
    Plot pressure mode shape along the tube.
    Optionally overlay the geometry profile.
    """
    fig, ax1 = plt.subplots(figsize=figsize)
    
    # Convert z to cm for readability
    z_cm = z_values * 100
    
    # Split z_values based on geometry profile height if available
    h_cm = None
    if geometry_profile is not None:
        h_cm = np.max(geometry_profile[0]) * 100
    
    if h_cm is not None:
        # Internal part (Solid line)
        mask_in = z_cm <= h_cm + 1e-5
        ax1.plot(z_cm[mask_in], pressure[mask_in], 'b-', linewidth=2, label='|p| (Internal)')
        ax1.fill_between(z_cm[mask_in], 0, pressure[mask_in], alpha=0.2, color='blue')
        
        # External part / End correction (Dashed line)
        mask_out = z_cm >= h_cm - 1e-5
        ax1.plot(z_cm[mask_out], pressure[mask_out], 'b--', linewidth=2, label='|p| (End Correction)')
    else:
        ax1.plot(z_cm, pressure, 'b-', linewidth=2, label='|p| (normalized)')
        ax1.fill_between(z_cm, 0, pressure, alpha=0.2, color='blue')
        
    ax1.set_xlabel('Position z (cm)')
    ax1.set_ylabel('Normalized Pressure |p|')
    ax1.set_title(f'Mode Shape at {frequency:.1f} Hz')
    
    if geometry_profile is not None:
        z_geo, r_geo = geometry_profile
        z_geo_cm = z_geo * 100
        r_geo_cm = r_geo * 100
        ax2 = ax1.twinx()
        ax2.plot(z_geo_cm, r_geo_cm, 'k--', linewidth=1.5, alpha=0.5, label='Radius')
        ax2.set_ylabel('Radius (cm)')
        ax2.set_ylim(0, np.max(r_geo_cm) * 1.2)  # Start from 0 with some padding
        ax2.legend(loc='upper left')
    
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_geometry_profile(geometry, figsize: Tuple[float, float] = (8, 6)) -> plt.Figure:
    """
    Plot the cross-section of the cavity geometry.
    Shows both halves (symmetric about z-axis).
    """
    z, r = geometry.get_profile(200)
    z_cm = z * 100
    r_cm = r * 100
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Draw both halves
    ax.plot(r_cm, z_cm, 'b-', linewidth=2)
    ax.plot(-r_cm, z_cm, 'b-', linewidth=2)
    
    # Bottom
    ax.plot([-r_cm[0], r_cm[0]], [z_cm[0], z_cm[0]], 'b-', linewidth=2)
    
    # Fill
    all_r = np.concatenate([r_cm, -r_cm[::-1]])
    all_z = np.concatenate([z_cm, z_cm[::-1]])
    ax.fill(all_r, all_z, alpha=0.1, color='skyblue')
    
    ax.set_xlabel('r (cm)')
    ax.set_ylabel('z (cm)')
    ax.set_title(f'{geometry.name} Cross Section')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.axvline(x=0, color='gray', linestyle=':', alpha=0.5)
    
    fig.tight_layout()
    return fig


def plot_water_filling_results(water_heights_cm: np.ndarray,
                                resonance_freqs: List[List[float]],
                                time_values: Optional[np.ndarray] = None,
                                figsize: Tuple[float, float] = (10, 6)) -> plt.Figure:
    """
    Plot resonance frequency vs water height (or time).
    
    Args:
        water_heights_cm: Water heights in cm
        resonance_freqs: List of resonance frequency lists at each water height
        time_values: Optional time values (seconds)
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    x_values = time_values if time_values is not None else water_heights_cm
    x_label = 'Time (s)' if time_values is not None else 'Water Height (cm)'
    
    # Extract first N resonance modes
    max_modes = 0
    for freqs in resonance_freqs:
        max_modes = max(max_modes, len(freqs))
    
    colors = plt.cm.viridis(np.linspace(0, 0.8, max(max_modes, 1)))
    
    for mode_idx in range(min(max_modes, 5)):  # Show up to 5 modes
        mode_freqs = []
        mode_x = []
        for j, freqs in enumerate(resonance_freqs):
            if mode_idx < len(freqs):
                mode_freqs.append(freqs[mode_idx])
                mode_x.append(x_values[j])
        
        if mode_freqs:
            ax.plot(mode_x, mode_freqs, 'o-', color=colors[mode_idx],
                    markersize=4, linewidth=1.5, label=f'Mode {mode_idx + 1}')
    
    ax.set_xlabel(x_label)
    ax.set_ylabel('Resonance Frequency (Hz)')
    ax.set_title('Resonance Frequency vs Water Level')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    fig.tight_layout()
    return fig

def plot_cavity_with_water(geometry, water_height: float, figsize: Tuple[float, float] = (6, 8)) -> plt.Figure:
    """
    Plot the cavity geometry and fill it with water up to water_height.
    """
    z, r = geometry.get_profile(200)
    z_cm = z * 100
    r_cm = r * 100
    wh_cm = water_height * 100
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # 1. Draw cavity wall
    ax.plot(r_cm, z_cm, 'k-', linewidth=2)
    ax.plot(-r_cm, z_cm, 'k-', linewidth=2)
    ax.plot([-r_cm[0], r_cm[0]], [0, 0], 'k-', linewidth=2)
    
    # 2. Fill cavity with transparency (Empty region)
    all_r = np.concatenate([r_cm, -r_cm[::-1]])
    all_z = np.concatenate([z_cm, z_cm[::-1]])
    ax.fill(all_r, all_z, alpha=0.05, color='gray')
    
    # 3. Draw Water
    if wh_cm > 0:
        # Mask geometry points below water height
        mask = z_cm <= wh_cm
        if np.any(mask):
            z_w = z_cm[mask]
            r_w = r_cm[mask]
            
            # If the last point isn't exactly at wh_cm, interpolate to get the radius at wh_cm
            if z_w[-1] < wh_cm:
                z_w = np.append(z_w, wh_cm)
                r_w = np.append(r_w, geometry.radius_at(water_height) * 100)
            
            w_r = np.concatenate([r_w, -r_w[::-1]])
            w_z = np.concatenate([z_w, z_w[::-1]])
            ax.fill(w_r, w_z, alpha=0.6, color='dodgerblue', label='Water')
            # Surface line
            r_surf = r_w[-1]
            ax.plot([-r_surf, r_surf], [wh_cm, wh_cm], color='deepskyblue', linewidth=3)
    
    ax.set_xlabel('Radius (cm)')
    ax.set_ylabel('Height (cm)')
    ax.set_title(f'Filling {geometry.name}')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.2)
    ax.axvline(x=0, color='gray', linestyle=':', alpha=0.3)
    
    # Set axis limits
    max_r = np.max(r_cm)
    ax.set_xlim(-max_r * 1.5, max_r * 1.5)
    ax.set_ylim(-1, geometry.height * 100 + 1)
    
    fig.tight_layout()
    return fig
