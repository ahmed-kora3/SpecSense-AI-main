import os
import argparse
import json
import re
import sys
from collections import Counter

# Try importing dependencies, handle if missing
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None


# -----------------------------------------------------------------------------
# 1. INPUT HANDLER
# -----------------------------------------------------------------------------
class InputHandler:
    def __init__(self):
        pass

    def read_text(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading text file: {e}"

    def read_pdf(self, file_path):
        if not PyPDF2:
            return "Error: PyPDF2 library not installed. Cannot read PDF."
        try:
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error reading PDF: {e}"

    def read_docx(self, file_path):
        if not docx:
            return "Error: python-docx library not installed. Cannot read DOCX."
        try:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            return f"Error reading DOCX: {e}"

    def read_json(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Flatten JSON values into a string for keyword extraction
            return " ".join([str(v) for v in data.values() if v])
        except Exception as e:
            return f"Error reading JSON: {e}"

    def process_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.txt':
            return self.read_text(file_path)
        elif ext == '.pdf':
            return self.read_pdf(file_path)
        elif ext == '.docx':
            return self.read_docx(file_path)
        elif ext == '.json':
            return self.read_json(file_path)
        else:
            return None

    def load_data(self, directory):
        results = {}
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                content = self.process_file(file_path)
                if content:
                    results[file] = content
        return results


# -----------------------------------------------------------------------------
# 2. KEYWORD EXTRACTOR
# -----------------------------------------------------------------------------
class KeywordExtractor:
    def __init__(self):
        # Regex patterns for common electrical specs
        self.patterns = {
            # Updated to handle ranges like 450/750 V
            "Voltage": r'\b\d+(?:[.,/]\d+)*\s*k?V\b', 
            "Current": r'\b\d+(?:\.\d+)?\s*A\b',  # Matches 100A, 630 A
            "CrossSection": r'\b\d+(?:\.\d+)?\s*mm2\b', # Matches 120mm2
            "Cores": r'\b(?<![-+])\d{1,2}C\b|\b\d+\s*Core\b', # Matches 3C, 4 Core
            "Material": r'\b(Copper|Aluminum|XLPE|PVC|SWA|AWA)\b',
            "Conductor Type": r'\b(ACSR|AAAC|AAC|HTSL)\b'
        }
        
        # Common English stop words plus some generic technical terms that aren't keywords
        self.stop_words = {
            "the", "and", "for", "with", "that", "this", "from", "are", "was", "were", 
            "but", "not", "has", "have", "had", "will", "would", "can", "could", "should",
            "data", "sheet", "spec", "specification", "type", "rated", "nominal", "cable", "conductor"
        }

    def preprocess_text(self, text):
        """
        Pre-process OCR text to fix common character substitutions.
        """
        # Fix common corrupted words
        text = re.sub(r'C[@a]b[l1][e3]', 'Cable', text, flags=re.IGNORECASE)
        text = re.sub(r'V[0o]ltage', 'Voltage', text, flags=re.IGNORECASE)
        text = re.sub(r'C[ou]rr[e3]nt', 'Current', text, flags=re.IGNORECASE)
        text = re.sub(r'C[0o]pp[\s]*[e3]r', 'Copper', text, flags=re.IGNORECASE)
        text = re.sub(r'P[0o]w[e3]r', 'Power', text, flags=re.IGNORECASE)
        text = re.sub(r'St[e3][e3][l1]', 'Steel', text, flags=re.IGNORECASE)
        text = re.sub(r'W[i1]r[e3]', 'Wire', text, flags=re.IGNORECASE)
        text = re.sub(r'Arm[0o]r', 'Armor', text, flags=re.IGNORECASE)
        
        # Fix numbers: O -> 0, S -> 5 (in numeric contexts)
        text = re.sub(r'(\d)O(\d)', r'\g<1>0\2', text)
        text = re.sub(r'(\d)S(\d)', r'\g<1>5\2', text)
        text = re.sub(r'(\d)O\s*V', r'\g<1>0 V', text)
        text = re.sub(r'(\d)S\s*V', r'\g<1>5 V', text)
        text = re.sub(r'O(\d)', r'0\1', text)
        text = re.sub(r'S(\d)', r'5\1', text)
        
        # Clean extra spaces in numbers
        text = re.sub(r'(\d)\s+(\d)\s*A\b', r'\1\2A', text)
        
        return text

    def extract_keywords(self, text):
        # Pre-process text to fix OCR errors
        text = self.preprocess_text(text)
        
        extracted = {}
        all_keywords = []

        # 1. Extract specific patterns
        for label, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Clean up matches
                clean_matches = []
                for m in matches:
                    if isinstance(m, tuple):
                        m = m[0]
                    clean_matches.append(m.strip())
                
                if clean_matches:
                    extracted[label] = list(set(clean_matches)) # Unique matches
                    all_keywords.extend(clean_matches)

        # 2. Generate Top Terms (Frequency Analysis)
        # Find words with 3+ chars
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter stop words and very short words
        filtered_words = [
            w for w in words 
            if w not in self.stop_words and len(w) > 3
        ]
        
        # Get top 5 most common terms
        common_terms = Counter(filtered_words).most_common(5)
        extracted["Top Terms"] = [term for term, count in common_terms]

        return extracted


# -----------------------------------------------------------------------------
# 3. CABLE CLASSIFIER
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# 3. CABLE CLASSIFIER
# -----------------------------------------------------------------------------
class CableClassifier:
    def __init__(self):
        # Categories defined in 'Cabels Category.pdf'
        self.categories = {
            "HTLS Conductors": [
                "htls", "htsl", "high temperature low sag", "accc", "acss", "tacsr", "stacir", "gap type", "invar"
            ],
            "Overhead Conductors": [
                "overhead", "bare copper", "aac", "aaac", "acsr", "abc", "areal bundled", "transmission line"
            ],
            "High & Extra High Voltage Cables": [
                "high voltage", "extra high voltage", "ehv", "hv cable", "66kv", "132kv", "220kv", "400kv", "500kv"
            ],
            "Medium Voltage Cables": [
                "medium voltage", "mv cable", "6.6kv", "11kv", "22kv", "33kv"
            ],
            "Low Voltage Cables": [
                "low voltage", "lv cable", "0.6/1kv", "1.8/3kv", "pvc insulated"
            ]
        }

    def classify(self, text):
        text_lower = text.lower()
        detected_categories = []

        # 1. Check Specific Conductor Types first (Text-based)
        # These are usually mutually exclusive with general "Cables" if they appear explicitly
        for cat in ["HTLS Conductors", "Overhead Conductors"]:
            for keyword in self.categories[cat]:
                if keyword in text_lower:
                    detected_categories.append(cat)
                    break 

        # 2. Logic-based classification (Voltage Thresholds per PDF)
        # PDF Definitions:
        # Low Voltage: up to 1.8/3 kV (max ~3000V)
        # Medium Voltage: up to 18/30 kV (max ~30000V)
        # High Voltage: up to 500 kV (>30000V)
        
        # First, preprocess text to fix OCR errors
        text = re.sub(r'(\d)O(\d)', r'\g<1>0\2', text)
        text = re.sub(r'(\d)S(\d)', r'\g<1>5\2', text)
        text = re.sub(r'(\d)O\s*V', r'\g<1>0 V', text)
        text = re.sub(r'(\d)S\s*V', r'\g<1>5 V', text)
        
        # Match voltage patterns including ranges like 450/750V, 0.6/1kV
        # This captures the SECOND number in a range (which is usually higher)
        voltage_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:/\s*(\d+(?:\.\d+)?))?\s*(k?V)\b', text, re.IGNORECASE)
        max_voltage = 0
        
        for match in voltage_matches:
            try:
                # match is a tuple: (first_num, second_num_or_empty, unit)
                first_num = float(match[0]) if match[0] else 0
                second_num = float(match[1]) if match[1] else 0
                unit = match[2]
                
                # Take the higher of the two numbers
                val = max(first_num, second_num)
                
                if unit.lower() == 'kv':
                    val *= 1000
                if val > max_voltage:
                    max_voltage = val
            except:
                pass
        
        if max_voltage > 0:
            if max_voltage <= 3000:
                 detected_categories.append("Low Voltage Cables")
            elif 3000 < max_voltage <= 30000:
                 detected_categories.append("Medium Voltage Cables")
            else:
                 detected_categories.append("High & Extra High Voltage Cables")

        # 3. Fallback to basic keywords if no voltage/type found
        if not detected_categories:
            for cat in ["High & Extra High Voltage Cables", "Medium Voltage Cables", "Low Voltage Cables"]:
                for keyword in self.categories[cat]:
                    if keyword in text_lower:
                        detected_categories.append(cat)
                        break

        if not detected_categories:
            return "Uncategorized"
        
        # Priority Logic: If specific conductor type is found, return that.
        # If multiple Voltage categories found (unlikely with max logic), take the highest?
        # Let's return the most specific one.
        
        unique = sorted(list(set(detected_categories)))
        # Filter: If "Overhead" or "HTLS" is present, usually that's the primary category.
        priority = ["HTLS Conductors", "Overhead Conductors", "High & Extra High Voltage Cables", "Medium Voltage Cables", "Low Voltage Cables"]
        
        for p in priority:
            if p in unique:
                return p # Return the highest priority match
                
        return unique[0]


# -----------------------------------------------------------------------------
# 4. MAIN EXECUTION
# -----------------------------------------------------------------------------
def run_analysis(input_path, output_path=None):
    """
    Main function to run the analysis, callable from other scripts.
    Returns the results dictionary.
    """
    # Validation
    if not os.path.exists(input_path):
        print(f"Error: Path '{input_path}' does not exist.")
        return None

    handler = InputHandler()
    extractor = KeywordExtractor()
    classifier = CableClassifier()
    
    results = {}

    if os.path.isfile(input_path):
        files = {os.path.basename(input_path): handler.process_file(input_path)}
    elif os.path.isdir(input_path):
        files = handler.load_data(input_path)
    else:
        print(f"Error: Invalid path type for {input_path}")
        return None

    print(f"Processing {len(files)} files from '{input_path}'...")
    print("-" * 40)

    for filename, content in files.items():
        if content and not content.startswith("Error"):
            keywords = extractor.extract_keywords(content)
            category = classifier.classify(content)
            
            results[filename] = {
                "Category": category,
                "Keywords": keywords
            }
            
            # Readable Output Block
            print(f"KEYWORD GEN: FILE: {filename}")
            print(f"KEYWORD GEN: CATEGORY: {category}")
            print("KEYWORD GEN: EXTRACTED DATA:")
            for key, values in keywords.items():
                if key == "Top Terms":
                     print(f"  {key}: {', '.join(values)}")
                else:
                    # Values might be a list, join them
                    val_str = ", ".join(values) if isinstance(values, list) else str(values)
                    print(f"  {key}: {val_str}")
            print("-" * 40)
        else:
            print(f"Skipping {filename} (empty, error, or unsupported)")

    if output_path:
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=4)
            print(f"Results saved to {output_path}")
        except Exception as e:
            print(f"Error saving output: {e}")
            
    return results

def main():
    parser = argparse.ArgumentParser(description="Keyword Generation and Cable Classification Tool (Single File)")
    # Make input_path optional with a default of 'data/'
    parser.add_argument("input_path", nargs='?', default="data/", help="Path to file or directory to process (default: data/)")
    parser.add_argument("--output", help="Path to save JSON output", default=None)
    
    args = parser.parse_args()
    run_analysis(args.input_path, args.output)

if __name__ == "__main__":
    main()
