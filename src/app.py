import sys
import os
import re
import numpy as np
import pandas as pd

# CRITICAL: Patch torch.classes BEFORE importing streamlit
# This prevents Streamlit's file watcher from crashing when it tries to access torch.classes.__path__._path
def _patch_torch_classes_early():
    """Patch torch.classes early to prevent Streamlit watcher errors."""
    try:
        import types
        import torch

        # Check if patch is needed
        needs_patch = False
        try:
            # Try to access the problematic attribute that Streamlit's watcher uses
            _ = list(torch.classes.__path__._path)  # type: ignore
        except (AttributeError, RuntimeError, TypeError):
            needs_patch = True

        if needs_patch:
            # Create a safe mock that mimics the expected structure
            # Streamlit expects: list(torch.classes.__path__._path)
            dummy_path_list = []
            
            # Create a namespace with _path as a list
            class DummyPath:
                def __init__(self):
                    self._path = dummy_path_list
                
                def __iter__(self):
                    return iter(self._path)
                
                def __getitem__(self, key):
                    return self._path[key] if isinstance(key, int) else None
            
            dummy_path = DummyPath()
            
            # Create safe classes namespace
            class SafeClasses:
                def __init__(self):
                    self.__path__ = dummy_path
                
                def __getattr__(self, name):
                    # Return None for any attribute access to prevent errors
                    return None
            
            torch.classes = SafeClasses()  # type: ignore[assignment]

    except ImportError:
        # torch not installed, nothing to patch
        pass
    except Exception:
        # Best-effort patch; ignore if torch internals change
        pass

# Apply patch immediately
_patch_torch_classes_early()

# Now safe to import streamlit
import streamlit as st
from typing import List, Dict, Tuple
import io

# Ensure local imports work when launched from project root
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from ddi_checker import DDIManager

os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

# Additional safety: Suppress torch.classes errors in Streamlit watcher (backup)
def _suppress_streamlit_torch_errors():
    """Backup: Suppress torch.classes errors from Streamlit's file watcher."""
    try:
        # This runs after streamlit is imported, so we can patch its watcher
        import streamlit.watcher.local_sources_watcher as watcher_module
        
        # Get the original extract_paths function
        if hasattr(watcher_module, 'extract_paths'):
            original_extract_paths = watcher_module.extract_paths
            
            def safe_extract_paths(module):
                """Wrapper that catches torch.classes errors."""
                try:
                    return original_extract_paths(module)
                except (RuntimeError, AttributeError) as e:
                    # If it's the torch.classes error, return empty list silently
                    error_str = str(e).lower()
                    if 'torch' in str(module).lower() or 'torch.classes' in error_str or '__path__._path' in error_str:
                        return []
                    # Otherwise, re-raise the original error
                    raise
            
            watcher_module.extract_paths = safe_extract_paths
    except Exception:
        # If patching fails, continue anyway - not critical
        pass

# Apply backup patch after streamlit is imported
_suppress_streamlit_torch_errors()

# Try importing plotting functions
try:
    from plotting import (
        create_relationship_chart,
        create_confidence_distribution,
        create_entity_network_graph,
        create_entity_type_distribution
    )
except ImportError:
    def create_relationship_chart(f): return None
    def create_confidence_distribution(f): return None
    def create_entity_network_graph(f): return None
    def create_entity_type_distribution(f): return None


st.set_page_config(
    page_title="Drug-Disease Analyzer | Premium Medical AI",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)



@st.cache_resource(show_spinner=False, max_entries=1)
def load_model():
    try:
        from transformers import pipeline
    except Exception:
        return None

    models = {}
    try:
        try:
            models['ner'] = pipeline(
                "token-classification",
                model="samrawal/bert-base-uncased_clinical-ner",
                aggregation_strategy="simple",
                device=-1
            )
        except Exception:
            models['ner'] = None

        try:
            if os.path.exists("outputs/pubmedbert-finetuned"):
                models['classifier'] = pipeline(
                    "text-classification",
                    model="outputs/pubmedbert-finetuned",
                    device=-1
                )
            else:
                models['classifier'] = None
        except Exception:
            models['classifier'] = None

    except Exception:
        return None

    return models if models.get('ner') or models.get('classifier') else None
@st.cache_resource(show_spinner=True)
def load_ddi_manager():
    """
    Loads the DDI Manager separately. 
    This is faster than the model loader and should be cached independently.
    Note: First load may take 30-60 seconds due to processing large datasets.
    """
    with st.spinner("🔄 Loading Drug Interaction Database (this may take 30-60 seconds on first load)..."):
        return DDIManager()
@st.cache_resource(ttl=3600, show_spinner=False, max_entries=1)
def load_drug_symptom_database():
    database = {'drugs': set(), 'symptoms': set(), 'relations': [], 'drug_info': {}, 'search_index': {}}
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    data_folder = os.path.join(project_root, 'data')
    
    if not os.path.exists(data_folder): data_folder = 'data'
    if not os.path.exists(data_folder): return database

    # 1. PROCESS ALL FILES IN DATA FOLDER
    files = [f for f in os.listdir(data_folder) if f.endswith(('.csv', '.tsv'))]
    print(f"📂 Found {len(files)} datasets: {files}") # Debug print to terminal
    
    for filename in files:
        filepath = os.path.join(data_folder, filename)
        
        try:
            # === CASE A: Handle TSV Files (train.tsv, dev.tsv, test.tsv) ===
            if filename.endswith('.tsv'):
                # Read without header (standard for these NLP datasets)
                df = pd.read_csv(filepath, sep='\t', header=None, on_bad_lines='skip', engine='python')
                
                # More specific patterns to distinguish chemical/drug vs disease
                # @ChemicalSrc$ or @DrugSrc$ = The DRUG (source of effect)
                # @DiseaseTgt$ = The DISEASE/SYMPTOM (target of effect)
                chemical_pattern = re.compile(r'@(Chemical|Drug)Src\$\s*(.*?)\s*@/(Chemical|Drug)Src\$', re.IGNORECASE)
                disease_pattern = re.compile(r'@DiseaseTgt\$\s*(.*?)\s*@/DiseaseTgt\$', re.IGNORECASE)
                
                # Use name=None to get simple tuples (faster/safer)
                for row in df.itertuples(index=False, name=None):
                    # Text is typically in the last or 8th column (index 7)
                    if len(row) < 8: continue
                    text_content = str(row[7]) 
                    
                    chem_match = chemical_pattern.search(text_content)
                    disease_match = disease_pattern.search(text_content)
                    
                    if chem_match and disease_match:
                        # ✅ CORRECT: Chemical/Drug = Source (drug), Disease = Target (symptom)
                        drug_entity = chem_match.group(2).lower().strip()
                        disease_entity = disease_match.group(1).lower().strip()
                        
                        # Validate entities before adding
                        if len(drug_entity) > 2 and len(disease_entity) > 2:
                            # Extract base drug name (remove common suffixes/prefixes)
                            base_drug = drug_entity.split()[0] if drug_entity.split() else drug_entity
                            database['drugs'].add(drug_entity)
                            database['drugs'].add(base_drug)  # Also add base name for better matching
                            database['symptoms'].add(disease_entity)
                            
                            # Build Search Index for fast lookups
                            first_word = drug_entity.split()[0]
                            if len(first_word) > 3:
                                if first_word not in database['search_index']:
                                    database['search_index'][first_word] = set()
                                database['search_index'][first_word].add(drug_entity)

                            # Add proven relationship
                            database['relations'].append({
                                'drug': drug_entity.title(),
                                'effect': disease_entity.title(),
                                'relationship': 'associated', # Derived from research paper
                                'confidence': 0.95, # Very high confidence
                                'evidence': f'Research Paper (from {filename})',
                                'sentence': text_content[:200] + "..."
                            })
                            
                            # Add drug info if missing
                            if drug_entity not in database['drug_info']:
                                database['drug_info'][drug_entity] = {
                                    'class': 'Research Entity',
                                    'common_use': disease_entity.title(),
                                    'known_effects': [disease_entity],
                                    'substitutes': [],
                                    'mechanism': 'Extracted from biomedical literature'
                                }

            # === CASE B: Handle Standard CSV (medicines_global.csv) ===
            elif filename.endswith('.csv'):
                df = pd.read_csv(
                    filepath, 
                    low_memory=False,
                    usecols=lambda col: any(kw in col.lower() for kw in ['name', 'sideeffect', 'substitute', 'therapeutic', 'class', 'use'])
                )
                df.columns = df.columns.str.lower().str.strip()
                headers = list(df.columns)
                
                name_idx = next((i for i, c in enumerate(headers) if 'name' in c), -1)
                if name_idx == -1: continue
                
                side_effect_indices = [i for i, c in enumerate(headers) if 'sideeffect' in c]
                substitute_indices = [i for i, c in enumerate(headers) if 'substitute' in c]
                use_indices = [i for i, c in enumerate(headers) if 'use' in c and 'user' not in c]
                class_idx = next((i for i, c in enumerate(headers) if 'therapeutic' in c or 'class' in c), -1)

                for row in df.itertuples(index=False, name=None):
                    drug_name = str(row[name_idx]).lower().strip()
                    if not drug_name or drug_name == 'nan': continue
                    
                    database['drugs'].add(drug_name)
                    
                    # Search Index
                    first_word = drug_name.split()[0]
                    if len(first_word) > 3:
                        if first_word not in database['search_index']: database['search_index'][first_word] = set()
                        database['search_index'][first_word].add(drug_name)

                    # Info gathering
                    found_effects = [str(row[i]).lower().strip() for i in side_effect_indices if str(row[i]).lower() != 'nan']
                    found_uses = [str(row[i]).lower().strip() for i in use_indices if str(row[i]).lower() != 'nan']
                    for f in found_effects + found_uses: database['symptoms'].add(f)
                    
                    drug_class = str(row[class_idx]) if class_idx != -1 and str(row[class_idx]).lower() != 'nan' else "Unknown"
                    primary_use = found_uses[0].title() if found_uses else drug_class

                    # Merge with existing info if present (e.g. if loaded from TSV first)
                    existing = database['drug_info'].get(drug_name, {})
                    merged_effects = list(set(existing.get('known_effects', []) + found_effects[:5]))
                    
                    database['drug_info'][drug_name] = {
                        'class': drug_class,
                        'common_use': primary_use,
                        'known_effects': merged_effects,
                        'substitutes': existing.get('substitutes', []) or ([str(row[i]).strip() for i in substitute_indices if str(row[i]).lower()!='nan'][:3]),
                        'mechanism': 'See medical guide'
                    }

        except Exception as e:
            print(f"⚠️ Error loading {filename}: {e}")
            continue

    # After all files are processed, validate the database
    print(f"\n📊 Database Loading Summary:")
    print(f"   Total drugs: {len(database['drugs'])}")
    print(f"   Total symptoms: {len(database['symptoms'])}")
    print(f"   Total relations: {len(database['relations'])}")

    # CRITICAL: Check for common misclassifications
    suspicious_drugs = [d for d in database['drugs'] if any(word in d for word in [
        'infection', 'disease', 'disorder', 'syndrome', 'cholesterol', 'diabetes', 
        'hypertension', 'fever', 'pain', 'headache', 'nausea', 'bacterial infection',
        'bacterial infections', 'condition', 'inflammation', 'allergy', 'rash', 'diarrhea'
    ])]

    if suspicious_drugs:
        print(f"\n⚠️ WARNING: Found {len(suspicious_drugs)} suspicious entries in drugs database:")
        print(f"   {', '.join(list(suspicious_drugs)[:20])}")
        print(f"   These may be misclassified symptoms. Removing...")
        
        # Clean up misclassifications
        for susp in suspicious_drugs:
            database['drugs'].discard(susp)
            database['symptoms'].add(susp)
        
        print(f"   ✅ Cleaned: {len(database['drugs'])} drugs remain")

    return database
# --- 4. OCR FUNCTIONS ---

def validate_tesseract_installed() -> bool:
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except:
        return False

def extract_text_from_image(image_bytes, aggressive_preprocessing=True) -> str:
    try:
        import pytesseract
        import cv2
        import numpy as np
        
        file_bytes = np.asarray(bytearray(image_bytes), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if image is None: return ""
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        if aggressive_preprocessing:
            gray = cv2.fastNlMeansDenoising(gray, h=10)
            try:
                coords = np.column_stack(np.where(gray > 0))
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45: angle = 90 + angle
                if abs(angle) > 1.0:
                    (h, w) = gray.shape
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            except: pass

        try:
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        except:
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
        if aggressive_preprocessing:
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        configs = [r'--oem 3 --psm 6', r'--oem 3 --psm 4'] 
        results = []
        for config in configs:
            try:
                text = pytesseract.image_to_string(binary, config=config)
                score = len(text.strip()) + len([c for c in text if c.isalnum()])
                results.append((score, text))
            except: continue
                
        if results: return max(results, key=lambda x: x[0])[1].strip()
        return ""

    except ImportError: return ""
    except Exception: return ""

def extract_text_from_pdf(uploaded_file) -> str:
    try:
        import fitz
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        if not file_bytes: return ""
        
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        total_pages = len(doc)
        
        show_progress = total_pages > 5
        if show_progress:
            progress_bar = st.progress(0)
        
        for page_num in range(total_pages):
            if show_progress:
                progress_bar.progress((page_num + 1) / total_pages)
            
            page = doc[page_num]
            page_text = page.get_text()
            
            if page_text and page_text.strip():
                text += page_text + "\n"
            else:
                try:
                    import pytesseract
                    from PIL import Image
                    import io
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    ocr_text = pytesseract.image_to_string(image, lang='eng')
                    if ocr_text.strip():
                        text += f"[OCR Page {page_num+1}]\n{ocr_text}\n"
                except: pass
        
        if show_progress: progress_bar.empty()
        doc.close()
        return text.strip()
    except Exception as e:
        st.error(f"PDF Error: {e}")
        return ""

# --- 5. CORE ANALYSIS LOGIC ---

def extract_entities_with_biobert(text: str, models: Dict) -> Tuple[List[str], List[str]]:
    if not models or not models.get('ner'):
        return [], []
    try:
        entities = models['ner'](text[:5000])
        drugs, symptoms = [], []
        for entity in entities:
            entity_text = entity['word'].lower()
            if entity['entity_group'] in ['MEDICATION', 'DRUG', 'CHEMICAL']:
                drugs.append(entity_text)
            elif entity['entity_group'] in ['SYMPTOM', 'DISEASE', 'CONDITION']:
                symptoms.append(entity_text)
        return list(set(drugs)), list(set(symptoms))
    except Exception: return [], []

def extract_drug_symptom_relations(text: str, use_ai: bool = False) -> List[Dict]:
    """
    Production-ready drug-symptom extraction.
    STRICT matching to avoid false positives.
    """
    if not text or not text.strip():
        return []

    database = load_drug_symptom_database()
    
    # Build validated drug set (CRITICAL: only drugs, not symptoms)
    valid_drugs = set()
    
    for drug in database['drugs']:
        drug_lower = drug.lower()
        # Skip if drug name looks like a symptom
        if any(word in drug_lower for word in ['infection', 'disease', 'pain', 'fever', 'cholesterol', 'diabetes', 'syndrome', 'disorder']):
            continue
        # Only include drugs with 4+ chars to avoid noise
        if len(drug_lower) >= 4:
            valid_drugs.add(drug_lower)
            
            # Extract base drug name (first word) - this catches generic names
            first_word = drug_lower.split()[0]
            if len(first_word) >= 4 and len(first_word) <= 20:
                # If first word is a standalone drug name (common patterns)
                if not any(skip in first_word for skip in ['tablet', 'capsule', 'injection', 'spray', 'gel', 'cream', 'mg', 'ml']):
                    valid_drugs.add(first_word)
            
            # Extract from compound names (split on common separators)
            parts = re.split(r'[/\+\-\(\)]', drug_lower)
            for part in parts:
                part = part.strip()
                # Extract first word from each part
                if part and ' ' in part:
                    part_first = part.split()[0]
                    if len(part_first) >= 4 and len(part_first) <= 20:
                        if not any(skip in part_first for skip in ['tablet', 'capsule', 'injection', 'mg', 'ml', 'mcg']):
                            valid_drugs.add(part_first)
    
    print(f"📊 Validated drug set: {len(valid_drugs)} drugs")
    
    found_drugs = {}
    text_lower = text.lower()
    
    # STRICT MATCHING: Only exact word boundaries
    for drug in valid_drugs:
        # Must match as whole word
        if re.search(r'\b' + re.escape(drug) + r'\b', text_lower):
            found_drugs[drug] = "Exact Match"
    
    print(f"🔍 Found {len(found_drugs)} drugs in text")
    
    if not found_drugs:
        return []
    
    relations = []
    
    # Extract sentences
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', text) if len(s.strip()) > 15]
    
    # Strict pattern matching
    treatment_pattern = re.compile(r'\b(treat|treating|treated|prescribed|taking|for|used for|indicated for|manages|helps|relieves)\b', re.IGNORECASE)
    adverse_pattern = re.compile(r'\b(caused|causing|side effect|adverse|reaction|developed|worsened|aggravated)\b', re.IGNORECASE)
    
    for sentence in sentences:
        sent_lower = sentence.lower()
        
        # Find drugs in this sentence (whole word match)
        local_drugs = [d for d in found_drugs if re.search(r'\b' + re.escape(d) + r'\b', sent_lower)]
        
        if not local_drugs:
            continue
        
        # Find symptoms (whole word match, must be in symptoms database)
        local_symptoms = []
        for symptom in database['symptoms']:
            if len(symptom) < 4:  # Skip short symptoms
                continue
            symptom_lower = symptom.lower()
            
            # Try direct match
            if re.search(r'\b' + re.escape(symptom_lower) + r'\b', sent_lower):
                # Double check it's not actually a drug
                if symptom_lower not in valid_drugs:
                    local_symptoms.append(symptom)
            
            # Also try matching individual words from compound symptoms (e.g., "tachycardia/bradycardia")
            elif '/' in symptom_lower or '-' in symptom_lower:
                # Split on / or - and match each part
                parts = re.split(r'[/\-]', symptom_lower)
                for part in parts:
                    part = part.strip()
                    if len(part) >= 4 and re.search(r'\b' + re.escape(part) + r'\b', sent_lower):
                        if part not in valid_drugs:
                            # Add the full symptom name if any part matches
                            if symptom not in local_symptoms:
                                local_symptoms.append(symptom)
                            break
        
        if not local_symptoms:
            continue
        
        # Determine relationship
        is_treatment = bool(treatment_pattern.search(sent_lower))
        is_adverse = bool(adverse_pattern.search(sent_lower))
        
        for drug in local_drugs[:3]:  # Max 3 drugs per sentence
            for symptom in local_symptoms[:3]:  # Max 3 symptoms per sentence
                
                # Check database first
                db_match = next((r for r in database['relations'] 
                               if r['drug'].lower() == drug.lower() 
                               and r['effect'].lower() == symptom.lower()), None)
                
                if db_match:
                    relations.append({
                        'drug': drug.title(),
                        'effect': symptom.title(),
                        'relationship': db_match['relationship'],
                        'confidence': 0.95,
                        'evidence': 'Validated by Database',
                        'sentence': sentence[:200]
                    })
                elif is_treatment:
                    relations.append({
                        'drug': drug.title(),
                        'effect': symptom.title(),
                        'relationship': 'treatment',
                        'confidence': 0.80,
                        'evidence': 'Treatment context detected',
                        'sentence': sentence[:200]
                    })
                elif is_adverse:
                    relations.append({
                        'drug': drug.title(),
                        'effect': symptom.title(),
                        'relationship': 'adverse',
                        'confidence': 0.75,
                        'evidence': 'Adverse effect context detected',
                        'sentence': sentence[:200]
                    })
    
    # Receipt fallback: Only if NO relations found from text analysis
    if not relations and found_drugs:
        for drug in list(found_drugs.keys())[:10]:
            info = database['drug_info'].get(drug)
            if info and info.get('common_use') and info['common_use'] != 'Unknown':
                # Only add if common_use is actually in symptoms database
                if info['common_use'].lower() in database['symptoms']:
                    relations.append({
                        'drug': drug.title(),
                        'effect': info['common_use'].title(),
                        'relationship': 'treatment',
                        'confidence': 0.85,
                        'evidence': 'Database: Known use',
                        'sentence': f"Medicine: {drug}"
                    })
    
        # CRITICAL: Final validation - remove any where drug is actually a symptom
        validated = []
        for rel in relations:
            drug_lower = rel['drug'].lower()
            effect_lower = rel['effect'].lower()
            
            # Skip if drug is in symptoms database (false positive)
            if drug_lower in database['symptoms']:
                continue
            
            # Skip if effect is in drugs database (reversed)
            if effect_lower in valid_drugs:
                continue
            
            # Lower confidence threshold for evaluation (was 0.70, now 0.50)
            if rel['confidence'] < 0.50:
                continue
            
            validated.append(rel)
    
    # Deduplicate
    unique = {}
    for rel in validated:
        key = (rel['drug'].lower(), rel['effect'].lower(), rel['relationship'])
        if key not in unique or rel['confidence'] > unique[key]['confidence']:
            unique[key] = rel
    
    return sorted(unique.values(), key=lambda x: x['confidence'], reverse=True)

# --- 6. UI & STYLING ---

@st.cache_data(show_spinner=False)
def load_premium_css():
    st.markdown("""
    <style>
    :root { 
        --primary: #2563eb; --primary-dark: #1e40af; 
        --success: #10b981; --danger: #ef4444; 
        --text: #1f2937; --text-light: #6b7280; 
        --bg: #ffffff; --border: #e5e7eb; --radius: 12px; 
    }
    .main .block-container { padding-top: 2rem; max-width: 1400px; }
    
    .premium-card { 
        background: #ffffff; 
        border-radius: var(--radius); 
        padding: 1.5rem; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
        border: 1px solid var(--border); 
        margin-bottom: 1rem; 
        color: #111827 !important; 
    }
    .premium-card h3, .premium-card p, .premium-card strong { color: #111827 !important; }
    
    .hero-section { 
        background: linear-gradient(135deg, var(--primary) 0%, #8b5cf6 100%); 
        color: white; padding: 3rem; border-radius: var(--radius); 
        text-align: center; margin-bottom: 2rem; 
    }
    .metric-item { 
        background: #fff; padding: 1.5rem; border-radius: var(--radius); 
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; 
        border-left: 4px solid var(--primary); 
    }
    .stButton > button { 
        background: linear-gradient(135deg, var(--primary) 0%, #8b5cf6 100%); 
        color: white; border: none; padding: 0.75rem 2rem; 
        border-radius: var(--radius); width: 100%; 
    }
    .badge { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-adverse { background: #fee2e2; color: #ef4444; }
    .badge-treatment { background: #d1fae5; color: #10b981; }
    </style>
    """, unsafe_allow_html=True)

def render_metric_card(label: str, value: str, icon: str = "", color: str = "primary"):
    colors = {"primary": "#2563eb", "success": "#10b981", "danger": "#ef4444", "warning": "#f59e0b"}
    st.markdown(f"""
    <div class="metric-item" style="border-left-color: {colors.get(color, '#2563eb')};">
        <div style="font-size: 0.85rem; color: #6b7280;">{icon} {label}</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #1f2937;">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def render_finding_card(finding: Dict):
    badge_cls = "badge-adverse" if finding['relationship'] == "adverse" else "badge-treatment"
    icon = "⚠️" if finding['relationship'] == "adverse" else "💊"
    
    st.markdown(f"""
    <div class="premium-card">
        <div style="display:flex; justify-content:space-between;">
            <h4 style="margin:0; color:#111827;">{finding['drug']} → {finding['effect']}</h4>
            <span class="badge {badge_cls}">{icon} {finding['relationship'].upper()}</span>
        </div>
        <div style="margin-top:0.5rem; font-size:0.9rem; color:#4b5563;">
            <strong>Confidence:</strong> {int(finding['confidence']*100)}% <br>
            <strong>Evidence:</strong> {finding['evidence']}
        </div>
        <div style="margin-top:0.5rem; font-size:0.8rem; font-style:italic; color:#6b7280;">
            "{finding['sentence'][:150]}..."
        </div>
    </div>
    """, unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def generate_all_charts(findings_json):
    findings = pd.read_json(io.StringIO(findings_json), orient='records').to_dict('records')
    return {
        'relationship': create_relationship_chart(findings),
        'confidence': create_confidence_distribution(findings),
        'network': create_entity_network_graph(findings),
        'entity_type': create_entity_type_distribution(findings)
    }

# --- 7. MAIN APPLICATION ---

def main():
    load_premium_css()
    ddi_manager = load_ddi_manager()
    if 'analysis_count' not in st.session_state: st.session_state.analysis_count = 0
    if 'findings' not in st.session_state: st.session_state.findings = []

    st.markdown("""
    <div class="hero-section">
        <h1>💊 Medical Receipt & Report Analyzer</h1>
        <p>Advanced AI identification for Drugs, Symptoms, and Side Effects</p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        use_aggressive_ocr = st.checkbox("🔎 Enhanced OCR (Slower)", value=True, help="Use OpenCV to clean noisy images")
        show_details = st.checkbox("Show Detailed Cards", value=True)
        use_ai_models = st.checkbox("🤖 Use BioBERT AI", value=False)
        min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.4, 0.05)
        st.markdown("---")
        st.metric("Total Analyses", st.session_state.analysis_count)

    tab1, tab2, tab3, tab4 = st.tabs(["📝 Analysis", "📊 Analytics", "🔍 Database", "📈 Data Stats"])

    with tab1:
        st.markdown("### 📤 Input Data")
        input_method = st.radio("Select Input:", ["Quick Text", "Upload File", "Sample Cases"], horizontal=True)
        text_input = ""
        
        if input_method == "Quick Text":
            text_input = st.text_area("Paste medical text or receipt items here:", height=200)
        elif input_method == "Upload File":
            uploaded = st.file_uploader("Upload Image (PNG/JPG) or PDF", type=['png','jpg','jpeg','pdf','txt'])
            if uploaded:
                if uploaded.name.endswith('.pdf'):
                    with st.spinner("📄 Extracting PDF..."):
                        text_input = extract_text_from_pdf(uploaded)
                elif any(uploaded.name.endswith(ext) for ext in ['.png','.jpg','.jpeg']):
                    with st.spinner("🔍 Scanning Image with OCR..."):
                        uploaded.seek(0)
                        text_input = extract_text_from_image(uploaded.read(), aggressive_preprocessing=use_aggressive_ocr)
                else:
                    text_input = uploaded.read().decode('utf-8')
                
                if text_input:
                    with st.expander("Show Extracted Text"):
                        st.text_area("Raw Text", text_input, height=150, disabled=True)
                else:
                    st.warning("⚠️ No text could be extracted.")
        else:
            samples = {
                "Cardio": "Patient prescribed lisinopril 10mg. Complaint of dry cough after 2 weeks.",
                "Receipt": "1. Dolo 650  2. Azithral 500  3. Pantocid 40",
                "Side Effect": "Patient taking ibuprofen 400mg. Reports severe stomach pain and acidity."
            }
            sel = st.selectbox("Select Sample", list(samples.keys()))
            text_input = samples[sel]
            st.info(f"Sample: {text_input}")

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🧹 Clear", use_container_width=True):
                st.session_state.findings = []
                st.rerun()
        with col2:
            analyze_btn = st.button("🚀 Analyze Report", type="primary", use_container_width=True)

        if analyze_btn:
            if not text_input.strip():
                st.warning("⚠️ Please enter some text to analyze.")
            else:
                with st.spinner("🧠 Processing Medical Data..."):
                    # ====================================
                    # STEP 1: EXTRACT DRUG-SYMPTOM RELATIONS
                    # ====================================
                    findings = extract_drug_symptom_relations(text_input, use_ai=use_ai_models)
                    findings = [f for f in findings if f['confidence'] >= min_confidence]
                    
                    st.session_state.findings = findings
                    st.session_state.analysis_count += 1
                    
                    # ====================================
                    # STEP 2: DRUG-DRUG INTERACTION CHECK
                    # ====================================
                    
                    if findings:
                        # Extract drugs only (not symptoms)
                        raw_drugs = set()
                        for f in findings:
                            if 'drug' in f:
                                raw_drugs.add(f['drug'])
                        
                        if raw_drugs:
                            # Clean drug names
                            cleaned_drugs = []
                            for drug in raw_drugs:
                                clean = re.sub(r'\b(tablet|capsule|syrup|injection|drops|gel|ointment|cream|powder)\b', 
                                             '', drug, flags=re.IGNORECASE)
                                clean = re.sub(r'\d+\.?\d*\s*(mg|ml|g|mcg|iu)', '', clean, flags=re.IGNORECASE)
                                clean = re.sub(r'[^\w\s]', '', clean).strip()
                                
                                if len(clean) > 2:
                                    cleaned_drugs.append(clean)
                            
                            # Validate against database
                            validated_drugs = ddi_manager.filter_valid_drugs(cleaned_drugs)
                            
                            # Debug output
                            print(f"\n{'='*60}")
                            print(f"🔍 DDI CHECK DEBUG:")
                            print(f"   Raw drugs: {list(raw_drugs)}")
                            print(f"   Cleaned: {cleaned_drugs}")
                            print(f"   Validated: {validated_drugs}")
                            print(f"{'='*60}\n")
                            
                            # Check interactions if 2+ drugs
                            if len(validated_drugs) >= 2:
                                interaction_alerts = ddi_manager.check_interactions(validated_drugs)
                                
                                # ====================================
                                # DISPLAY DDI WARNINGS
                                # ====================================
                                
                                if interaction_alerts:
                                    st.error(f"🚨 **CRITICAL SAFETY ALERT:** {len(interaction_alerts)} Drug Interaction(s) Detected!")
                                    
                                    st.markdown("---")
                                    st.markdown("### ⚠️ Drug Interaction Warnings")
                                    
                                    for alert in interaction_alerts:
                                        # Severity styling
                                        severity_config = {
                                            'SEVERE': ('🔴', 'red', True),
                                            'MODERATE': ('🟠', 'orange', True),
                                            'CAUTION': ('🟡', 'yellow', False),
                                            'MILD': ('🔵', 'blue', False)
                                        }
                                        icon, color, expand = severity_config.get(alert['severity'], ('⚪', 'gray', False))
                                        
                                        # Build header
                                        if alert.get('is_internal'):
                                            header = f"{icon} **{alert['severity']}**: {alert['pair']} *(Internal Conflict)*"
                                        else:
                                            header = f"{icon} **{alert['severity']}**: {alert['pair']}"
                                        
                                        with st.expander(header, expanded=expand):
                                            col1, col2 = st.columns([3, 1])
                                            
                                            with col1:
                                                st.markdown(f"**🔬 Active Components:**")
                                                st.code(alert.get('components', 'Unknown'), language='text')
                                                
                                                if alert.get('is_internal'):
                                                    st.warning(f"⚠️ {alert.get('note', 'Internal interaction detected')}")
                                                
                                                st.markdown("**⚕️ Clinical Description:**")
                                                st.info(alert['message'])
                                            
                                            with col2:
                                                st.metric("Severity", alert['severity'])
                                            
                                            # Action recommendations
                                            st.markdown("**📋 Recommended Action:**")
                                            if alert['severity'] == 'SEVERE':
                                                st.error(
                                                    "🚨 **URGENT:**\n\n"
                                                    "• Do NOT take these drugs together\n"
                                                    "• Contact your doctor immediately\n"
                                                    "• This combination can cause serious harm"
                                                )
                                            elif alert['severity'] == 'MODERATE':
                                                st.warning(
                                                    "⚠️ **CAUTION:**\n\n"
                                                    "• Consult your doctor before combining\n"
                                                    "• Dosage adjustment may be needed\n"
                                                    "• Close monitoring required"
                                                )
                                            else:
                                                st.info(
                                                    "ℹ️ **MONITOR:**\n\n"
                                                    "• Generally safe to combine\n"
                                                    "• Watch for unusual symptoms\n"
                                                    "• Inform your doctor at next visit"
                                                )
                                    
                                    st.markdown("---")
                                
                                else:
                                    st.success(f"✅ **No Known Interactions:** Analyzed {len(validated_drugs)} drugs - no dangerous combinations found.")
                            
                            elif len(validated_drugs) == 1:
                                st.info(f"ℹ️ Single drug detected: **{validated_drugs[0].title()}**\n\nNeed 2+ drugs to check for interactions.")
                            
                            else:
                                st.warning("⚠️ No valid drugs identified for interaction checking.")
                    
                    # ====================================
                    # STEP 3: DISPLAY ANALYSIS RESULTS
                    # ====================================
                    
                    if findings:
                        st.success(f"✅ Analysis Complete! Found {len(findings)} drug-symptom relationships.")
                        
                        # Summary metrics
                        st.markdown("### 📊 Analysis Summary")
                        c1, c2, c3, c4 = st.columns(4)
                        
                        adv_count = sum(1 for f in findings if f['relationship'] == 'adverse')
                        treat_count = len(findings) - adv_count
                        uniq_drugs = len(set(f['drug'] for f in findings))
                        avg_conf = sum(f['confidence'] for f in findings) / len(findings) if findings else 0
                        
                        with c1: render_metric_card("Adverse Events", str(adv_count), "⚠️", "danger")
                        with c2: render_metric_card("Treatments", str(treat_count), "💊", "success")
                        with c3: render_metric_card("Unique Drugs", str(uniq_drugs), "💉", "primary")
                        with c4: render_metric_card("Avg Confidence", f"{int(avg_conf*100)}%", "📊", "warning")
                        
                        # Detailed findings
                        if show_details:
                            st.markdown("### 🔍 Detailed Analysis")
                            
                            adverse = [f for f in findings if f['relationship'] == 'adverse']
                            treatment = [f for f in findings if f['relationship'] == 'treatment']
                            
                            if adverse:
                                st.markdown("#### ⚠️ Adverse Effects")
                                for f in adverse:
                                    render_finding_card(f)
                            
                            if treatment:
                                st.markdown("#### 💊 Treatment Effects")
                                for f in treatment:
                                    render_finding_card(f)
                        
                        # Download option
                        st.markdown("---")
                        df = pd.DataFrame(findings)
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "📥 Download Full Report (CSV)",
                            csv,
                            "medical_analysis_report.csv",
                            "text/csv",
                            use_container_width=True
                        )
                    
                    else:
                        st.info("ℹ️ No drug-symptom relationships detected in the text. Try:\n"
                               "- Including drug names (generic or brand)\n"
                               "- Mentioning symptoms or conditions\n"
                               "- Using keywords like 'taking', 'prescribed', 'for'")

    # TAB 2: VISUALIZATIONS
    with tab2:
        if st.session_state.findings:
            findings_json = pd.DataFrame(st.session_state.findings).to_json(orient='records')
            charts = generate_all_charts(findings_json)
            
            # Row 1: Overview Charts
            c1, c2 = st.columns(2)
            with c1: 
                st.subheader("Relationship Types")
                if charts['relationship']: 
                    st.plotly_chart(charts['relationship'], use_container_width=True)
                else:
                    st.info("No relationship data available.")
            with c2: 
                st.subheader("Confidence Scores")
                if charts['confidence']: 
                    st.plotly_chart(charts['confidence'], use_container_width=True)
            
            st.divider()

            # Row 2: Network Graph (The "Cool" one that was missing)
            st.subheader("🔗 Entity Network Graph")
            if charts['network']:
                st.plotly_chart(charts['network'], use_container_width=True)
            else:
                st.info("Not enough connections to form a network graph.")

            st.divider()

            # Row 3: Frequency Distribution (The other missing one)
            st.subheader("📊 Top Drugs & Symptoms")
            if charts['entity_type']:
                st.plotly_chart(charts['entity_type'], use_container_width=True)

            st.divider()
                
            # Row 4: Raw Data
            st.subheader("📋 Raw Data Table")
            st.dataframe(pd.DataFrame(st.session_state.findings), use_container_width=True)
        else:
            st.info("Run an analysis first to see visualizations.")

    with tab3:
        st.markdown("### 🏥 Drug Knowledge Base")
        db = load_drug_symptom_database()
        search = st.text_input("Search Database (Brand or Generic name):")
        if search:
            if len(search) < 2: st.caption("Please type at least 2 characters...")
            else:
                matches = [d for d in db['drug_info'].keys() if search.lower() in d][:100]
                if matches:
                    sel_drug = st.selectbox("Select Drug", matches)
                    if sel_drug:
                        info = db['drug_info'][sel_drug]
                        st.markdown(f"""
                        <div class="premium-card">
                            <h3 style="color:#2563eb;">💊 {sel_drug.title()}</h3>
                            <p><strong>Class:</strong> {info.get('class','Unknown')}</p>
                            <p><strong>Primary Use:</strong> {info.get('common_use','Unknown')}</p>
                            <p><strong>Substitutes:</strong> {', '.join(info.get('substitutes',[])[:5])}</p>
                            <hr>
                            <p style="color:#ef4444;"><strong>Known Side Effects:</strong><br>
                            {', '.join(info.get('known_effects',[]))}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else: st.warning("No drugs found matching that name.")

    with tab4:
        db = load_drug_symptom_database()
        st.markdown("### 🗄️ Database Statistics")
        c1, c2, c3 = st.columns(3)
        with c1: render_metric_card("Total Drugs", f"{len(db['drugs']):,}", "📚")
        with c2: render_metric_card("Total Symptoms", f"{len(db['symptoms']):,}", "🤒")
        with c3: render_metric_card("Cached Relations", f"{len(db['relations']):,}", "🔗")

if __name__ == '__main__':
    main()