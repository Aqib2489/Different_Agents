"""
Deterministic calculation engine for RC beam design.
All numerical calculations are performed here - agents only interpret results.
"""

import math
from typing import Dict, List, Tuple


class BeamCalculations:
    """Pure calculation engine - no AI, no interpretation, just math"""
    
    @staticmethod
    def apply_load_combinations(dead_load: float, live_load: float, 
                                combinations: List[Dict]) -> Dict[str, float]:
        """
        Apply NBCC load combinations to get factored loads.
        
        Args:
            dead_load: Dead load in kN/m
            live_load: Live load in kN/m
            combinations: List of combination rules from NBCC agent
            
        Returns:
            Dictionary with governing factored loads
        """
        results = {}
        max_load = 0
        governing_combo = ""
        
        for combo in combinations:
            # Expected format: {'name': 'ULS-1', 'dead_factor': 1.4, 'live_factor': 1.5}
            factored_load = (combo.get('dead_factor', 0) * dead_load + 
                           combo.get('live_factor', 0) * live_load)
            results[combo['name']] = factored_load
            
            if factored_load > max_load:
                max_load = factored_load
                governing_combo = combo['name']
        
        return {
            'all_combinations': results,
            'governing_factored_load': max_load,
            'governing_combination': governing_combo
        }
    
    @staticmethod
    def calculate_bending_moment(factored_load: float, span: float, 
                                 support_condition: str) -> float:
        """
        Calculate maximum bending moment based on support conditions.
        
        Args:
            factored_load: Factored load in kN/m
            span: Beam span in meters
            support_condition: 'simply_supported', 'fixed', 'continuous'
            
        Returns:
            Maximum bending moment in kN.m
        """
        if support_condition == 'simply_supported':
            # M = wL²/8
            return (factored_load * span**2) / 8
        elif support_condition == 'fixed':
            # M = wL²/12 (fixed both ends)
            return (factored_load * span**2) / 12
        elif support_condition == 'continuous':
            # M = wL²/10 (continuous beam approximation)
            return (factored_load * span**2) / 10
        else:
            # Default to simply supported
            return (factored_load * span**2) / 8
    
    @staticmethod
    def calculate_shear_force(factored_load: float, span: float, 
                             support_condition: str) -> float:
        """
        Calculate maximum shear force based on support conditions.
        
        Args:
            factored_load: Factored load in kN/m
            span: Beam span in meters
            support_condition: Support condition type
            
        Returns:
            Maximum shear force in kN
        """
        if support_condition in ['simply_supported', 'fixed']:
            # V = wL/2
            return (factored_load * span) / 2
        elif support_condition == 'continuous':
            # V = 0.6 * wL (continuous beam approximation)
            return 0.6 * factored_load * span
        else:
            return (factored_load * span) / 2
    
    @staticmethod
    def design_flexural_reinforcement(moment: float, width: float, depth: float,
                                     cover: float, fc_prime: float, fy: float,
                                     phi_c: float = 0.65, phi_s: float = 0.85) -> Dict:
        """
        Design flexural reinforcement for rectangular beam section.
        
        Args:
            moment: Factored moment in kN.m
            width: Beam width in mm
            depth: Total beam depth in mm
            cover: Concrete cover in mm
            fc_prime: Concrete compressive strength in MPa
            fy: Steel yield strength in MPa
            phi_c: Resistance factor for concrete
            phi_s: Resistance factor for steel
            
        Returns:
            Dictionary with reinforcement details
        """
        # Effective depth
        d = depth - cover - 20  # Assuming 20mm bar diameter + stirrup
        
        # Convert moment to N.mm
        M_f = moment * 1e6
        
        # Calculate required area of steel
        # Using rectangular stress block
        # Mr = φs * As * fy * (d - a/2)
        # a = (φs * As * fy) / (α1 * φc * fc' * b)
        # α1 = 0.85 - 0.0015*fc' >= 0.67 for NBCC
        alpha1 = max(0.85 - 0.0015 * fc_prime, 0.67)
        
        # Simplified approach: assume a ≈ 0.1*d initially
        a_assumed = 0.1 * d
        
        # Required steel area
        As_req = M_f / (phi_s * fy * (d - a_assumed / 2))
        
        # Recalculate 'a' with computed As
        a_actual = (phi_s * As_req * fy) / (alpha1 * phi_c * fc_prime * width)
        
        # Iterate once for better accuracy
        As_req = M_f / (phi_s * fy * (d - a_actual / 2))
        a_actual = (phi_s * As_req * fy) / (alpha1 * phi_c * fc_prime * width)
        
        # Check minimum reinforcement
        As_min = max(0.2 * math.sqrt(fc_prime) * width * d / fy,
                     1.4 * width * d / fy)
        
        As_required = max(As_req, As_min)
        
        # Calculate reinforcement ratio
        rho = As_required / (width * d)
        
        # Check balanced condition (simplified)
        rho_balanced = 0.85 * alpha1 * phi_c * fc_prime * 0.0035 / (phi_s * fy * (0.0035 + fy / 200000))
        rho_max = 0.75 * rho_balanced  # NBCC limit
        
        return {
            'As_required': As_required,  # mm²
            'As_min': As_min,  # mm²
            'effective_depth': d,  # mm
            'stress_block_depth': a_actual,  # mm
            'reinforcement_ratio': rho,
            'rho_max': rho_max,
            'is_over_reinforced': rho > rho_max,
            'alpha1': alpha1
        }
    
    @staticmethod
    def select_bar_arrangement(As_required: float, width: float) -> Dict:
        """
        Select practical bar arrangement.
        
        Args:
            As_required: Required steel area in mm²
            width: Beam width in mm
            
        Returns:
            Dictionary with bar selection
        """
        # Standard bar sizes (diameter in mm and area in mm²)
        bars = {
            10: 78.5,
            15: 177,
            20: 314,
            25: 491,
            30: 707,
            35: 962
        }
        
        # Try different bar combinations
        best_config = None
        min_waste = float('inf')
        
        for bar_size, bar_area in bars.items():
            num_bars = math.ceil(As_required / bar_area)
            
            # Check if bars fit (assume 25mm clear spacing minimum)
            required_width = num_bars * bar_size + (num_bars - 1) * 25 + 2 * 25  # spacing + cover
            
            if required_width <= width:
                As_provided = num_bars * bar_area
                waste = As_provided - As_required
                
                if waste < min_waste:
                    min_waste = waste
                    best_config = {
                        'bar_diameter': bar_size,
                        'num_bars': num_bars,
                        'As_provided': As_provided,
                        'bar_area_each': bar_area
                    }
        
        if best_config is None:
            # Use two layers if can't fit in one
            best_config = {
                'bar_diameter': 25,
                'num_bars': math.ceil(As_required / bars[25]),
                'As_provided': math.ceil(As_required / bars[25]) * bars[25],
                'bar_area_each': bars[25],
                'note': 'Multiple layers required'
            }
        
        return best_config
    
    @staticmethod
    def design_shear_reinforcement(shear_force: float, width: float, depth: float,
                                  cover: float, fc_prime: float, fy_v: float,
                                  phi_c: float = 0.65) -> Dict:
        """
        Design transverse reinforcement for shear.
        
        Args:
            shear_force: Factored shear force in kN
            width: Beam width in mm
            depth: Total depth in mm
            cover: Concrete cover in mm
            fc_prime: Concrete strength in MPa
            fy_v: Stirrup yield strength in MPa
            phi_c: Resistance factor
            
        Returns:
            Dictionary with shear reinforcement details
        """
        d = depth - cover - 20
        V_f = shear_force * 1000  # Convert to N
        
        # Concrete shear resistance (simplified)
        lambda_factor = 1.0  # Normal density concrete
        V_c = phi_c * 0.2 * lambda_factor * math.sqrt(fc_prime) * width * d
        
        # Required shear reinforcement
        V_s_required = V_f - V_c
        
        # Stirrup configuration (assume 2-leg stirrups, 10mm diameter)
        stirrup_diameter = 10
        A_v = 2 * math.pi * (stirrup_diameter / 2)**2  # mm² for 2-leg stirrup
        
        if V_s_required <= 0:
            # Minimum shear reinforcement
            s_required = 0.06 * math.sqrt(fc_prime) * width / (fy_v * 1)
            s_max = min(0.7 * d, 600)  # NBCC limits
            spacing = min(s_max, 300)  # Use 300mm as practical max
            
            return {
                'V_c': V_c / 1000,  # kN
                'V_s_required': 0,
                'stirrup_diameter': stirrup_diameter,
                'stirrup_legs': 2,
                'A_v': A_v,
                'spacing': spacing,
                'spacing_max': s_max,
                'requires_stirrups': False,
                'note': 'Minimum reinforcement'
            }
        else:
            # Calculate required spacing
            # V_s = (A_v * fy_v * d) / s
            s_required = (A_v * fy_v * d) / V_s_required
            
            # Maximum spacing limits
            s_max = min(0.7 * d, 600)  # mm
            
            # Practical spacing (round down to nearest 25mm)
            spacing = math.floor(min(s_required, s_max) / 25) * 25
            spacing = max(spacing, 75)  # Minimum 75mm for practical construction
            
            return {
                'V_c': V_c / 1000,  # kN
                'V_s_required': V_s_required / 1000,  # kN
                'stirrup_diameter': stirrup_diameter,
                'stirrup_legs': 2,
                'A_v': A_v,
                'spacing': spacing,
                'spacing_max': s_max,
                's_required': s_required,
                'requires_stirrups': True,
                'note': 'Shear reinforcement required'
            }
    
    @staticmethod
    def check_serviceability(span: float, depth: float, 
                            support_condition: str) -> Dict:
        """
        Check span-to-depth ratio for deflection control.
        
        Args:
            span: Beam span in meters
            depth: Total depth in mm
            support_condition: Support condition type
            
        Returns:
            Dictionary with serviceability checks
        """
        span_mm = span * 1000
        
        # NBCC span-to-depth limits (simplified)
        limits = {
            'simply_supported': 20,
            'continuous': 26,
            'fixed': 28,
            'cantilever': 8
        }
        
        limit_ratio = limits.get(support_condition, 20)
        actual_ratio = span_mm / depth
        
        # Check deflection
        passes_deflection = actual_ratio <= limit_ratio
        
        return {
            'span_to_depth_actual': actual_ratio,
            'span_to_depth_limit': limit_ratio,
            'passes_deflection_check': passes_deflection,
            'support_condition': support_condition,
            'recommendation': 'OK' if passes_deflection else 'Increase depth or check detailed deflection'
        }
