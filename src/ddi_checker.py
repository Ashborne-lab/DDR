import pandas as pd
from itertools import combinations
import os
import re
from difflib import get_close_matches
from typing import List, Dict, Set

class DDIManager:
    """
    Production-ready Drug-Drug Interaction Manager.
    Handles Indian medicines database with robust validation.
    """
    
    def __init__(self, data_dir='data', ddi_file='drug_interactions.csv', medicine_file='medicines_global.csv'):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ddi_path = os.path.join(base_path, data_dir, ddi_file)
        self.med_path = os.path.join(base_path, data_dir, medicine_file)
        
        self.interaction_map = {}
        self.brand_to_generic = {}
        self._generic_cache = {}
        self.all_known_drugs = set()  # Combined set of all drugs
        
        print("🔄 Initializing DDI Manager...")
        self._load_interactions()
        self._load_brand_map()
        print(f"✅ DDI Manager Ready: {len(self.brand_to_generic)} brands, {len(self.interaction_map)} interactions")

    def _clean_composition(self, raw_comp: str) -> List[str]:
        """
        Extract clean generic names from composition string.
        Handles complex Indian medicine formats.
        """
        if not raw_comp or str(raw_comp).lower() == 'nan':
            return []
        
        comp = str(raw_comp).lower()
        
        # Remove pharmacopeia standards
        comp = re.sub(r'\b(i\.?p\.?|b\.?p\.?|u\.?s\.?p\.?)\b', '', comp, flags=re.IGNORECASE)
        
        # Remove equivalence statements
        comp = re.sub(r'(?:equivalent|eq\.?)\s*to\s+\w+', '', comp, flags=re.IGNORECASE)
        
        # Remove all dosage information
        comp = re.sub(r'\d+\.?\d*\s*(mg|ml|g|mcg|iu|%|gm|microgram)', '', comp, flags=re.IGNORECASE)
        
        # Remove parentheses and brackets
        comp = re.sub(r'[\(\)\[\]]', ' ', comp)
        
        # Split by separators
        parts = re.split(r'[+/,;]', comp)
        
        generics = []
        for part in parts:
            part = part.strip()
            # Remove special characters
            part = re.sub(r'[^\w\s]', '', part)
            # Normalize whitespace
            part = ' '.join(part.split())
            
            # Validation
            if len(part) < 3 or part.isdigit():
                continue
            
            # Skip filler words
            fillers = {'and', 'with', 'plus', 'in', 'as', 'of', 'or', 'the', 'a', 'an'}
            if part.lower() in fillers:
                continue
            
            generics.append(part.lower())
        
        return generics

    def _load_interactions(self):
        """Load DDI database."""
        try:
            print(f"📂 Loading interactions from {os.path.basename(self.ddi_path)}...")
            df = pd.read_csv(self.ddi_path, on_bad_lines='skip')
            df.columns = [c.strip().lower() for c in df.columns]
            
            # Find columns
            cols = list(df.columns)
            drug_a_col = next((c for c in cols if any(kw in c for kw in ['drug1', 'drug_1', 'drug 1', 'druga'])), cols[0])
            drug_b_col = next((c for c in cols if any(kw in c for kw in ['drug2', 'drug_2', 'drug 2', 'drugb'])), cols[1])
            desc_col = next((c for c in cols if any(kw in c for kw in ['interaction', 'description', 'effect'])), cols[2] if len(cols) > 2 else cols[1])
            
            loaded = 0
            for _, row in df.iterrows():
                try:
                    d1 = str(row[drug_a_col]).strip().lower()
                    d2 = str(row[drug_b_col]).strip().lower()
                    desc = str(row[desc_col])
                    
                    if not d1 or not d2 or d1 == 'nan' or d2 == 'nan' or len(d1) < 3 or len(d2) < 3:
                        continue
                    
                    # Add to known drugs
                    self.all_known_drugs.add(d1)
                    self.all_known_drugs.add(d2)
                    
                    key = frozenset([d1, d2])
                    severity = self._determine_severity(desc)
                    
                    self.interaction_map[key] = {
                        'severity': severity,
                        'desc': desc,
                        'drugs': (d1, d2)
                    }
                    loaded += 1
                except:
                    continue
            
            print(f"   ✅ Loaded {loaded} interactions")
            
        except FileNotFoundError:
            print(f"   ⚠️ DDI file not found: {self.ddi_path}")
        except Exception as e:
            print(f"   ⚠️ Error: {e}")

    def _determine_severity(self, desc: str) -> str:
        """Determine severity from description."""
        desc_lower = desc.lower()
        
        if any(kw in desc_lower for kw in ['contraindicated', 'avoid', 'fatal', 'life-threatening', 'dangerous', 'serious', 'death', 'toxicity']):
            return 'SEVERE'
        elif any(kw in desc_lower for kw in ['caution', 'monitor', 'adjust', 'may increase', 'potential', 'risk']):
            return 'MODERATE'
        elif any(kw in desc_lower for kw in ['minor', 'unlikely', 'rare', 'possible', 'slight']):
            return 'MILD'
        else:
            return 'CAUTION'

    def _load_brand_map(self):
        """Load medicine database with strict validation."""
        # Hardcoded high-confidence mappings
        self.brand_to_generic = {
            # Statins
            'simvotin': ['simvastatin'], 'simvotin 5': ['simvastatin'], 'simvotin 10': ['simvastatin'],
            'simvotin 20': ['simvastatin'], 'simvotin 40': ['simvastatin'],
            'atorva': ['atorvastatin'], 'atorva 10': ['atorvastatin'], 'atorva 20': ['atorvastatin'],
            
            # Antibiotics
            'claribid': ['clarithromycin'], 'claribid 250': ['clarithromycin'], 'claribid 500': ['clarithromycin'],
            'azithral': ['azithromycin'], 'azithral 500': ['azithromycin'], 'azithral 250': ['azithromycin'],
            'augmentin': ['amoxicillin', 'clavulanic acid'], 'augmentin 625': ['amoxicillin', 'clavulanic acid'],
            
            # Pain/Fever
            'combiflam': ['ibuprofen', 'paracetamol'],
            'dolo': ['paracetamol'], 'dolo 650': ['paracetamol'], 'dolo 500': ['paracetamol'],
            'crocin': ['paracetamol'], 'crocin 650': ['paracetamol'],
            'brufen': ['ibuprofen'], 'brufen 400': ['ibuprofen'], 'brufen 600': ['ibuprofen'],
            
            # Antacids
            'pantocid': ['pantoprazole'], 'pantocid 40': ['pantoprazole'],
            'pan d': ['pantoprazole', 'domperidone'],
            'omez': ['omeprazole'], 'omez 20': ['omeprazole'],
            
            # Common generics
            'aspirin': ['aspirin'], 'warfarin': ['warfarin'], 'metformin': ['metformin'],
            'lisinopril': ['lisinopril'], 'amlodipine': ['amlodipine']
        }
        
        try:
            print(f"📂 Loading medicines from {os.path.basename(self.med_path)}...")
            df = pd.read_csv(self.med_path, low_memory=False, nrows=100000)  # Limit for speed
            df.columns = [c.strip().lower() for c in df.columns]
            
            # Find columns flexibly
            name_col = next((c for c in df.columns if 'name' in c or 'medicine' in c or 'drug' in c), None)
            comp_col = next((c for c in df.columns if 'composition' in c or 'salt' in c or 'generic' in c or 'ingredient' in c), None)
            
            if not name_col:
                print("   ⚠️ Name column not found, using hardcoded mappings only")
                return
            
            if not comp_col:
                print("   ⚠️ Composition column not found, using hardcoded mappings only")
                return
            
            print(f"   📋 Columns: {name_col} → {comp_col}")
            
            loaded = 0
            for _, row in df.iterrows():
                try:
                    brand = str(row[name_col]).strip().lower()
                    composition = str(row[comp_col])
                    
                    if not brand or brand == 'nan' or len(brand) < 3:
                        continue
                    
                    # Skip if already mapped
                    if brand in self.brand_to_generic:
                        continue
                    
                    generics = self._clean_composition(composition)
                    if not generics:
                        continue
                    
                    # Validate: at least one generic must be in DDI database
                    valid_generics = [g for g in generics if g in self.all_known_drugs]
                    
                    if valid_generics:
                        self.brand_to_generic[brand] = valid_generics
                        loaded += 1
                        
                        # Also add brand to known drugs
                        self.all_known_drugs.add(brand)
                except:
                    continue
            
            print(f"   ✅ Loaded {loaded} brand mappings from CSV")
            print(f"   📊 Total: {len(self.brand_to_generic)} brands, {len(self.all_known_drugs)} known drugs")
            
        except FileNotFoundError:
            print(f"   ⚠️ File not found: {self.med_path}")
        except Exception as e:
            print(f"   ⚠️ Error: {e}")

    def is_valid_drug(self, drug_name: str) -> bool:
        """Strict validation: drug must be in database."""
        norm = drug_name.strip().lower()
        
        # Blacklist non-drugs
        blacklist = {
            'infection', 'bacterial', 'viral', 'disease', 'disorder', 'syndrome',
            'cholesterol', 'diabetes', 'hypertension', 'fever', 'pain', 'headache',
            'nausea', 'cough', 'cold', 'flu', 'allergy', 'inflammation', 'rash',
            'joint', 'muscle', 'bone', 'heart', 'liver', 'kidney', 'stomach',
            'blood', 'sugar', 'pressure', 'chronic', 'acute', 'severe', 'mild'
        }
        
        # Check if drug name contains blacklisted words
        for word in blacklist:
            if word in norm:
                return False
        
        # Must be in brand map OR known drugs
        if norm in self.brand_to_generic:
            return True
        
        if norm in self.all_known_drugs:
            return True
        
        # Fuzzy match (high threshold)
        matches = get_close_matches(norm, list(self.brand_to_generic.keys()) + list(self.all_known_drugs), n=1, cutoff=0.90)
        return bool(matches)

    def filter_valid_drugs(self, entities: List[str]) -> List[str]:
        """Filter to keep only validated drugs."""
        valid = []
        filtered = []
        
        for entity in entities:
            if self.is_valid_drug(entity):
                valid.append(entity)
            else:
                filtered.append(entity)
        
        if filtered:
            print(f"🔍 Filtered out: {', '.join(filtered[:10])}")
        
        return valid

    def get_generic_name(self, drug_name: str) -> List[str]:
        """Get generics for a brand/drug name."""
        if drug_name in self._generic_cache:
            return self._generic_cache[drug_name]
        
        norm = drug_name.strip().lower()
        
        # Direct match
        if norm in self.brand_to_generic:
            result = self.brand_to_generic[norm]
            self._generic_cache[drug_name] = result
            return result
        
        # Fuzzy match
        matches = get_close_matches(norm, self.brand_to_generic.keys(), n=1, cutoff=0.90)
        if matches:
            result = self.brand_to_generic[matches[0]]
            self._generic_cache[drug_name] = result
            return result
        
        # Assume it's already generic if in DDI database
        if norm in self.all_known_drugs:
            result = [norm]
            self._generic_cache[drug_name] = result
            return result
        
        # Not found
        result = []
        self._generic_cache[drug_name] = result
        return result

    def check_interactions(self, drugs: List[str]) -> List[Dict]:
        """Check for DDIs among drugs."""
        if not drugs or len(drugs) < 2:
            return []
        
        # Get all generics
        all_generics = []
        for drug in drugs:
            generics = self.get_generic_name(drug)
            for gen in generics:
                all_generics.append((drug, gen))
        
        if len(all_generics) < 2:
            return []
        
        # Check pairs
        warnings = []
        seen = set()
        
        for i, (orig_a, gen_a) in enumerate(all_generics):
            for orig_b, gen_b in all_generics[i+1:]:
                if gen_a == gen_b:
                    continue
                
                key = frozenset([gen_a, gen_b])
                if key in seen:
                    continue
                
                if key in self.interaction_map:
                    seen.add(key)
                    info = self.interaction_map[key]
                    
                    warnings.append({
                        'pair': f"{orig_a.title()} + {orig_b.title()}",
                        'components': f"{gen_a.title()} + {gen_b.title()}",
                        'severity': info['severity'],
                        'message': info['desc'],
                        'is_internal': orig_a == orig_b
                    })
        
        # Sort by severity
        order = {'SEVERE': 0, 'MODERATE': 1, 'CAUTION': 2, 'MILD': 3}
        warnings.sort(key=lambda w: order.get(w['severity'], 99))
        
        return warnings