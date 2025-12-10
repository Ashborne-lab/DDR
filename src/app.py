import sys
import os
import re
import numpy as np
import pandas as pd
import streamlit as st
from typing import List, Dict, Tuple
import io

# --- 1. SYSTEM SETUP & PATCHES ---
os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

def _patch_torch_classes():
    try:
        import torch
        class SafeClasses:
            class PathObj:
                _path = []
            __path__ = PathObj()
            def __getattr__(self, name):
                return None

        if hasattr(torch, 'classes'):
            torch.classes = SafeClasses()
            
    except ImportError:
        pass

_patch_torch_classes()

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

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Drug-Disease Analyzer | Premium Medical AI",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. CACHED RESOURCE LOADING ---

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
                
                # Regex to extract tagged entities
                # Finds: @TypeSrc$ EntityName @/TypeSrc$
                source_pattern = re.compile(r'@.*?Src\$\s*(.*?)\s*@/.*?Src\$')
                target_pattern = re.compile(r'@.*?Tgt\$\s*(.*?)\s*@/.*?Tgt\$')
                
                # Use name=None to get simple tuples (faster/safer)
                for row in df.itertuples(index=False, name=None):
                    # Text is typically in the last or 8th column (index 7)
                    if len(row) < 8: continue
                    text_content = str(row[7]) 
                    
                    src_match = source_pattern.search(text_content)
                    tgt_match = target_pattern.search(text_content)
                    
                    if src_match and tgt_match:
                        entity_a = src_match.group(1).lower().strip() # Source (often Symptom/Disease)
                        entity_b = tgt_match.group(1).lower().strip() # Target (often Drug/Gene)
                        
                        # Add to master lists
                        database['drugs'].add(entity_b)
                        database['symptoms'].add(entity_a)
                        
                        # Build Search Index
                        first_word = entity_b.split()[0]
                        if len(first_word) > 3:
                            if first_word not in database['search_index']:
                                database['search_index'][first_word] = set()
                            database['search_index'][first_word].add(entity_b)

                        # Add Proven Relationship
                        database['relations'].append({
                            'drug': entity_b.title(),
                            'effect': entity_a.title(),
                            'relationship': 'associated', # Derived from research paper
                            'confidence': 0.95, # Very high confidence
                            'evidence': f'Research Paper (from {filename})',
                            'sentence': text_content[:200] + "..."
                        })
                        
                        # Add Info if missing
                        if entity_b not in database['drug_info']:
                            database['drug_info'][entity_b] = {
                                'class': 'Research Entity',
                                'common_use': entity_a.title(),
                                'known_effects': [entity_a],
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

def extract_drug_symptom_relations(text: str, use_ai: bool = True) -> List[Dict]:
    """
    Optimized relation extraction with Partial Matching for receipts.
    """
    if not text or not text.strip(): return []

    database = load_drug_symptom_database()
    biobert_models = load_model() if use_ai else None

    found_drugs_map = {}
    text_lower = text.lower()
    
    # Clean tokens (alphanumeric only)
    tokens = re.findall(r'[a-z0-9]+', text_lower)
    
    # 1. Search Logic (Updated for Partial Matching)
    for word in tokens:
        # A. Exact Match
        if len(word) > 2 and word in database['drugs']:
            found_drugs_map[word] = "Exact Match"
        # B. Partial/Index Match (Fix for "Abiros" -> "Abiros CA")
        elif word in database.get('search_index', {}):
            candidates = list(database['search_index'][word])
            if candidates:
                best_match = min(candidates, key=len)
                found_drugs_map[best_match] = "Partial Match"

    # 2. Multi-word Check
    if len(tokens) > 1:
        for n in range(2, 4):
            for i in range(len(tokens) - n + 1):
                gram = " ".join(tokens[i:i+n])
                if gram in database['drugs']:
                    found_drugs_map[gram] = "Exact Match"

    # AI Fallback
    if biobert_models and biobert_models.get('ner') and len(found_drugs_map) < 50:
        try:
            ai_drugs, _ = extract_entities_with_biobert(text, biobert_models)
            for d in ai_drugs:
                if d not in found_drugs_map: found_drugs_map[d] = "BioBERT AI"
        except: pass

    relations = []
    
    # Strategy A: Sentences
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', text) if s.strip()]
    adverse_pattern = re.compile(r'(?:caused|side effect|worsened|aggravated|due to)', re.IGNORECASE)
    treatment_pattern = re.compile(r'(?:treated|taking|prescribed|helps|manages|for)', re.IGNORECASE)
    
    for sentence in sentences:
        sent_lower = sentence.lower()
        # Loose matching for sentence context
        local_drugs = [d for d in found_drugs_map if d.split()[0] in sent_lower][:5]
        
        sent_tokens = set(re.findall(r'[a-z]+', sent_lower))
        local_symptoms = list(sent_tokens & database['symptoms'])[:5]
        
        is_adverse = bool(adverse_pattern.search(sent_lower))
        is_treatment = bool(treatment_pattern.search(sent_lower))
        
        for drug in local_drugs:
            for symptom in local_symptoms:
                rel_type = None
                conf = 0.5
                evidence = []

                db_match = next((r for r in database['relations'] if r['drug'] == drug and r['effect'] == symptom), None)
                if db_match:
                    rel_type = db_match['relationship']
                    conf = 0.9
                    evidence.append("Validated by Medical Database")
                elif is_adverse:
                    rel_type = 'adverse'
                    conf = 0.7
                    evidence.append("Context implies side effect")
                elif is_treatment:
                    rel_type = 'treatment'
                    conf = 0.7
                    evidence.append("Context implies treatment")
                
                if rel_type:
                    relations.append({
                        'drug': drug.title(), 'effect': symptom.title(),
                        'relationship': rel_type, 'confidence': conf,
                        'evidence': ' • '.join(evidence), 'sentence': sentence
                    })

    # Strategy B: Receipt Fallback
    if len(relations) == 0 and len(found_drugs_map) > 0:
        for drug in list(found_drugs_map.keys())[:20]:
            info = database['drug_info'].get(drug)
            if info:
                if info.get('common_use') and info['common_use'] != 'Unknown':
                    relations.append({
                        'drug': drug.title(), 'effect': str(info['common_use']).title(),
                        'relationship': 'treatment', 'confidence': 0.85,
                        'evidence': 'Database Knowledge', 'sentence': f"Detected Item: {drug}"
                    })
                
                if info.get('known_effects'):
                    top_effect = info['known_effects'][0]
                    relations.append({
                        'drug': drug.title(), 'effect': str(top_effect).title(),
                        'relationship': 'adverse', 'confidence': 0.6,
                        'evidence': 'Potential Side Effect Warning', 'sentence': f"Warning: {drug} may cause {top_effect}"
                    })

    unique_relations = {}
    for rel in relations:
        key = (rel['drug'].lower(), rel['effect'].lower(), rel['relationship'])
        if key not in unique_relations or rel['confidence'] > unique_relations[key]['confidence']:
            unique_relations[key] = rel

    return sorted(unique_relations.values(), key=lambda x: x['confidence'], reverse=True)

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
    findings = pd.read_json(findings_json, orient='records').to_dict('records')
    return {
        'relationship': create_relationship_chart(findings),
        'confidence': create_confidence_distribution(findings),
        'network': create_entity_network_graph(findings),
        'entity_type': create_entity_type_distribution(findings)
    }

# --- 7. MAIN APPLICATION ---

def main():
    load_premium_css()
    
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
                st.warning("Please enter some text to analyze.")
            else:
                with st.spinner("🧠 Processing Medical Data..."):
                    findings = extract_drug_symptom_relations(text_input, use_ai=use_ai_models)
                    findings = [f for f in findings if f['confidence'] >= min_confidence]
                    
                    st.session_state.findings = findings
                    st.session_state.analysis_count += 1
                    
                    if findings:
                        st.success(f"Found {len(findings)} insights!")
                        c1, c2, c3, c4 = st.columns(4)
                        adv_count = sum(1 for f in findings if f['relationship'] == 'adverse')
                        treat_count = len(findings) - adv_count
                        uniq_drugs = len(set(f['drug'] for f in findings))
                        
                        with c1: render_metric_card("Adverse Events", str(adv_count), "⚠️", "danger")
                        with c2: render_metric_card("Treatments", str(treat_count), "💊", "success")
                        with c3: render_metric_card("Unique Drugs", str(uniq_drugs), "💉", "primary")
                        
                        if show_details:
                            st.markdown("#### Detailed Findings")
                            for f in findings: render_finding_card(f)
                        
                        df = pd.DataFrame(findings)
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download Report", csv, "report.csv", "text/csv")
                    else:
                        st.info("No medical relationships found in the text.")

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