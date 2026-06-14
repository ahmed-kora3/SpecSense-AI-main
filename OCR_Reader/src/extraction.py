import re

class SpecificationExtractor:
    def __init__(self):
        # English-only patterns
        self.patterns = {
            "cable_type": {
                # Copper, C0pper, COpp er, etc.
                "en": r"\b(C[o0]pp[\s]*[e3]r|Cu|Aluminium|Aluminum|Al)\b\s*(?:C[@a]ble|Conductor)?"
            },
            "voltage": {
                # 450/750V, 450 / 7S0 V, 0.6/1kV
                "en": r"(\d[\d\s\.]*[/]?[\d\sS]*\s*[kK]?[vV])"
            },
            "current_rating": {
                 # 32 A, 3 2 A
                 "en": r"(\d[\d\s]*\s*(?:Amps?|A)\b)"
            },
            "insulation": {
                "en": r"(XLPE|PVC)"
            },
            "conductor_count": {
                "en": r"(\d+)\s*(?:Core|Cores|x)"
            },
            "conductor_size": { 
                # 6 mm2, 6m m 2, 6  mm2
                "en": r"(\d+(?:[\s]*[xX][\s]*\d+)?[\s]*m[\s]*m[h]?[\s]*[2²\?]?)"
            },
            "sheath": {
                "en": r"(PVC|HDPE|LDPE|Lead|LAZH|LSOH|MDPE|EPR|PUR|TPU|Neoprene|Rubber|LSZH)\s*(?:Sheath|Jacket)?"
            },
            "operating_temperature": {
                # 40 C, 4O C, 4 0 C
                "en": r"(\d+(?:[\s]*[O0\d]+)?[\s]*(?:°|\*|deg|degrees)?[\s]*C)"
            },
            "insulation_resistance": {
                # 20 MO.km, 20M O.km
                "en": r"(\d+[\s]*M?[O\u03a9][\s]*[\.]?k?m)"
            },
            "armor": {
                # Steel Wire Armor, Steel Tape Armor, SWA, STA (word boundaries)
                "en": r"(Stee[l1][\s]*[WT][l1Iae3p]+[\s]*Armo[r0x]|\bSWA\b|\bSTA\b|SWA|AWA|ATA|GSWA|GSTA|CWA|BWA)"
            }
        }

    def preprocess_text(self, text):
        """
        Pre-process OCR text to fix common character substitutions.
        This cleans the text BEFORE extraction patterns are applied.
        """
        # Common OCR substitutions in words (not in numbers)
        word_fixes = {
            '@': 'a',
            '0': 'o',  # Will be handled carefully
            '1': 'l',  # In words only
            '3': 'e',
            '5': 's',
        }
        
        # Fix common corrupted words
        text = re.sub(r'C[@a]b[l1][e3]', 'Cable', text, flags=re.IGNORECASE)
        text = re.sub(r'V[0o]ltage', 'Voltage', text, flags=re.IGNORECASE)
        text = re.sub(r'C[ou]rr[e3]nt', 'Current', text, flags=re.IGNORECASE)
        text = re.sub(r'R[@a]t[i1]ng', 'Rating', text, flags=re.IGNORECASE)
        text = re.sub(r'Insu[l1]at[i1][0o]n', 'Insulation', text, flags=re.IGNORECASE)
        text = re.sub(r'C[0o]ndu[\s]*ct[0o]r', 'Conductor', text, flags=re.IGNORECASE)
        text = re.sub(r'Sh[e3]ath', 'Sheath', text, flags=re.IGNORECASE)
        text = re.sub(r'Arm[0o]r', 'Armor', text, flags=re.IGNORECASE)
        text = re.sub(r'[0o]p[e3]rat[i1]ng', 'Operating', text, flags=re.IGNORECASE)
        text = re.sub(r'T[e3]mp[\s]*[e3]ratur[e3]', 'Temperature', text, flags=re.IGNORECASE)
        text = re.sub(r'R[e3]s[i1]stanc[e3]', 'Resistance', text, flags=re.IGNORECASE)
        text = re.sub(r'C[0o]pp[\s]*[e3]r', 'Copper', text, flags=re.IGNORECASE)
        text = re.sub(r'P[0o]w[e3]r', 'Power', text, flags=re.IGNORECASE)
        text = re.sub(r'c[0o]r[e3]s?', 'cores', text, flags=re.IGNORECASE)
        text = re.sub(r'St[e3][e3][l1]', 'Steel', text, flags=re.IGNORECASE)
        text = re.sub(r'W[i1]r[e3]', 'Wire', text, flags=re.IGNORECASE)
        
        # Fix numbers: O -> 0, S -> 5 (in numeric contexts like voltage)
        # Pattern: digit followed by O or S followed by digit or V
        text = re.sub(r'(\d)O(\d)', r'\g<1>0\2', text)
        text = re.sub(r'(\d)S(\d)', r'\g<1>5\2', text)
        text = re.sub(r'(\d)O\s*V', r'\g<1>0 V', text)
        text = re.sub(r'(\d)S\s*V', r'\g<1>5 V', text)
        text = re.sub(r'O(\d)', r'0\1', text)  # O at start of number
        text = re.sub(r'S(\d)', r'5\1', text)  # S at start of number
        
        # Clean extra spaces in numbers: "3 2 A" -> "32A"
        text = re.sub(r'(\d)\s+(\d)\s*A\b', r'\1\2A', text)
        
        return text

    def extract_specs(self, text):
        """
        Extract specifications from full text (English Only).
        """
        # Pre-process text to fix OCR errors
        text = self.preprocess_text(text)
        
        specs = {}
        for key, lang_patterns in self.patterns.items():
            specs[key] = None
            
            # Search English
            match_en = re.search(lang_patterns["en"], text, re.IGNORECASE)
            if match_en:
                # If we have groups, use group 1, unless it's the whole match we want
                if len(match_en.groups()) > 0:
                     specs[key] = match_en.group(1)
                else:
                     specs[key] = match_en.group(0)
        
        return self.clean_specs(specs)

    def clean_specs(self, specs):
        """
        Clean and correct extracted data.
        """
        # voltage correction logic
        if specs.get("voltage"):
            val = specs["voltage"]
            # Remove spaces
            val = val.replace(" ", "")
            # Fix S -> 5
            val = val.replace("S", "5").replace("s", "5")
            
            if "6" in val and "v" in val.lower() and ("1000" in val or "1k" in val):
                 specs["voltage"] = "600/1000V"
            # Attempt to normalize 450/750
            if "450" in val and "750" in val:
                specs["voltage"] = "450/750V"
            else:
                specs["voltage"] = val
        
        # conductor/size correction
        if specs.get("conductor_size"):
            val = specs["conductor_size"]
            val = val.replace(" ", "")
            val = val.replace("mh", "mm").replace("?", "2")
            if "mm" in val and not val.endswith("2"): # Append 2 if missing (e.g. 6mm -> 6mm2)
                 val += "2"
            specs["conductor_size"] = val

        # current rating correction
        if specs.get("current_rating"):
            val = specs["current_rating"]
            val = val.replace(" ", "")
            specs["current_rating"] = val

        # armor correction
        if specs.get("armor"):
             val = specs["armor"]
             import re
             if re.search(r"Stee[l1]", val, re.IGNORECASE):
                 specs["armor"] = "Steel Wire Armor"
             else:
                 specs["armor"] = val.replace("Armox", "Armor").replace("armox", "armor")
        
        # cable type cleanup
        if specs.get("cable_type"):
            val = specs["cable_type"].lower()
            if ("c" in val and ("p" in val or "o" in val) and "r" in val) or "copper" in val: # Loose check for copper
                specs["cable_type"] = "Copper"
            elif "al" in val or "alum" in val:
                specs["cable_type"] = "Aluminum"

        # sheath cleanup
        if specs.get("sheath"):
             val = specs["sheath"].upper()
             if "PVC" in val: specs["sheath"] = "PVC"
             elif "HDPE" in val: specs["sheath"] = "HDPE"

        # resistance cleanup (OCR often reads Omega as O or 0)
        if specs.get("insulation_resistance"):
             specs["insulation_resistance"] = specs["insulation_resistance"].replace("O", "Ω").replace(" ", "")

        return specs


# =============================================================================
# POST-OCR CORRECTION MODULE
# =============================================================================
class SpecCorrector:
    """
    Expert Post-OCR Correction Module.
    Normalizes units, expands abbreviations, and formats values before validation.
    Handles 'NxS' splitting and strict unit enforcement.
    """
    def __init__(self):
        self.corrections_log = []

    def log(self, field, original, corrected, reason):
        if str(original) != str(corrected):
            self.corrections_log.append(f"{field}: Changed '{original}' to '{corrected}' ({reason})")

    def correct_voltage(self, val):
        if not val: return None
        orig = val
        # Normalize spacing: 0.6/1kV -> 0.6/1 kV
        val = re.sub(r'(\d)(k?V)', r'\1 \2', str(val), flags=re.IGNORECASE)
        # Ensure 'kV' or 'V' casing
        val = val.replace("kv", "kV").replace("KV", "kV")
        
        if orig != val:
            self.log("Voltage", orig, val, "Formatting")
        return val

    def correct_temperature(self, val):
        if not val: return None
        orig = val
        val = str(val).strip()
        
        # Fix "90"" -> 90 C
        val = val.replace('"', '').replace("''", "")
        
        # Remove internal spaces in digits "4 0" -> "40"
        # Match digits separated by space, but not separate ranges "40 90"
        # If it looks like "d d C", it's likely "dd C"
        if re.search(r'\d\s+\d', val):
            val_clean = re.sub(r'(\d)\s+(?=\d)', r'\1', val)
            if val_clean != val:
                val = val_clean
        
        # Specific fix for "4 c" -> UNVERIFIABLE unless clear context
        # User reported "4 c" should be "40". OCR likely lost the 0.
        # Heuristic: If single digit d (3-9), assume d0.
        match_single = re.match(r'^(\d)\s*c$', val, re.IGNORECASE)
        if match_single:
            digit = int(match_single.group(1))
            if 3 <= digit <= 9:
                new_val = f"{digit}0°C"
                self.log("Temperature", orig, new_val, "Heuristic Repair (Truncated Zero)")
                return new_val
            else:
                self.log("Temperature", orig, "UNVERIFIABLE", "Ambiguous Single Digit")
                return "UNVERIFIABLE" 
            
        # Standardize "C" to "°C"
        if (val.lower().endswith("c") or val.lower().endswith("c.")) and "°" not in val:
            val = re.sub(r'(\d+)\s*[cCx]?\.?$', r'\1°C', val, flags=re.IGNORECASE)
            
        if orig != val:
            self.log("Temperature", orig, val, "Formatting")
        return val

    def correct_units_generic(self, val):
         # Mm -> mm
         if not val: return val
         val = str(val).replace("Mm", "mm").replace("mM", "mm")
         return val

    def correct_size_and_cores(self, specs):
        """
        Handle CRITICAL PARSING RULE A: NxS mm2
        Check if conductor_size contains the Core count (e.g. "4x16mm2")
        """
        size_val = specs.get('conductor_size')
        cores_val = specs.get('conductor_count')
        
        if not size_val: return specs
        
        # Regex for N x S pattern in size string
        # e.g. "4x16", "4 x 16", "3x50+2x25" (ignoring complex for now, focus on simple NxS)
        match = re.match(r'^\s*(\d+)\s*[xX]\s*(\d+(?:\.\d+)?)\s*(?:mm[2²]?)?', str(size_val), re.IGNORECASE)
        
        if match:
            n_extracted = match.group(1)
            s_extracted = match.group(2)
            
            # Logic: Parsing "4x16mm2" -> Cores=4, Size=16
            # User Rule: "NEVER interpret N as the conductor size"
            
            new_size = f"{s_extracted} mm²"
            
            # Update Size
            if size_val != new_size:
                self.log("Conductor Size", size_val, new_size, "NxS Split (Size)")
                specs['conductor_size'] = new_size
                
            # Update Cores (Override or Fill)
            if not cores_val or str(cores_val) != n_extracted:
                self.log("Conductor Count", cores_val, n_extracted, "NxS Split (Cores)")
                specs['conductor_count'] = int(n_extracted)
                
        else:
            # Normal normalization for size if no 'x'
            # 16mm2 -> 16 mm²
            clean_size = size_val
            clean_size = re.sub(r'(\d)\s*mm2', r'\1 mm²', str(clean_size), flags=re.IGNORECASE)
            clean_size = re.sub(r'(\d)\s*mm²', r'\1 mm²', clean_size) # verify space
            clean_size = self.correct_units_generic(clean_size)
            
            if size_val != clean_size:
                 self.log("Conductor Size", size_val, clean_size, "Unit Normalization")
                 specs['conductor_size'] = clean_size
                 
        return specs

    def correct_armor(self, val):
        if not val: return None
        orig = val
        val = str(val).strip()
        mapping = {
            "AWA": "Aluminum Wire Armor",
            "SWA": "Steel Wire Armor",
            "STA": "Steel Tape Armor",
            "ATA": "Aluminum Tape Armor"
        }
        if val.upper() in mapping:
            val = mapping[val.upper()]
        
        if orig != val:
            self.log("Armor", orig, val, "Expansion")
        return val

    def correct_resistance(self, val):
        if not val: return None
        orig = val
        val = str(val)
        # 100MΩkm -> 100 MΩ·km
        val = val.replace("MΩkm", " MΩ·km").replace("MΩ km", " MΩ·km")
        # Ensure space
        val = re.sub(r'(\d)(MΩ)', r'\1 \2', val)
        
        if orig != val:
            self.log("Resistance", orig, val, "Unit Formatting")
        return val

    def correct_all(self, specs):
        new_specs = specs.copy()
        self.corrections_log = []

        # 1. Complex dependency corrections (NxS)
        new_specs = self.correct_size_and_cores(new_specs)

        # 2. Individual fields
        if 'voltage' in new_specs:
            new_specs['voltage'] = self.correct_voltage(new_specs['voltage'])
            
        if 'armor' in new_specs:
            new_specs['armor'] = self.correct_armor(new_specs['armor'])
            
        if 'insulation_resistance' in new_specs:
            new_specs['insulation_resistance'] = self.correct_resistance(new_specs['insulation_resistance'])
            
        if 'operating_temperature' in new_specs:
           new_specs['operating_temperature'] = self.correct_temperature(new_specs['operating_temperature'])

        return new_specs, self.corrections_log
