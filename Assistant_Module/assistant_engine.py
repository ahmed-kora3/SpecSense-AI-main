import math

class LoadCalculator:
    @staticmethod
    def calculate_total_load(appliances):
        """
        appliances is a list of dicts: [{'name': 'AC', 'power': 1500, 'quantity': 2}, ...]
        Returns total power in Watts.
        """
        total = 0
        for app in appliances:
            total += float(app.get('power', 0)) * int(app.get('quantity', 1))
        return total

    @staticmethod
    def calculate_current(total_power, voltage=220, system_type="single"):
        if voltage <= 0:
            return 0
        if system_type == "three":
            return total_power / (math.sqrt(3) * voltage)
        # single phase
        return total_power / voltage


class SafetyFactor:
    @staticmethod
    def apply_safety_margin(current, factor=1.25):
        return current * factor

class VoltageDropCalculator:
    @staticmethod
    def calculate_voltage_drop(current, length, resistance_per_meter, phases=1):
        # V_d = 2 * I * R * L (for single-phase, accounting for return path)
        multiplier = 2 if phases == 1 else 1.732
        return multiplier * current * resistance_per_meter * length

class CableSelectionEngine:
    # Based on standard rule-based selection. Mapping Current -> mm2
    rules = [
        {'max_current': 15, 'recommended_mm2': 1.5, 'resistance_per_km': 12.1, 'material': 'Copper'},
        {'max_current': 25, 'recommended_mm2': 2.5, 'resistance_per_km': 7.41, 'material': 'Copper'},
        {'max_current': 32, 'recommended_mm2': 4.0, 'resistance_per_km': 4.61, 'material': 'Copper'},
        {'max_current': 40, 'recommended_mm2': 6.0, 'resistance_per_km': 3.08, 'material': 'Copper'},
        {'max_current': 55, 'recommended_mm2': 10.0, 'resistance_per_km': 1.83, 'material': 'Copper'},
        {'max_current': 75, 'recommended_mm2': 16.0, 'resistance_per_km': 1.15, 'material': 'Copper'},
        {'max_current': 100, 'recommended_mm2': 25.0, 'resistance_per_km': 0.727, 'material': 'Copper'},
        {'max_current': 135, 'recommended_mm2': 35.0, 'resistance_per_km': 0.524, 'material': 'Copper'},
        # Extend as necessary
    ]

    @staticmethod
    def select_optimal_cable(safe_current, voltage, length, phases, max_voltage_drop_pct):
        vd_calc = VoltageDropCalculator()
        initial_cable = None
        
        for rule in CableSelectionEngine.rules:
            if safe_current <= rule['max_current']:
                # Save the first cable that meets current requirements as the initial selection
                if initial_cable is None:
                    initial_cable = rule
                    
                # Now check voltage drop for this candidate cable
                res_per_m = rule['resistance_per_km'] / 1000.0
                v_drop = vd_calc.calculate_voltage_drop(safe_current, length, res_per_m, phases=phases)
                v_drop_pct = (v_drop / voltage) * 100
                
                if v_drop_pct <= max_voltage_drop_pct:
                    return initial_cable, rule, v_drop, v_drop_pct, "OK"
        
        # If no cable satisfies both, or if current is too high for all rules
        if initial_cable is None:
            return None, {'max_current': 999, 'recommended_mm2': -1, 'error': 'Current exceeds standard single-phase residential rules in simple DB. Consult engineer.'}, 0, 0, "ERROR"
            
        # If we got here, current was fine but voltage drop exceeded limits even on the largest cable
        largest_rule = CableSelectionEngine.rules[-1]
        res_per_m = largest_rule['resistance_per_km'] / 1000.0
        v_drop = vd_calc.calculate_voltage_drop(safe_current, length, res_per_m, phases=phases)
        v_drop_pct = (v_drop / voltage) * 100
        
        return initial_cable, largest_rule, v_drop, v_drop_pct, f"WARNING: {v_drop_pct:.2f}% drop exceeds {max_voltage_drop_pct}% limit even with largest cable"

def run_assistant_pipeline(appliances, voltage, length, system_type="single", max_voltage_drop_pct=5):
    load_calc = LoadCalculator()
    total_power = load_calc.calculate_total_load(appliances)
    current = load_calc.calculate_current(total_power, voltage, system_type)
    
    saf = SafetyFactor()
    safe_current = saf.apply_safety_margin(current)
    
    # Input validation checks
    validation_warnings = []
    if system_type == "three" and voltage < 300:
        validation_warnings.append("Three Phase systems typically operate at 380V or higher. Ensure your voltage input is correct.")
    elif system_type == "single" and voltage > 250:
        validation_warnings.append("Single Phase systems typically operate under 250V. Ensure your voltage input is correct.")
    
    phases_num = 3 if system_type == "three" else 1
    
    selector = CableSelectionEngine()
    initial_cable, final_cable, v_drop, v_drop_pct, v_drop_status = selector.select_optimal_cable(
        safe_current, voltage, length, phases_num, max_voltage_drop_pct
    )
    
    return {
        'total_power_w': total_power,
        'current_a': current,
        'safe_current_a': safe_current,
        'initial_cable': initial_cable,
        'cable': final_cable,
        'voltage_drop_v': v_drop,
        'voltage_drop_pct': v_drop_pct,
        'voltage_drop_status': v_drop_status,
        'validation_warnings': validation_warnings
    }
