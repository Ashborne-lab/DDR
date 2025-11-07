import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Optional
import networkx as nx

def create_relationship_chart(findings: List[Dict]) -> Optional[go.Figure]:
    if not findings:
        return None

    df = pd.DataFrame(findings)

    adverse_df = df[df['relationship'] == 'adverse'].copy()
    treatment_df = df[df['relationship'] == 'treatment'].copy()

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Adverse Reactions', 'Treatment Effects'),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )

    if not adverse_df.empty:
        fig.add_trace(
            go.Bar(
                x=adverse_df['drug'],
                y=adverse_df['confidence'],
                text=[f"{c:.0%}" for c in adverse_df['confidence']],
                textposition='auto',
                marker_color='#ef4444',
                name='Adverse',
                hovertemplate='<b>%{x}</b><br>Confidence: %{y:.0%}<extra></extra>'
            ),
            row=1, col=1
        )

    if not treatment_df.empty:
        fig.add_trace(
            go.Bar(
                x=treatment_df['drug'],
                y=treatment_df['confidence'],
                text=[f"{c:.0%}" for c in treatment_df['confidence']],
                textposition='auto',
                marker_color='#10b981',
                name='Treatment',
                hovertemplate='<b>%{x}</b><br>Confidence: %{y:.0%}<extra></extra>'
            ),
            row=1, col=2
        )

    fig.update_layout(
        height=400,
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12)
    )

    fig.update_xaxes(title_text="Drug", row=1, col=1)
    fig.update_xaxes(title_text="Drug", row=1, col=2)
    fig.update_yaxes(title_text="Confidence", range=[0, 1.1], row=1, col=1)
    fig.update_yaxes(title_text="Confidence", range=[0, 1.1], row=1, col=2)

    return fig

def create_confidence_distribution(findings: List[Dict]) -> Optional[go.Figure]:
    if not findings:
        return None

    confidences = [f['confidence'] for f in findings]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=confidences,
        nbinsx=20,
        marker_color='#2563eb',
        opacity=0.7,
        hovertemplate='Confidence: %{x:.0%}<br>Count: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title="Confidence Score Distribution",
        xaxis_title="Confidence Level",
        yaxis_title="Frequency",
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif")
    )

    return fig

def create_entity_network_graph(findings: List[Dict]) -> Optional[go.Figure]:
    if not findings:
        return None

    G = nx.Graph()
    drug_nodes = set()
    symptom_nodes = set()

    for finding in findings:
        drug = finding['drug']
        symptom = finding['effect']
        rel_type = finding['relationship']
        confidence = finding['confidence']

        drug_nodes.add(drug)
        symptom_nodes.add(symptom)

        edge_color = '#ef4444' if rel_type == 'adverse' else '#10b981'
        G.add_edge(drug, symptom, weight=confidence, color=edge_color, type=rel_type)

    pos = nx.spring_layout(G, k=2, iterations=50)

    edge_traces = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_traces.append(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=2, color=edge[2]['color']),
                hoverinfo='none',
                showlegend=False
            )
        )

    drug_x = [pos[node][0] for node in drug_nodes if node in pos]
    drug_y = [pos[node][1] for node in drug_nodes if node in pos]
    drug_text = [node for node in drug_nodes if node in pos]

    symptom_x = [pos[node][0] for node in symptom_nodes if node in pos]
    symptom_y = [pos[node][1] for node in symptom_nodes if node in pos]
    symptom_text = [node for node in symptom_nodes if node in pos]

    fig = go.Figure()

    for trace in edge_traces:
        fig.add_trace(trace)

    fig.add_trace(go.Scatter(
        x=drug_x,
        y=drug_y,
        mode='markers+text',
        name='Drugs',
        marker=dict(size=20, color='#3b82f6', symbol='square'),
        text=drug_text,
        textposition="middle center",
        hovertemplate='<b>%{text}</b><br>Drug<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=symptom_x,
        y=symptom_y,
        mode='markers+text',
        name='Symptoms',
        marker=dict(size=20, color='#f59e0b', symbol='circle'),
        text=symptom_text,
        textposition="middle center",
        hovertemplate='<b>%{text}</b><br>Symptom<extra></extra>'
    ))

    fig.update_layout(
        title="Drug-Symptom Relationship Network",
        showlegend=True,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        annotations=[dict(
            text="Red edges = Adverse, Green edges = Treatment",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.005, y=-0.002,
            xanchor="left", yanchor="bottom",
            font=dict(size=12, color="#666")
        )],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def create_entity_type_distribution(findings: List[Dict]) -> Optional[go.Figure]:
    if not findings:
        return None

    df = pd.DataFrame(findings)

    drug_counts = df['drug'].value_counts().head(10)
    symptom_counts = df['effect'].value_counts().head(10)

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Top Drugs by Frequency', 'Top Symptoms by Frequency'),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )

    fig.add_trace(
        go.Bar(
            x=drug_counts.values,
            y=drug_counts.index,
            orientation='h',
            marker_color='#3b82f6',
            name='Drugs',
            hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Bar(
            x=symptom_counts.values,
            y=symptom_counts.index,
            orientation='h',
            marker_color='#f59e0b',
            name='Symptoms',
            hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
        ),
        row=1, col=2
    )

    fig.update_layout(
        height=400,
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12)
    )

    fig.update_xaxes(title_text="Frequency", row=1, col=1)
    fig.update_xaxes(title_text="Frequency", row=1, col=2)
    fig.update_yaxes(title_text="Drug", row=1, col=1)
    fig.update_yaxes(title_text="Symptom", row=1, col=2)

    return fig

