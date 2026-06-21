"""
Material properties for acoustic simulation.
"""
import numpy as np


class Air:
    """Properties of air at standard conditions."""
    
    def __init__(self, temperature_celsius: float = 20.0):
        """
        Initialize air properties.
        
        Args:
            temperature_celsius: Temperature in Celsius (default: 20°C)
        """
        self.temperature = temperature_celsius
        self.speed_of_sound = 331.3 + 0.606 * temperature_celsius  # m/s
        self.density = 1.225 * (273.15 / (273.15 + temperature_celsius))  # kg/m³
        self.impedance = self.density * self.speed_of_sound  # Pa·s/m
    
    def wavenumber(self, frequency: float) -> float:
        """Calculate wavenumber k = ω/c = 2πf/c."""
        return 2.0 * np.pi * frequency / self.speed_of_sound
    
    def wavelength(self, frequency: float) -> float:
        """Calculate wavelength λ = c/f."""
        return self.speed_of_sound / frequency
