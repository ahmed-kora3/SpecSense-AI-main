import re

class CableValidator:
    def __init__(self):
        self.rules = {
            "valid_insulation": ["PVC", "XLPE", "EPR", "RUBBER", "LSZH"],
            "valid_sheath": ["PVC", "PE", "LSZH", "RUBBER", "HDPE", "MDPE", "LDPE"],
            "valid_armor": ["STEEL", "ALUMINUM", "COPPER", "SWA", "STA", "AWA", "ATA", "NONE"],
            "invalid_materials": ["PLASTIC", "FOAM", "GLASS", "WOOD", "PAPER", "PAINT", "WATER", "STONE"],
            "temp_range": (-40, 105)
        }
    
    def parse_float(self, val_str):
        if not val_str: return None
        nums = re.findall(r'\d+(?:\.\d+)?', str(val_str))
        if nums: return float(nums[0])
        return None

    def validate_cable(self, specs):
        violations = []
        missing_data = []
        
        # Extract Raw Values (Already Corrected by SpecCorrector)
        type_str = (specs.get('cable_type') or "").upper()
        voltage_str = (specs.get('voltage') or "").upper()
        current_str = (specs.get('current_rating') or "").upper()
        insulation_str = (specs.get('insulation') or "").upper()
        conductor_count_str = str(specs.get('conductor_count') or "")
        conductor_size_str = (specs.get('conductor_size') or "").upper()
        sheath_str = (specs.get('sheath') or "").upper()
        armor_str = (specs.get('armor') or "NONE").upper()
        temp_str = str(specs.get('operating_temperature') or "")
        resistance_str = (specs.get('insulation_resistance') or "").upper()

        # Check for explicitly UNVERIFIABLE from Corrector
        if "UNVERIFIABLE" in [type_str, voltage_str, current_str, insulation_str, conductor_size_str, temp_str]:
             missing_data.append("Contains UNVERIFIABLE fields (marked by Corrector).")

        # --- ENGINEERING VALIDATION RULES ---

        # Rule 1: Cable Type
        if "FIBER" in type_str or "OPTIC" in type_str:
            violations.append("1. Cable Type: Rejected hybrid Fiber-Optic/Power cable.")
        if not type_str or any(x in type_str for x in ["UNKNOWN", "?", "AMBIGUOUS"]):
            missing_data.append("1. Cable Type: Unknown or ambiguous.")

        # Rule 2: Voltage Rating
        if "AC" in voltage_str and "DC" in voltage_str:
            violations.append("2. Voltage: Rejected mixed AC/DC ratings.")
        if "/" in voltage_str and "V" in voltage_str:
             matches = re.findall(r'(\d+(?:\.\d+)?)\s*(k?V)', voltage_str, re.IGNORECASE)
             parsed_vs = []
             for val_str, unit in matches:
                 try:
                    v = float(val_str)
                    if 'k' in unit.lower(): v *= 1000
                    parsed_vs.append(v)
                 except: pass
             if len(parsed_vs) >= 2 and max(parsed_vs) > 0:
                 ratio = max(parsed_vs) / (min(parsed_vs) if min(parsed_vs) > 0 else 1)
                 if ratio > 50: 
                     violations.append(f"2. Voltage: Rejected mixed voltage levels '{voltage_str}'.")

        # Rule 3 & 10: Current vs Conductor Size
        current_val = self.parse_float(current_str)
        size_val = self.parse_float(conductor_size_str)
        
        if size_val is not None:
             if size_val < 0.1: 
                 violations.append(f"10. Conductor Size: Rejected unrealistic size {size_val} mm2.")
        
        if current_val and size_val:
            density = current_val / size_val
            if density > 30: 
                 violations.append(f"3. Current: {current_val}A is physically incompatible with {size_val}mm2 (Density {density:.1f} A/mm2 too high).")
            # Rule 3b: Minimum Density (Catch absurdly low ratings like 2A for 1000mm2)
            if density < 0.1:
                 violations.append(f"3b. Current: {current_val}A is too low for {size_val}mm2 (Density {density:.4f} A/mm2). Likely OCR Error.")
        
        # Rule 4: Insulation Type
        if any(bad in insulation_str for bad in self.rules["invalid_materials"]):
            violations.append(f"4. Insulation: Rejected non-electrical material '{insulation_str}'.")

        # Rule 5: Number of Conductors
        if conductor_count_str and '.' in conductor_count_str:
            violations.append(f"5. Conductors: Rejected fractional conductor count '{conductor_count_str}'.")

        # Rule 7: Armor
        if armor_str != "NONE" and armor_str not in self.rules["valid_armor"]:
             if any(bad in armor_str for bad in self.rules["invalid_materials"]):
                 violations.append(f"7. Armor: Rejected non-metallic armor '{armor_str}'.")

        # Rule 8: Operating Temperature
        temp_val = self.parse_float(temp_str)
        if temp_val is not None:
            min_t, max_t = self.rules["temp_range"]
            if not (min_t <= temp_val <= max_t):
                violations.append(f"8. Temperature: {temp_val}°C is outside realistic limit.")

        # Rule 9: Standard Cross-Sections (IEC)
        standard_sizes = [0.5, 0.75, 1.0, 1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0, 50.0, 70.0, 
                          95.0, 120.0, 150.0, 185.0, 240.0, 300.0, 400.0, 500.0, 630.0, 800.0, 1000.0]
        
        if size_val is not None:
             is_standard = any(abs(size_val - s) / s < 0.05 for s in standard_sizes)
             if not is_standard:
                 violations.append(f"9. Conductor Size: {size_val} mm2 is not a standard IEC size.")

        # Rule 10: Material Compatibility
        voltage_max = 0
        if "/" in voltage_str and "V" in voltage_str:
             matches = re.findall(r'(\d+(?:\.\d+)?)\s*(k?V)', voltage_str, re.IGNORECASE)
             parsed_vs = []
             for val_str, unit in matches:
                 try:
                    v = float(val_str)
                    if 'k' in unit.lower(): v *= 1000
                    parsed_vs.append(v)
                 except: pass
             if parsed_vs: voltage_max = max(parsed_vs)

        if voltage_max > 3300 and "PVC" in insulation_str:
            violations.append(f"10. Material: PVC Insulation cannot be used for High Voltage ({voltage_str}). Must be XLPE.")

        # Rule 11: Critical Safety for High Voltage
        # If Voltage > 1000V, Insulation MUST be verified (not None/Unknown)
        if voltage_max > 1000 and (not insulation_str or insulation_str in ["UNKNOWN", "NONE", ""]):
             violations.append(f"11. Safety: High Voltage ({voltage_str}) requires verified Insulation type. None found.")

        # Final Decision Logic
        if violations:
            status = "NOT READY"
        elif missing_data or not voltage_str: # Voltage is critical
            status = "UNVERIFIABLE"
        else:
            status = "READY"
        
        return {
            'valid': status == "READY",
            'status': status,
            'errors': violations, # Only Engineering Violations
            'missing': missing_data
        }
