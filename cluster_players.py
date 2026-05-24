import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import os

def cluster_players():
    print("Starting Phase 4: KMeans Clustering...")
    
    features_path = 'player_features.csv'
    if not os.path.exists(features_path):
        print(f"Error: {features_path} not found. Please run player_pipeline.py first.")
        return
        
    df = pd.read_csv(features_path)
    
    cluster_features = ['total_goals', 'total_assists', 'total_minutes_played', 
                        'avg_goals_per_game', 'avg_assists_per_game']
                        
    # Ensure no missing values in clustering features
    df = df.dropna(subset=cluster_features).copy()
    
    X = df[cluster_features]
    
    # Normalize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # KMeans
    kmeans = KMeans(n_clusters=4, random_state=42, n_init='auto')
    df['raw_cluster'] = kmeans.fit_predict(X_scaled)
    
    # Assign labels based on cluster centers (heuristic)
    # We examine the cluster centers to map them to predefined descriptions
    # Note: cluster centers shape is (4, 5) corresponding to cluster_features
    centers = kmeans.cluster_centers_
    
    # Map clusters to labels based on their characteristics
    # total_goals (0), total_assists (1), total_minutes (2), avg_goals (3), avg_assists (4)
    # This logic roughly maps the requirements:
    labels = {}
    remaining_clusters = [0, 1, 2, 3]
    
    # 1. Clinical Striker: Highest avg_goals
    striker_cluster = max(remaining_clusters, key=lambda c: centers[c][3])
    labels[striker_cluster] = "Clinical Striker"
    remaining_clusters.remove(striker_cluster)
    
    # 2. Playmaker: Highest avg_assists among remaining
    playmaker_cluster = max(remaining_clusters, key=lambda c: centers[c][4])
    labels[playmaker_cluster] = "Playmaker"
    remaining_clusters.remove(playmaker_cluster)
    
    # 3. Workhorse: Highest total_minutes among remaining
    workhorse_cluster = max(remaining_clusters, key=lambda c: centers[c][2])
    labels[workhorse_cluster] = "Workhorse"
    remaining_clusters.remove(workhorse_cluster)
    
    # 4. Rotation Player: The last one (usually lowest minutes/contribution)
    rotation_cluster = remaining_clusters[0]
    labels[rotation_cluster] = "Rotation Player"
    
    df['cluster_label'] = df['raw_cluster'].map(labels)
    df = df.drop(columns=['raw_cluster'])
    
    # Save
    df.to_csv('player_clustered.csv', index=False)
    print("Phase 4 Complete: player_clustered.csv saved successfully.")

if __name__ == "__main__":
    cluster_players()
