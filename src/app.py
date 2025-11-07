import sys
import os

os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

def _patch_torch_classes():
    try:
        import torch
        if hasattr(torch, '_classes'):
            class _SafeClassesProxy:
                def __init__(self):
                    pass
                def __getattr__(self, name):
                    if name == '__path__':
                        path_obj = type('path', (), {})()
                        path_obj._path = []
                        return path_obj
                    raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
            try:
                torch._classes = _SafeClassesProxy()
            except (RuntimeError, AttributeError, TypeError):
                pass
    except ImportError:
        pass

_patch_torch_classes()

import streamlit as st
import pandas as pd
import re
from pathlib import Path
from typing import List, Dict, Tuple
from plotting import (
    create_relationship_chart,
    create_confidence_distribution,
    create_entity_network_graph,
    create_entity_type_distribution
)

@st.cache_resource
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
            models['classifier'] = pipeline(
                "text-classification",
                model="outputs/pubmedbert-finetuned",
                device=-1
            )
        except Exception:
            models['classifier'] = None

    except Exception:
        return None

    return models if models.get('ner') or models.get('classifier') else None

def extract_entities_with_biobert(text: str, models: Dict) -> Tuple[List[str], List[str]]:
    if not models or not models.get('ner'):
        return [], []

    try:
        entities = models['ner'](text)

        drugs = []
        symptoms = []

        for entity in entities:
            entity_text = entity['word'].lower()
            entity_type = entity.get('entity_group', '').upper()

            if entity_type in ['MEDICATION', 'DRUG', 'CHEMICAL']:
                drugs.append(entity_text)
            elif entity_type in ['SYMPTOM', 'DISEASE', 'CONDITION', 'ADVERSE_EVENT']:
                symptoms.append(entity_text)
            elif 'drug' in entity_text or any(d in entity_text for d in ['medication', 'pill', 'tablet']):
                drugs.append(entity_text)
            elif any(s in entity_text for s in ['pain', 'headache', 'nausea', 'fever', 'rash']):
                symptoms.append(entity_text)

        return list(set(drugs)), list(set(symptoms))

    except Exception as e:
        st.warning(f"⚠️ BioBERT NER error: {e}. Using rule-based fallback.")
        return [], []

def extract_text_from_image(image_bytes, file_format="PNG") -> str:
    try:
        import pytesseract
        from PIL import Image
        import io
        
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang='eng')
        return text.strip()
    except ImportError:
        st.error("OCR libraries not installed. Please install: pip install pytesseract Pillow")
        st.info("Note: You also need to install Tesseract OCR engine on your system.")
        return ""
    except Exception as e:
        st.warning(f"OCR extraction error: {e}")
        return ""

def extract_text_from_pdf(uploaded_file) -> str:
    try:
        import fitz
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        if not file_bytes:
            return ""
        
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        total_pages = len(doc)
        
        for page_num in range(total_pages):
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
                    if ocr_text and ocr_text.strip():
                        text += f"[OCR from page {page_num + 1}]\n{ocr_text}\n"
                except ImportError:
                    pass
                except Exception:
                    pass
        
        doc.close()
        return text.strip()
    except ImportError:
        st.error("PyMuPDF (fitz) is not installed. Please install it: pip install PyMuPDF")
        return ""
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

@st.cache_data(ttl=3600)
def load_drug_symptom_database():
    database = {
        'drugs': set(),
        'symptoms': set(),
        'relations': [],
        'drug_info': {}
    }

    default_drugs = {
        'lisinopril', 'metformin', 'atorvastatin', 'ibuprofen',
        'aspirin', 'omeprazole', 'sertraline', 'loratadine',
        'amlodipine', 'amlodipine besylate', 'nsaid', 'nsaids',
        'acetaminophen', 'paracetamol', 'naproxen', 'ondansetron',
        'dolo', 'naxdom', 'ondem', 'electral', 'dulcoflex',
        'naproxen sodium', 'ondansetron hcl', 'acetaminophen 650',
        'electrolyte', 'electrolyte powder', 'dolo 650', 'naxdom 500',
        'tablet', 'tab', 'capsule', 'cap', 'naydom', 'tab naxdom',
        'tab ondem', 'tab dolo', 'electral powder'
    }
    database['drugs'].update(default_drugs)

    default_symptoms = {
        'headache', 'migraine', 'pain', 'nausea', 'dizziness',
        'fatigue', 'cough', 'rash', 'fever', 'anxiety',
        'depression', 'insomnia', 'vomiting', 'diarrhea',
        'breathing difficulty', 'chest pain', 'muscle pain',
        'joint pain', 'stomach pain', 'abdominal pain', 'bleeding',
        'hypertension', 'diabetes', 'heartburn', 'swelling',
        'dry mouth', 'gastritis'
    }
    database['symptoms'].update(default_symptoms)

    try:
        sample_dir = Path('data/sample')
        if sample_dir.exists():
            tsv_files = list(sample_dir.glob('*.tsv'))
            for file in tsv_files:
                try:
                    df = pd.read_csv(file, sep='\t', on_bad_lines='skip')
                    for _, row in df.iterrows():
                        if 'drug' in df.columns and 'effect' in df.columns:
                            drug = str(row['drug']).lower().strip()
                            effect = str(row['effect']).lower().strip()
                            if drug and effect:
                                database['drugs'].add(drug)
                                database['symptoms'].add(effect)
                                database['relations'].append({
                                    'drug': drug,
                                    'effect': effect,
                                    'type': row.get('type', 'adverse')
                                })
                except Exception:
                    continue
    except Exception:
        pass

    database['drug_info'] = {
        'ibuprofen': {
            'class': 'NSAID',
            'common_use': 'pain',
            'known_effects': ['stomach pain', 'abdominal pain', 'heartburn', 'nausea', 'gastritis'],
            'mechanism': 'Cyclooxygenase inhibition'
        },
        'nsaid': {
            'class': 'NSAID',
            'common_use': 'pain',
            'known_effects': ['stomach pain', 'abdominal pain', 'heartburn', 'nausea', 'gastritis'],
            'mechanism': 'Cyclooxygenase inhibition'
        },
        'nsaids': {
            'class': 'NSAID',
            'common_use': 'pain',
            'known_effects': ['stomach pain', 'abdominal pain', 'heartburn', 'nausea', 'gastritis'],
            'mechanism': 'Cyclooxygenase inhibition'
        },
        'lisinopril': {
            'class': 'ACE inhibitor',
            'common_use': 'hypertension',
            'known_effects': ['cough', 'dizziness', 'headache', 'fatigue'],
            'mechanism': 'Angiotensin-converting enzyme inhibition'
        },
        'metformin': {
            'class': 'Biguanide',
            'common_use': 'diabetes',
            'known_effects': ['nausea', 'diarrhea', 'vitamin b12 deficiency', 'stomach pain'],
            'mechanism': 'Reduces hepatic glucose production'
        },
        'sertraline': {
            'class': 'SSRI',
            'common_use': 'depression',
            'known_effects': ['nausea', 'insomnia', 'anxiety', 'headache'],
            'mechanism': 'Selective serotonin reuptake inhibition'
        },
        'omeprazole': {
            'class': 'Proton pump inhibitor',
            'common_use': 'acid reflux',
            'known_effects': ['headache', 'stomach pain', 'vitamin b12 deficiency'],
            'mechanism': 'Gastric acid suppression'
        },
        'naproxen': {
            'class': 'NSAID',
            'common_use': 'pain',
            'known_effects': ['stomach pain', 'headache', 'nausea', 'dizziness'],
            'mechanism': 'Cyclooxygenase inhibition'
        },
        'naxdom': {
            'class': 'NSAID',
            'common_use': 'pain',
            'known_effects': ['stomach pain', 'headache', 'nausea', 'dizziness'],
            'mechanism': 'Cyclooxygenase inhibition'
        },
        'naydom': {
            'class': 'NSAID',
            'common_use': 'pain',
            'known_effects': ['stomach pain', 'headache', 'nausea', 'dizziness'],
            'mechanism': 'Cyclooxygenase inhibition'
        },
        'ondansetron': {
            'class': 'Antiemetic',
            'common_use': 'nausea',
            'known_effects': ['headache', 'dizziness', 'fatigue'],
            'mechanism': 'Serotonin receptor antagonist'
        },
        'ondem': {
            'class': 'Antiemetic',
            'common_use': 'nausea',
            'known_effects': ['headache', 'dizziness', 'fatigue'],
            'mechanism': 'Serotonin receptor antagonist'
        },
        'paracetamol': {
            'class': 'Analgesic',
            'common_use': 'fever',
            'known_effects': ['nausea', 'rash', 'liver damage'],
            'mechanism': 'Cyclooxygenase inhibition'
        },
        'acetaminophen': {
            'class': 'Analgesic',
            'common_use': 'fever',
            'known_effects': ['nausea', 'rash', 'liver damage'],
            'mechanism': 'Cyclooxygenase inhibition'
        },
        'dolo': {
            'class': 'Analgesic',
            'common_use': 'fever',
            'known_effects': ['nausea', 'rash'],
            'mechanism': 'Cyclooxygenase inhibition'
        }
    }

    return database

def extract_drug_symptom_relations(text: str, use_ai: bool = True) -> List[Dict]:
    if not text or not text.strip():
        return []

    database = load_drug_symptom_database()

    biobert_models = None
    if use_ai:
        biobert_models = load_model()

    ADVERSE_PATTERNS = [
        r'(?:caused|induced|triggered|developed|experienced|due to|because of|after taking|following|since starting)',
        r'(?:side effect|adverse|reaction|complication)',
        r'(?:worsened|aggravated|exacerbated)',
        r'(?:discontinued|stopped|changed|stopped taking)',
        r'(?:suspected|possible|likely|potential)',
        r'(?:new onset|new-onset|newly developed)'
    ]

    TREATMENT_PATTERNS = [
        r'(?:treated with|taking for|prescribed for|helps|helped|improved|resolved|controlled)',
        r'(?:treatment|therapy|medication for|managing)',
        r'(?:manages|controls|treats)',
        r'(?:remains stable|well-controlled|effective)',
        r'(?:for (?:the )?(?:treatment|management|control) of)',
        r'(?:to (?:treat|manage|control))'
    ]

    adverse_pattern = re.compile('|'.join(ADVERSE_PATTERNS), re.IGNORECASE)
    treatment_pattern = re.compile('|'.join(TREATMENT_PATTERNS), re.IGNORECASE)

    symptoms = database['symptoms']
    drugs = database['drugs']
    known_relations = database['relations']
    drug_info = database['drug_info']

    sentences = [s.strip() for s in re.split(r'[.!?\n]+', text) if s.strip()]
    if not sentences:
        sentences = [text.strip()]
    
    relations = []
    seen_pairs = set()
    
    text_lower = text.lower()
    all_found_drugs = set()
    all_found_symptoms = set()
    
    if biobert_models and biobert_models.get('ner'):
        biobert_drugs, biobert_symptoms = extract_entities_with_biobert(text, biobert_models)
        all_found_drugs.update(biobert_drugs if biobert_drugs else [])
        all_found_symptoms.update(biobert_symptoms if biobert_symptoms else [])
    
    for drug in drugs:
        pattern = r'\b' + re.escape(drug) + r'\b'
        if re.search(pattern, text_lower):
            all_found_drugs.add(drug)
    
    for symptom in symptoms:
        pattern = r'\b' + re.escape(symptom) + r'\b'
        if re.search(pattern, text_lower):
            all_found_symptoms.add(symptom)
    
    prescription_keywords = ['prescription', 'tab', 'tablet', 'capsule', 'cap', 'mg', 'od', 'bd', 'tds', 'sos', 'advice']
    is_prescription_context = any(keyword in text_lower for keyword in prescription_keywords)
    
    if is_prescription_context and all_found_drugs and all_found_symptoms:
        for drug in all_found_drugs:
            for symptom in all_found_symptoms:
                pair_key = (drug, symptom)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                known_relation = None
                for rel in known_relations:
                    if rel['drug'] == drug and rel['effect'] == symptom:
                        known_relation = rel['type']
                        break

                confidence = 0.5
                relationship = None
                evidence_parts = []

                if drug in drug_info:
                    info = drug_info[drug]
                    if info['common_use'] == symptom:
                        is_treatment = True
                        confidence = 0.7
                        evidence_parts.append(f"Known treatment: {drug} treats {symptom}")
                        relationship = 'treatment'
                    elif symptom in info['known_effects']:
                        is_adverse = True
                        confidence = 0.7
                        evidence_parts.append(f"Known side effect: {drug} can cause {symptom}")
                        relationship = 'adverse'
                    else:
                        is_treatment = True
                        confidence = 0.5
                        evidence_parts.append("Prescription context: implicit treatment relationship")
                        relationship = 'treatment'
                else:
                    is_treatment = True
                    confidence = 0.5
                    evidence_parts.append("Prescription context: implicit treatment relationship")
                    relationship = 'treatment'

                if relationship:
                    relations.append({
                        'drug': drug.title(),
                        'effect': symptom.title(),
                        'relationship': relationship,
                        'confidence': min(confidence, 1.0),
                        'sentence': text[:200] + '...' if len(text) > 200 else text,
                        'evidence': ' • '.join(evidence_parts)
                    })
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        found_drugs = {drug for drug in all_found_drugs if re.search(r'\b' + re.escape(drug) + r'\b', sentence_lower)}
        found_symptoms = {symptom for symptom in all_found_symptoms if re.search(r'\b' + re.escape(symptom) + r'\b', sentence_lower)}

        for drug in found_drugs:
            for symptom in found_symptoms:
                pair_key = (drug, symptom)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                known_relation = None
                for rel in known_relations:
                    if rel['drug'] == drug and rel['effect'] == symptom:
                        known_relation = rel['type']
                        break

                is_adverse = bool(adverse_pattern.search(sentence_lower))
                is_treatment = bool(treatment_pattern.search(sentence_lower))

                confidence = 0.5
                relationship = None
                evidence_parts = []

                if drug in drug_info:
                    info = drug_info[drug]
                    if info['common_use'] == symptom:
                        is_treatment = True
                        confidence = 0.7
                        evidence_parts.append(f"Known treatment: {drug} treats {symptom}")
                    if symptom in info['known_effects']:
                        is_adverse = True
                        confidence = 0.7
                        evidence_parts.append(f"Known side effect: {drug} can cause {symptom}")

                if is_prescription_context and not is_adverse and not is_treatment:
                    if drug in drug_info:
                        info = drug_info[drug]
                        if info['common_use'] == symptom:
                            is_treatment = True
                            confidence = 0.6
                            evidence_parts.append("Prescription context: drug prescribed for symptom")
                        elif symptom in info['known_effects']:
                            is_adverse = True
                            confidence = 0.6
                            evidence_parts.append("Prescription context: drug may cause symptom")
                    else:
                        is_treatment = True
                        confidence = 0.5
                        evidence_parts.append("Prescription context: implicit treatment relationship")

                biobert_classification = None
                if biobert_models and biobert_models.get('classifier'):
                    try:
                        classification_text = f"Drug: {drug}. Symptom: {symptom}. Context: {sentence}"
                        result = biobert_models['classifier'](classification_text)
                        if result and len(result) > 0:
                            biobert_classification = result[0]
                            if biobert_classification['score'] > 0.7:
                                confidence += 0.2
                                evidence_parts.append(f"BioBERT classification ({biobert_classification['label']})")
                    except Exception:
                        pass

                if known_relation:
                    relationship = known_relation
                    confidence += 0.3
                    evidence_parts.append("Database match")

                if is_adverse and is_treatment:
                    if any(word in sentence_lower for word in ['despite', 'although', 'but', 'however']):
                        relationship = 'adverse'
                        evidence_parts.append("Adverse reaction detected")
                    else:
                        relationship = 'treatment'
                        evidence_parts.append("Treatment effect detected")
                elif is_adverse:
                    relationship = 'adverse'
                    confidence += 0.2
                    evidence_parts.append("Adverse pattern match")
                elif is_treatment:
                    relationship = 'treatment'
                    confidence += 0.2
                    evidence_parts.append("Treatment pattern match")

                if drug in drug_info:
                    info = drug_info[drug]
                    if symptom == info['common_use']:
                        confidence += 0.2
                        evidence_parts.append(f"Common use: {info['common_use']}")
                    elif symptom in info['known_effects']:
                        confidence += 0.2
                        evidence_parts.append(f"Known {info['class']} effect")

                if any(phrase in sentence_lower for phrase in [
                    'after taking', 'since starting', 'developed after',
                    'started after', 'began after', 'following', 'induced'
                ]):
                    confidence += 0.2
                    evidence_parts.append("Strong temporal relationship")

                if relationship:
                    relations.append({
                        'drug': drug.title(),
                        'effect': symptom.title(),
                        'relationship': relationship,
                        'confidence': min(confidence, 1.0),
                        'sentence': sentence,
                        'evidence': ' • '.join(evidence_parts)
                    })

    unique_relations = {}
    for rel in relations:
        key = (rel['drug'].lower(), rel['effect'].lower(), rel['relationship'])
        if key not in unique_relations or rel['confidence'] > unique_relations[key]['confidence']:
            unique_relations[key] = rel

    return sorted(unique_relations.values(), key=lambda x: x['confidence'], reverse=True)

def load_premium_css():
    st.markdown("""
    <style>
    :root {
        --primary: #2563eb;
        --primary-dark: #1e40af;
        --primary-light: #3b82f6;
        --secondary: #8b5cf6;
        --success: #10b981;
        --danger: #ef4444;
        --warning: #f59e0b;
        --text: #1f2937;
        --text-light: #6b7280;
        --bg: #ffffff;
        --bg-alt: #f9fafb;
        --border: #e5e7eb;
        --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --radius: 12px;
        --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        background: var(--bg-alt);
        color: var(--text);
        line-height: 1.6;
    }

    footer { visibility: hidden; }
    header { visibility: hidden; }

    .main .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    .premium-card {
        background: var(--bg);
        border-radius: var(--radius);
        padding: 2rem;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border);
        margin-bottom: 1.5rem;
        transition: var(--transition);
    }

    .premium-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }

    .hero-section {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: white;
        padding: 4rem 2rem;
        border-radius: var(--radius);
        text-align: center;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }

    .hero-section::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="80" r="2" fill="rgba(255,255,255,0.1)"/></svg>');
        opacity: 0.3;
    }

    .hero-content {
        position: relative;
        z-index: 1;
    }

    .hero-section h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        letter-spacing: -0.02em;
    }

    .hero-section p {
        font-size: 1.25rem;
        opacity: 0.95;
        max-width: 600px;
        margin: 0 auto;
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .metric-item {
        background: var(--bg);
        padding: 1.5rem;
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        text-align: center;
        border-left: 4px solid var(--primary);
        transition: var(--transition);
    }

    .metric-item:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }

    .metric-label {
        font-size: 0.875rem;
        color: var(--text-light);
        margin-bottom: 0.5rem;
        font-weight: 500;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary);
    }

    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: white;
        border: none;
        border-radius: var(--radius);
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: var(--transition);
        box-shadow: var(--shadow);
        width: 100%;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--secondary) 100%);
    }

    .stTextArea > div > div > textarea,
    .stTextInput > div > div > input {
        border: 2px solid var(--border);
        border-radius: var(--radius);
        padding: 0.75rem;
        transition: var(--transition);
    }

    .stTextArea > div > div > textarea:focus,
    .stTextInput > div > div > input:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background: var(--bg-alt);
        border-radius: var(--radius) var(--radius) 0 0;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: var(--transition);
    }

    .stTabs [aria-selected="true"] {
        background: var(--bg);
        color: var(--primary);
        box-shadow: var(--shadow);
    }

    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .badge-adverse {
        background: rgba(239, 68, 68, 0.1);
        color: var(--danger);
    }

    .badge-treatment {
        background: rgba(16, 185, 129, 0.1);
        color: var(--success);
    }

    .badge-confidence {
        background: rgba(37, 99, 235, 0.1);
        color: var(--primary);
    }

    .finding-card {
        background: var(--bg);
        border-radius: var(--radius);
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary);
        box-shadow: var(--shadow);
        transition: var(--transition);
    }

    .finding-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateX(4px);
    }

    @media (max-width: 768px) {
        .hero-section h1 { font-size: 2rem; }
        .hero-section p { font-size: 1rem; }
        .metric-grid { grid-template-columns: 1fr; }
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)

def render_metric_card(label: str, value: str, icon: str = "", color: str = "primary"):
    color_map = {
        "primary": "var(--primary)",
        "success": "var(--success)",
        "danger": "var(--danger)",
        "warning": "var(--warning)"
    }
    border_color = color_map.get(color, color_map["primary"])

    st.markdown(f"""
    <div class="metric-item" style="border-left-color: {border_color};">
        <div class="metric-label">{icon} {label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def render_finding_card(finding: Dict):
    rel_type = finding['relationship']
    badge_class = "badge-adverse" if rel_type == "adverse" else "badge-treatment"
    badge_text = "⚠️ Adverse" if rel_type == "adverse" else "💊 Treatment"

    confidence_pct = int(finding['confidence'] * 100)
    confidence_color = "var(--success)" if confidence_pct >= 70 else "var(--warning)" if confidence_pct >= 50 else "var(--text-light)"

    st.markdown(f"""
    <div class="finding-card fade-in">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
            <div>
                <h4 style="margin: 0; color: var(--text); font-size: 1.25rem;">
                    {finding['drug']} → {finding['effect']}
                </h4>
                <span class="badge {badge_class}" style="margin-top: 0.5rem; display: inline-block;">
                    {badge_text}
                </span>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.5rem; font-weight: 700; color: {confidence_color};">
                    {confidence_pct}%
                </div>
                <div style="font-size: 0.75rem; color: var(--text-light);">Confidence</div>
            </div>
        </div>
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border);">
            <div style="font-size: 0.875rem; color: var(--text-light); margin-bottom: 0.5rem;">
                <strong>Evidence:</strong> {finding['evidence']}
            </div>
            <div style="font-size: 0.875rem; font-style: italic; color: var(--text-light);">
                "{finding['sentence'][:150]}{'...' if len(finding['sentence']) > 150 else ''}"
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="Drug-Disease Analyzer | Premium Medical AI",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    load_premium_css()

    if 'analysis_count' not in st.session_state:
        st.session_state.analysis_count = 0
    if 'findings' not in st.session_state:
        st.session_state.findings = []

    st.markdown("""
    <div class="hero-section">
        <div class="hero-content">
            <h1>💊 Drug-Disease Relation Analyzer</h1>
            <p>Advanced AI-powered medical text analysis with intelligent relationship detection</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%); border-radius: var(--radius); margin-bottom: 1.5rem; color: white;">
            <h2 style="margin: 0; color: white;">🔬 Analysis Tools</h2>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### ⚙️ Settings")
        show_details = st.checkbox("Show Detailed Analysis", value=True)
        use_ai_models = st.checkbox(
            "🤖 Use BioBERT AI Models",
            value=False,
            disabled=False,
            help="Uses Hugging Face BioBERT for entity recognition and relation extraction. Falls back to rule-based if unavailable."
        )
        min_confidence = st.slider("Minimum Confidence", 0.0, 1.0, 0.3, 0.05)
        max_results = st.slider("Max Results", 10, 50, 20)

        st.info("ℹ️ (Optional) Install transformers + torch for AI-powered analysis: `pip install transformers torch`")

        st.markdown("---")

        st.markdown("### 📊 Session Stats")
        st.metric("Analyses", st.session_state.analysis_count)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Analysis", "📊 Visualizations", "🔍 Database", "📈 Insights"
    ])

    with tab1:
        st.markdown("### Medical Report Input")

        input_method = st.radio(
            "Input Method",
            ["Quick Input", "File Upload", "Sample Cases"],
            horizontal=True
        )

        text = ""

        if input_method == "Quick Input":
            text = st.text_area(
                "Enter medical report or symptoms",
                height=250,
                placeholder="Example: Patient presents with severe headache and nausea. Currently taking lisinopril for hypertension and reports dry cough that started after beginning medication..."
            )

            with st.expander("🎯 Quick Symptom Selector"):
                col_a, col_b = st.columns(2)
                with col_a:
                    symptoms_a = st.multiselect("Common Symptoms",
                        ["Headache", "Nausea", "Fever", "Rash", "Dizziness", "Fatigue"])
                with col_b:
                    symptoms_b = st.multiselect("Additional",
                        ["Pain", "Cough", "Anxiety", "Depression", "Insomnia", "Vomiting"])

                if symptoms_a or symptoms_b:
                    selected = ", ".join(symptoms_a + symptoms_b)
                    if text:
                        text += f"\nAdditional symptoms: {selected}"
                    else:
                        text = f"Symptoms present: {selected}"

        elif input_method == "File Upload":
            uploaded = st.file_uploader(
                "Upload Medical Report", 
                type=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp'],
                help="Supports: Text files, PDFs (text or scanned), and images (JPG, PNG, etc.)"
            )
            if uploaded is not None:
                file_type = uploaded.type.lower() if uploaded.type else ""
                file_name = uploaded.name.lower() if uploaded.name else ""
                
                if "pdf" in file_type or file_name.endswith('.pdf'):
                    with st.spinner("📄 Extracting text from PDF..."):
                        text = extract_text_from_pdf(uploaded)
                    if not text or not text.strip():
                        st.warning("⚠️ Could not extract text from PDF. Trying OCR on first page...")
                        try:
                            import fitz
                            uploaded.seek(0)
                            file_bytes = uploaded.read()
                            doc = fitz.open(stream=file_bytes, filetype="pdf")
                            if len(doc) > 0:
                                page = doc[0]
                                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                                img_data = pix.tobytes("png")
                                text = extract_text_from_image(img_data)
                            doc.close()
                        except Exception:
                            st.error("⚠️ PDF extraction failed. The PDF might be corrupted or password-protected.")
                            text = ""
                
                elif any(img_type in file_type for img_type in ['image', 'png', 'jpg', 'jpeg', 'gif', 'bmp']) or \
                     any(file_name.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
                    with st.spinner("🔍 Scanning image with OCR..."):
                        uploaded.seek(0)
                        image_bytes = uploaded.read()
                        text = extract_text_from_image(image_bytes)
                    if not text or not text.strip():
                        st.warning("⚠️ Could not extract text from image. Make sure the image is clear and contains readable text.")
                
                else:
                    try:
                        uploaded.seek(0)
                        text = uploaded.read().decode('utf-8')
                    except Exception as e:
                        st.error(f"Error reading file: {e}")
                        text = ""
                
                if text and text.strip():
                    with st.expander("📋 Preview Extracted Text"):
                        st.text_area("Content", text, height=200, disabled=True, key="preview_text")
                else:
                    text = ""

        else:
            samples = {
                "Cardiovascular Case": """
                Patient presents with chest pain and shortness of breath.
                Currently taking lisinopril 10mg daily for hypertension.
                Reports dry cough that started 2 weeks after beginning lisinopril.
                Also experiencing dizziness upon standing.
                """,
                "Pain Management Case": """
                Patient reports severe joint pain and muscle aches.
                Taking ibuprofen 400mg three times daily for pain relief.
                Developed stomach pain and heartburn after 1 week of treatment.
                """,
                "Mental Health Case": """
                Patient on sertraline 50mg daily for depression.
                Reports increased anxiety and insomnia since starting medication.
                Also experiencing nausea and dizziness in the morning.
                """
            }

            selected = st.selectbox("Choose Sample Case", list(samples.keys()))
            text = samples[selected]
            with st.expander("Preview Sample"):
                st.text_area("Sample Text", text, height=200, disabled=True)

        col1, col2 = st.columns([3, 1])
        with col1:
            analyze_btn = st.button("🔍 Analyze Report", type="primary", use_container_width=True)
        with col2:
            clear_btn = st.button("🧹 Clear", use_container_width=True)

        if clear_btn:
            st.session_state.findings = []
            st.rerun()

        if analyze_btn:
            if not text or not text.strip():
                st.warning("⚠️ Please enter a medical report or upload a file.")
            else:
                with st.spinner("🔬 Analyzing medical text... This may take a few moments."):
                    findings = extract_drug_symptom_relations(text, use_ai=use_ai_models)

                    findings = [f for f in findings if f['confidence'] >= min_confidence]
                    findings = findings[:max_results]

                    st.session_state.findings = findings
                    st.session_state.analysis_count += 1

                    if findings:
                        st.success(f"✅ Found {len(findings)} drug-symptom relationships!")

                        st.markdown("### 📈 Analysis Summary")
                        col1, col2, col3, col4 = st.columns(4)

                        adverse_count = sum(1 for f in findings if f['relationship'] == 'adverse')
                        treatment_count = sum(1 for f in findings if f['relationship'] == 'treatment')
                        avg_conf = sum(f['confidence'] for f in findings) / len(findings) if findings else 0
                        unique_drugs = len(set(f['drug'].lower() for f in findings))

                        with col1:
                            render_metric_card("Adverse Reactions", str(adverse_count), "⚠️", "danger")
                        with col2:
                            render_metric_card("Treatment Effects", str(treatment_count), "💊", "success")
                        with col3:
                            render_metric_card("Avg Confidence", f"{avg_conf:.0%}", "📊", "warning")
                        with col4:
                            render_metric_card("Drugs Found", str(unique_drugs), "💉", "primary")

                        if show_details:
                            st.markdown("### 🔍 Detailed Findings")

                            adverse_findings = [f for f in findings if f['relationship'] == 'adverse']
                            treatment_findings = [f for f in findings if f['relationship'] == 'treatment']

                            if adverse_findings:
                                st.markdown("#### ⚠️ Adverse Reactions")
                                for finding in adverse_findings:
                                    render_finding_card(finding)

                            if treatment_findings:
                                st.markdown("#### 💊 Treatment Effects")
                                for finding in treatment_findings:
                                    render_finding_card(finding)

                            st.markdown("---")
                            df_export = pd.DataFrame(findings)
                            csv = df_export.to_csv(index=False)
                            st.download_button(
                                "📥 Download Analysis Report (CSV)",
                                csv,
                                "drug_analysis_report.csv",
                                "text/csv",
                                use_container_width=True
                            )
                    else:
                        st.info("ℹ️ No drug-symptom relationships found above the confidence threshold.")

    with tab2:
        st.markdown("### 📊 Data Visualizations")

        findings = st.session_state.findings

        if findings:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Relationship Overview")
                chart = create_relationship_chart(findings)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)

            with col2:
                st.markdown("#### Confidence Distribution")
                dist_chart = create_confidence_distribution(findings)
                if dist_chart:
                    st.plotly_chart(dist_chart, use_container_width=True)

            st.markdown("#### Entity Network Graph")
            network_chart = create_entity_network_graph(findings)
            if network_chart:
                st.plotly_chart(network_chart, use_container_width=True)

            st.markdown("#### Entity Type Distribution")
            entity_chart = create_entity_type_distribution(findings)
            if entity_chart:
                st.plotly_chart(entity_chart, use_container_width=True)

            st.markdown("#### 📋 Summary Table")
            df_table = pd.DataFrame(findings)
            st.dataframe(
                df_table[['drug', 'effect', 'relationship', 'confidence', 'evidence']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("📊 Run an analysis first to see visualizations here.")

    with tab3:
        st.markdown("### 🔍 Drug Database Explorer")

        database = load_drug_symptom_database()
        search_term = st.text_input("🔍 Search for a drug", placeholder="e.g., lisinopril, ibuprofen")

        if search_term:
            drug_info = database['drug_info']
            matching = [drug for drug in drug_info.keys() if search_term.lower() in drug.lower()]

            if matching:
                selected = st.selectbox("Select Drug", matching)
                if selected and selected in drug_info:
                    info = drug_info[selected]

                    st.markdown(f"""
                    <div class="premium-card">
                        <h3 style="color: var(--primary); margin-bottom: 1rem;">💊 {selected.title()}</h3>
                        <p><strong>Drug Class:</strong> {info.get('class', 'Unknown')}</p>
                        <p><strong>Mechanism:</strong> {info.get('mechanism', 'Unknown')}</p>
                        <p><strong>Common Use:</strong> {info.get('common_use', 'Unknown').title()}</p>
                        <p><strong>Known Effects:</strong> {', '.join([e.title() for e in info.get('known_effects', [])])}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No matching drugs found.")

        with st.expander("📋 View All Drugs"):
            all_drugs = sorted(list(database['drugs']))
            cols = st.columns(3)
            for i, drug in enumerate(all_drugs):
                with cols[i % 3]:
                    st.write(f"• {drug.title()}")

    with tab4:
        st.markdown("### 📈 Analytics & Insights")

        database = load_drug_symptom_database()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Drugs", len(database['drugs']))
        with col2:
            st.metric("Total Symptoms", len(database['symptoms']))
        with col3:
            st.metric("Relations", len(database['relations']))

        if database['relations']:
            st.markdown("#### Most Common Drug-Symptom Relations")
            df_relations = pd.DataFrame(database['relations'])
            relation_counts = df_relations.groupby(['drug', 'effect']).size().reset_index(name='count')
            relation_counts = relation_counts.sort_values('count', ascending=False).head(10)

            st.dataframe(relation_counts, use_container_width=True, hide_index=True)

if __name__ == '__main__':
    main()
