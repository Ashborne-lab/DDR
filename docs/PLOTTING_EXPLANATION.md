# Plotting Functions: Types of Comparisons Explained

This document explains what each visualization function in `plotting.py` does and what types of comparisons they perform.

## Overview

The plotting module contains 4 visualization functions, each designed to show different aspects of the drug-symptom relationship data. Let me break down what each one compares and why it's useful.

---

## 1. `create_relationship_chart()` - Relationship Type Comparison

**What it compares**: Adverse reactions vs. Treatment effects

**How it works**:
- Takes all findings and splits them into two groups:
  - **Adverse reactions**: Drug-symptom pairs where the drug causes the symptom (bad)
  - **Treatment effects**: Drug-symptom pairs where the drug treats the symptom (good)
- Creates side-by-side bar charts showing confidence scores for each relationship type
- Left chart (red): Adverse reactions with their confidence levels
- Right chart (green): Treatment effects with their confidence levels

**Why it's useful**: 
- Quickly see the balance between harmful and beneficial relationships
- Compare confidence levels between adverse and treatment relationships
- Identify which drugs have more adverse vs. treatment relationships

**Example**: If you analyze a report and see 5 adverse reactions (red bars) and 2 treatment effects (green bars), you know there are more problems than benefits detected.

---

## 2. `create_confidence_distribution()` - Confidence Score Distribution

**What it compares**: Distribution of confidence scores across all findings

**How it works**:
- Extracts all confidence scores (0.0 to 1.0) from findings
- Creates a histogram with 20 bins showing how many relationships fall into each confidence range
- X-axis: Confidence level (0% to 100%)
- Y-axis: Frequency (how many relationships have that confidence)

**Why it's useful**:
- See if most relationships are high-confidence (right side of chart) or low-confidence (left side)
- Identify if the analysis is producing reliable results
- Spot patterns: Are most findings around 50% confidence (uncertain) or 80%+ (confident)?

**Example**: If the histogram shows most bars on the right (high confidence), your analysis is producing reliable results. If most bars are on the left (low confidence), the relationships are less certain.

---

## 3. `create_entity_network_graph()` - Relationship Network Visualization

**What it compares**: Visual connections between drugs and symptoms

**How it works**:
- Creates a network graph where:
  - **Nodes** (points) represent drugs (blue squares) and symptoms (orange circles)
  - **Edges** (lines) connect drugs to symptoms they're related to
  - **Edge colors**: Red for adverse relationships, green for treatment relationships
- Uses a spring layout algorithm to position nodes so connected items are close together
- Shows the overall structure of relationships in the data

**Why it's useful**:
- See which drugs are connected to multiple symptoms (highly connected nodes)
- Identify symptoms that appear with multiple drugs (common symptoms)
- Understand the complexity of relationships in a single view
- Spot clusters: groups of drugs and symptoms that are all related

**Example**: If you see one drug (blue square) connected to many symptoms (orange circles) with red lines, that drug has many adverse effects. If a symptom has many green lines connecting to different drugs, multiple drugs can treat that symptom.

---

## 4. `create_entity_type_distribution()` - Frequency Comparison

**What it compares**: Most frequently appearing drugs vs. most frequently appearing symptoms

**How it works**:
- Counts how many times each drug appears in the findings
- Counts how many times each symptom appears in the findings
- Creates side-by-side horizontal bar charts:
  - Left chart (blue): Top 10 most frequent drugs
  - Right chart (orange): Top 10 most frequent symptoms
- Shows the count (frequency) for each item

**Why it's useful**:
- Identify which drugs appear most often in the analysis (might indicate common medications)
- Identify which symptoms appear most often (might indicate common side effects)
- Compare the frequency of different entities
- Useful for understanding patterns: "Is headache the most common symptom? Is ibuprofen the most common drug?"

**Example**: If "ibuprofen" appears 5 times and "headache" appears 8 times, the chart shows these as the tallest bars, indicating they're the most common drug and symptom respectively.

---

## Summary Table

| Function | Comparison Type | What It Shows | Use Case |
|----------|----------------|---------------|----------|
| `create_relationship_chart`` | Adverse vs. Treatment | Confidence scores by relationship type | Balance of good vs. bad relationships |
| `create_confidence_distribution` | Confidence levels | Distribution of confidence scores | Quality/reliability of analysis |
| `create_entity_network_graph` | Network connections | Visual map of drug-symptom connections | Overall relationship structure |
| `create_entity_type_distribution` | Frequency ranking | Most common drugs and symptoms | Pattern identification |

---

## How They Work Together

These four visualizations complement each other:

1. **Start with `create_relationship_chart`**: Get an overview of adverse vs. treatment
2. **Check `create_confidence_distribution`**: Verify the results are reliable
3. **Explore `create_entity_network_graph`**: Understand the connections visually
4. **Review `create_entity_type_distribution`**: Identify the most common patterns

Together, they provide a comprehensive view of the drug-symptom relationships detected in your medical text analysis.

---

## Technical Details

### Data Flow

All functions follow the same pattern:
1. **Input**: List of findings (dictionaries with drug, effect, relationship, confidence)
2. **Processing**: Filter, group, or transform the data as needed
3. **Visualization**: Create Plotly figure objects
4. **Output**: Return figure (or None if no data)

### Comparison Methods Used

- **Categorical comparison**: Splitting by relationship type (adverse/treatment)
- **Statistical distribution**: Histogram of confidence scores
- **Network analysis**: Graph theory to show connections
- **Frequency analysis**: Counting occurrences and ranking

Each uses different data analysis techniques to reveal different insights from the same underlying data.

