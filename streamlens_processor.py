#!/usr/bin/env python3
"""
StreamLens Analytics Data Processing Pipeline
Advanced representation and bias analysis for streaming media content
Author: Cazandra Aporbo, MS
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
from collections import Counter
import networkx as nx
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import RobustScaler
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# Note: Removed spaCy and transformers imports to avoid dependency conflicts
# This simplified version focuses on the core statistical analysis


@dataclass
class MediaContent:
    """Represents a media content item with metadata"""
    id: str
    title: str
    platform: str
    genre: str
    release_year: int
    episodes: int
    runtime: float
    cast: List[Dict]
    dialogue_data: Optional[Dict] = None


class RepresentationAnalyzer:
    """Main analyzer for representation metrics"""

    def __init__(self):
        self.scaler = RobustScaler()  # Robust to outliers
        self.bias_detector = BiasDetector()
        self.network_analyzer = NetworkAnalyzer()

    def calculate_diversity_index(self, demographics: List[str]) -> float:
        """Calculate Shannon diversity index"""
        counts = Counter(demographics)
        total = sum(counts.values())
        if total == 0:
            return 0

        diversity = 0
        for count in counts.values():
            p = count / total
            if p > 0:
                diversity -= p * np.log(p)

        return diversity / np.log(len(counts)) if len(counts) > 1 else 0

    def calculate_gender_parity(self, gender_data: Dict) -> float:
        """Calculate gender parity index (0-1, where 1 is perfect parity)"""
        total = sum(gender_data.values())
        if total == 0:
            return 0

        female_ratio = gender_data.get('female', 0) / total
        return 1 - abs(0.5 - female_ratio) * 2

    def calculate_intersectionality_score(self, data: pd.DataFrame) -> Dict:
        """Calculate intersectional representation scores"""
        intersections = {}

        # Define intersectional groups
        for gender in ['male', 'female', 'non-binary']:
            for race in ['white', 'black', 'asian', 'hispanic', 'other']:
                for age in ['<30', '30-50', '>50']:
                    group_key = f"{gender}_{race}_{age}"

                    # Calculate representation vs population baseline
                    group_data = data[
                        (data['gender'] == gender) &
                        (data['race'] == race) &
                        (data['age_group'] == age)
                    ]

                    if len(group_data) > 0:
                        representation = len(group_data) / len(data)
                        # Simplified population baseline (would use real census data)
                        population_baseline = 1 / (3 * 5 * 3)
                        intersections[group_key] = {
                            'representation': representation,
                            'baseline': population_baseline,
                            'ratio': representation / population_baseline if population_baseline > 0 else 0,
                            'screen_time': group_data['screen_time'].mean() if 'screen_time' in group_data else 0
                        }

        return intersections


class BiasDetector:
    """Advanced bias detection using statistical and ML methods"""

    def __init__(self):
        self.models = {
            'gender_bias': RandomForestClassifier(n_estimators=100, random_state=42),
            'racial_bias': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'age_bias': RandomForestClassifier(n_estimators=100, random_state=42)
        }

    def detect_dialogue_bias(self, dialogue_data: Dict) -> Dict:
        """Detect bias in dialogue distribution and sentiment"""
        biases = {}

        # Analyze speaking time distribution
        word_counts = dialogue_data.get('word_counts', {})
        if not word_counts:
            return biases
        total_words = sum(word_counts.values())

        for demographic, word_count in word_counts.items():
            expected = total_words / len(word_counts)
            observed = word_count

            # Chi-square test statistic
            chi_square = ((observed - expected) ** 2) / expected if expected > 0 else 0

            biases[f'dialogue_{demographic}'] = {
                'observed': observed,
                'expected': expected,
                'bias_score': chi_square,
                'percentage': (observed / total_words * 100) if total_words > 0 else 0
            }

        return biases

    def detect_role_stereotyping(self, character_data: pd.DataFrame) -> Dict:
        """Detect stereotypical role assignments"""
        stereotypes = {}

        role_demographics = character_data.groupby(['role_type', 'gender']).size().unstack(fill_value=0)

        for role in role_demographics.index:
            role_data = role_demographics.loc[role]
            total = role_data.sum()

            if total > 0:
                # Calculate deviation from expected distribution
                expected = total / len(role_data)
                chi_square = sum(((role_data - expected) ** 2) / expected)

                stereotypes[role] = {
                    'distribution': role_data.to_dict(),
                    'chi_square': chi_square,
                    'stereotype_score': min(chi_square / 10, 1),  # Normalized score
                    'dominant_gender': role_data.idxmax()
                }

        return stereotypes

    def calculate_bechdel_extension(self, interactions: List[Dict]) -> Dict:
        """Extended Bechdel test for multiple dimensions"""
        results = {
            'classic_bechdel': False,
            'racial_bechdel': False,
            'age_bechdel': False,
            'lgbtq_bechdel': False
        }

        # Classic Bechdel: Two women talking about something other than a man
        female_interactions = [i for i in interactions if
                               i.get('char1_gender') == 'female' and
                               i.get('char2_gender') == 'female']

        non_romantic = [i for i in female_interactions if
                        'romantic' not in i.get('topic', '').lower() and
                        'relationship' not in i.get('topic', '').lower()]

        results['classic_bechdel'] = len(non_romantic) > 0

        # Similar tests for other dimensions
        minority_interactions = [i for i in interactions if
                                 i.get('char1_race') != 'white' and
                                 i.get('char2_race') != 'white']

        results['racial_bechdel'] = len(minority_interactions) > 5  # Threshold

        return results


class NetworkAnalyzer:
    """Analyze character interaction networks"""

    def build_character_network(self, interactions: List[Dict]) -> nx.Graph:
        """Build network graph from character interactions"""
        G = nx.Graph()

        for interaction in interactions:
            char1 = interaction['character1']
            char2 = interaction['character2']

            # Add nodes with attributes
            if not G.has_node(char1):
                G.add_node(char1, **interaction.get('char1_attrs', {}))
            if not G.has_node(char2):
                G.add_node(char2, **interaction.get('char2_attrs', {}))

            # Add or update edge
            if G.has_edge(char1, char2):
                G[char1][char2]['weight'] += interaction.get('weight', 1)
            else:
                G.add_edge(char1, char2, weight=interaction.get('weight', 1))

        return G

    def calculate_centrality_metrics(self, G: nx.Graph) -> pd.DataFrame:
        """Calculate various centrality metrics for characters"""
        metrics = pd.DataFrame()

        metrics['degree'] = pd.Series(dict(G.degree()))
        metrics['betweenness'] = pd.Series(nx.betweenness_centrality(G))
        metrics['eigenvector'] = pd.Series(nx.eigenvector_centrality(G, max_iter=1000))
        metrics['closeness'] = pd.Series(nx.closeness_centrality(G))

        # Add demographic data
        node_attrs = nx.get_node_attributes(G, 'gender')
        metrics['gender'] = pd.Series(node_attrs)

        node_attrs = nx.get_node_attributes(G, 'race')
        metrics['race'] = pd.Series(node_attrs)

        return metrics

    def detect_homophily(self, G: nx.Graph, attribute: str) -> float:
        """Calculate homophily (tendency for similar nodes to connect)"""
        try:
            coefficient = nx.attribute_assortativity_coefficient(G, attribute)
        except (nx.NetworkXError, ZeroDivisionError, ValueError, KeyError):
            return 0.0
        return 0.0 if np.isnan(coefficient) else float(coefficient)


class DataProcessor:
    """Main data processing pipeline"""

    def __init__(self):
        self.analyzer = RepresentationAnalyzer()
        self.platforms = ['netflix', 'amazon_prime', 'disney_plus', 'hbo_max', 'apple_tv', 'hulu']
        self.genres = ['drama', 'comedy', 'action', 'scifi', 'thriller', 'documentary']

    def generate_synthetic_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """Generate synthetic data for demonstration"""
        np.random.seed(42)

        data = []

        for i in range(n_samples):
            year = np.random.randint(2015, 2027)
            platform = np.random.choice(self.platforms)
            genre = np.random.choice(self.genres)

            # Create realistic bias patterns that slowly improve over time
            year_progress = (year - 2015) / 11
            gender_bias = (0.3 if genre == 'action' else 0.1) * (1 - 0.4 * year_progress)
            age_bias = (0.2 if genre == 'drama' else 0.05) * (1 - 0.3 * year_progress)

            # Generate character
            gender = np.random.choice(['male', 'female', 'non-binary'],
                                      p=[0.5 + gender_bias, 0.5 - gender_bias - 0.02, 0.02])

            race = np.random.choice(['white', 'black', 'asian', 'hispanic', 'other'],
                                    p=[0.6, 0.13, 0.06, 0.18, 0.03])

            age_group = np.random.choice(['<30', '30-50', '>50'],
                                         p=[0.4 + age_bias, 0.4, 0.2 - age_bias])

            # Calculate metrics with bias
            base_screen_time = 50 + np.random.normal(0, 20)
            screen_time = base_screen_time * (1.2 if gender == 'male' else 0.9 if gender == 'female' else 0.7)

            dialogue_words = int(screen_time * 20 + np.random.normal(0, 100))

            role_type = np.random.choice(['lead', 'support', 'minor'])

            # Sentiment based on role and demographics
            sentiment = 0.7 if role_type == 'lead' else 0.5
            sentiment += np.random.normal(0, 0.1)
            sentiment = np.clip(sentiment, 0, 1)

            data.append({
                'id': f'char_{i}',
                'platform': platform,
                'genre': genre,
                'year': year,
                'gender': gender,
                'race': race,
                'age_group': age_group,
                'role_type': role_type,
                'screen_time': max(0, screen_time),
                'dialogue_words': max(0, dialogue_words),
                'sentiment_score': sentiment,
                'centrality': np.random.beta(2, 5),  # Skewed distribution
                'is_protagonist': role_type == 'lead' and np.random.random() > 0.5
            })

        return pd.DataFrame(data)

    def process_data(self, df: pd.DataFrame) -> Dict:
        """Process data and calculate all metrics"""
        results = {
            'overall_metrics': {},
            'temporal_analysis': {},
            'platform_comparison': {},
            'genre_analysis': {},
            'bias_detection': {},
            'network_metrics': {}
        }

        # Overall metrics
        results['overall_metrics']['diversity_index'] = self.analyzer.calculate_diversity_index(
            df['race'].tolist()
        )

        gender_counts = df['gender'].value_counts().to_dict()
        results['overall_metrics']['gender_parity'] = self.analyzer.calculate_gender_parity(
            gender_counts
        )

        results['overall_metrics']['intersectionality'] = self.analyzer.calculate_intersectionality_score(df)

        # Temporal analysis
        yearly_metrics = []
        for year in sorted(df['year'].unique()):
            year_data = df[df['year'] == year]
            yearly_metrics.append({
                'year': year,
                'diversity': self.analyzer.calculate_diversity_index(year_data['race'].tolist()),
                'gender_parity': self.analyzer.calculate_gender_parity(
                    year_data['gender'].value_counts().to_dict()
                ),
                'avg_sentiment': year_data['sentiment_score'].mean()
            })

        results['temporal_analysis'] = pd.DataFrame(yearly_metrics).to_dict('records')

        # Genre analysis
        genre_metrics = []
        for genre in sorted(df['genre'].unique()):
            genre_data = df[df['genre'] == genre]
            leads = genre_data[genre_data['role_type'] == 'lead']
            male_leads = leads[leads['gender'] == 'male'].shape[0]
            dialogue_by_gender = genre_data.groupby('gender')['dialogue_words'].mean()
            male_dialogue = dialogue_by_gender.get('male', 0)
            female_dialogue = dialogue_by_gender.get('female', 0)
            genre_metrics.append({
                'genre': genre,
                'diversity': self.analyzer.calculate_diversity_index(genre_data['race'].tolist()),
                'gender_parity': self.analyzer.calculate_gender_parity(
                    genre_data['gender'].value_counts().to_dict()
                ),
                'male_lead_share': male_leads / leads.shape[0] if leads.shape[0] > 0 else 0,
                'dialogue_gap': (1 - female_dialogue / male_dialogue) if male_dialogue > 0 else 0,
                'avg_screen_time': genre_data['screen_time'].mean(),
                'sample_size': len(genre_data)
            })
        results['genre_analysis'] = genre_metrics

        # Platform comparison
        platform_metrics = []
        for platform in df['platform'].unique():
            platform_data = df[df['platform'] == platform]
            platform_metrics.append({
                'platform': platform,
                'diversity': self.analyzer.calculate_diversity_index(platform_data['race'].tolist()),
                'female_leads': (platform_data[
                    (platform_data['gender'] == 'female') &
                    (platform_data['role_type'] == 'lead')
                ].shape[0] / platform_data[platform_data['role_type'] == 'lead'].shape[0])
                if platform_data[platform_data['role_type'] == 'lead'].shape[0] > 0 else 0,
                'avg_screen_time_disparity': platform_data.groupby('gender')['screen_time'].mean().std()
            })

        results['platform_comparison'] = pd.DataFrame(platform_metrics).to_dict('records')

        # Bias detection
        bias_detector = BiasDetector()
        results['bias_detection']['role_stereotyping'] = bias_detector.detect_role_stereotyping(df)

        # Dialogue bias simulation
        dialogue_data = {
            'word_counts': df.groupby('gender')['dialogue_words'].sum().to_dict()
        }
        results['bias_detection']['dialogue_bias'] = bias_detector.detect_dialogue_bias(dialogue_data)

        # Network metrics: build an interaction network from a character sample
        network_analyzer = NetworkAnalyzer()
        rng = np.random.default_rng(42)
        sample = df.sample(min(200, len(df)), random_state=42).reset_index(drop=True)
        interactions = []
        for _ in range(min(400, len(sample) * 2)):
            i, j = rng.integers(0, len(sample), size=2)
            if i == j:
                continue
            c1, c2 = sample.iloc[int(i)], sample.iloc[int(j)]
            interactions.append({
                'character1': c1['id'],
                'character2': c2['id'],
                'weight': 1,
                'char1_attrs': {'gender': c1['gender'], 'race': c1['race']},
                'char2_attrs': {'gender': c2['gender'], 'race': c2['race']},
            })
        graph = network_analyzer.build_character_network(interactions)
        results['network_metrics'] = {
            'nodes': graph.number_of_nodes(),
            'edges': graph.number_of_edges(),
            'gender_homophily': network_analyzer.detect_homophily(graph, 'gender'),
            'racial_homophily': network_analyzer.detect_homophily(graph, 'race'),
            'density': nx.density(graph) if graph.number_of_nodes() > 1 else 0,
        }

        # Generated narrative insights
        results['insights'] = self.generate_insights(df, results)

        return results

    def generate_insights(self, df: pd.DataFrame, results: Dict) -> List[Dict]:
        """Generate human-readable findings from computed metrics"""
        insights = []

        temporal = results['temporal_analysis']
        if len(temporal) >= 2:
            delta = temporal[-1]['gender_parity'] - temporal[0]['gender_parity']
            direction = 'improved' if delta >= 0 else 'declined'
            insights.append({
                'category': 'trend',
                'title': 'Gender parity over time',
                'detail': (f"Gender parity has {direction} by {abs(delta):.2f} points "
                           f"between {temporal[0]['year']} and {temporal[-1]['year']}."),
            })

        platforms = results['platform_comparison']
        if platforms:
            best = max(platforms, key=lambda p: p['diversity'])
            worst = min(platforms, key=lambda p: p['diversity'])
            insights.append({
                'category': 'platform',
                'title': 'Platform diversity gap',
                'detail': (f"{best['platform'].replace('_', ' ').title()} leads on diversity "
                           f"({best['diversity']:.2f}) while {worst['platform'].replace('_', ' ').title()} "
                           f"trails ({worst['diversity']:.2f})."),
            })

        genres = results.get('genre_analysis', [])
        if genres:
            most_biased = max(genres, key=lambda g: g['male_lead_share'])
            insights.append({
                'category': 'genre',
                'title': 'Genre lead-role skew',
                'detail': (f"{most_biased['genre'].title()} has the highest male lead share at "
                           f"{most_biased['male_lead_share'] * 100:.0f}% of lead roles."),
            })
            widest_gap = max(genres, key=lambda g: g['dialogue_gap'])
            insights.append({
                'category': 'dialogue',
                'title': 'Dialogue gap by genre',
                'detail': (f"In {widest_gap['genre']}, female characters average "
                           f"{widest_gap['dialogue_gap'] * 100:.0f}% fewer dialogue words than male characters."),
            })

        leads = df[df['role_type'] == 'lead']
        if len(leads) > 0:
            woc = leads[(leads['gender'] == 'female') & (leads['race'] != 'white')]
            insights.append({
                'category': 'intersectional',
                'title': 'Intersectional representation',
                'detail': (f"Women of color hold {len(woc) / len(leads) * 100:.0f}% "
                           f"of lead roles across the dataset."),
            })

        network = results.get('network_metrics', {})
        if network:
            insights.append({
                'category': 'network',
                'title': 'Interaction homophily',
                'detail': (f"Gender homophily in interaction networks is "
                           f"{network['gender_homophily']:.2f} "
                           f"(positive values mean characters interact mostly within their own group)."),
            })

        return insights

    def export_results(self, results: Dict, filename: str = 'analysis_results.json'):
        """Export results to JSON file"""
        # Convert numpy types for JSON serialization
        def convert_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {str(k): convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_types(i) for i in obj]
            return obj

        clean_results = convert_types(results)

        with open(filename, 'w') as f:
            json.dump(clean_results, f, indent=2)

        print(f"Results exported to {filename}")

        return clean_results


def main():
    """Main execution function"""
    print("=" * 60)
    print("StreamLens Analytics - Streaming Media Bias Analysis")
    print("Author: Cazandra Aporbo, MS")
    print("=" * 60)

    # Initialize processor
    processor = DataProcessor()

    # Generate synthetic data
    print("\nGenerating synthetic dataset...")
    df = processor.generate_synthetic_data(n_samples=5000)
    print(f"Generated {len(df)} character records")

    # Process data
    print("\nAnalyzing representation and bias...")
    results = processor.process_data(df)

    # Display key findings
    print("\nKey Findings:")
    print("-" * 40)

    overall = results['overall_metrics']
    print(f"Diversity Index: {overall['diversity_index']:.3f}")
    print(f"Gender Parity: {overall['gender_parity']:.3f}")

    # Temporal trends
    temporal = pd.DataFrame(results['temporal_analysis'])
    if not temporal.empty:
        trend = temporal['diversity'].iloc[-1] - temporal['diversity'].iloc[0]
        print(f"Diversity Trend (10yr): {'+' if trend > 0 else ''}{trend:.3f}")

    # Platform comparison
    platforms = pd.DataFrame(results['platform_comparison'])
    if not platforms.empty:
        best_platform = platforms.loc[platforms['diversity'].idxmax(), 'platform']
        best_score = platforms['diversity'].max()
        print(f"Most Diverse Platform: {best_platform.replace('_', ' ').title()} ({best_score:.3f})")

    # Bias detection
    print("\nBias Detection Results:")
    print("-" * 40)

    dialogue_bias = results['bias_detection']['dialogue_bias']
    for demo, bias_data in dialogue_bias.items():
        if 'percentage' in bias_data:
            print(f"{demo}: {bias_data['percentage']:.1f}% of dialogue")

    # Export results
    print("\nExporting results...")
    processor.export_results(results)

    print("\nAnalysis complete!")
    print("Run `python app.py` and open http://localhost:8000 for the interactive dashboard")


if __name__ == "__main__":
    main()
