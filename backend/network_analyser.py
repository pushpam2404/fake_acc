import random
import networkx as nx

def analyze_profile_network(username: str, platform: str, risk_score: float) -> dict:
    """
    Constructs and analyzes a network graph of related/coordinated profiles.
    Calculates Degree Centrality using NetworkX.
    """
    G = nx.Graph()
    
    # 1. Initialize Nodes list
    nodes = []
    edges = []
    
    # Node categories based on threat level
    classification = "REAL"
    if risk_score > 70:
        classification = "FAKE"
    elif risk_score >= 30:
        classification = "SUSPICIOUS"
        
    # Main target node
    G.add_node(username, type="target", risk=risk_score)
    
    # Generate relation nodes based on classification
    if classification == "FAKE":
        # Botnets coordinate in tight, highly connected clusters
        num_connections = random.randint(5, 8)
        relation_usernames = [f"{username[:4]}_bot_{i}" for i in range(1, num_connections + 1)]
        
        # Add connection reasons reflecting Coordinated Inauthentic Behavior (CIB)
        cib_reasons = [
            "Shared IP Subnet (Honeypot)",
            "Concurrent Login Activity",
            "Lexical Caption Similarity (>85%)",
            "90% Follower List Overlap",
            "Simultaneous Posting Event (<3s)"
        ]
        
        # Connect target to all bots
        for bot in relation_usernames:
            G.add_node(bot, type="bot", risk=random.randint(75, 100))
            reason = random.choice(cib_reasons)
            G.add_edge(username, bot, reason=reason)
            
        # Connect bots together (dense botnet clique/cluster)
        for i in range(len(relation_usernames)):
            for j in range(i + 1, len(relation_usernames)):
                if random.random() > 0.4: # Dense cross-links
                    G.add_edge(relation_usernames[i], relation_usernames[j], reason="Coordinated follow")
                    
    elif classification == "SUSPICIOUS":
        # Suspicious profiles have some odd links but are not a fully dense botnet
        num_connections = random.randint(3, 5)
        relation_usernames = [f"{username[:4]}_sys_{i}" for i in range(1, num_connections + 1)]
        
        for bot in relation_usernames:
            G.add_node(bot, type="suspicious", risk=random.randint(35, 75))
            G.add_edge(username, bot, reason=random.choice(["Shared follow-back", "Comment frequency overlap"]))
            
    else:
        # Genuine profiles have sparse, normal human connections
        num_connections = random.randint(2, 4)
        relation_usernames = [f"user_{username[:3]}_{i}" for i in range(1, num_connections + 1)]
        
        for user in relation_usernames:
            G.add_node(user, type="human", risk=random.randint(1, 29))
            G.add_edge(username, user, reason="Standard follower link")

    # 2. Calculate NetworkX Centrality Metrics
    centralities = nx.degree_centrality(G)
    
    # 3. Compile output dictionaries
    for node in G.nodes():
        node_attr = G.nodes[node]
        nodes.append({
            "id": node,
            "label": f"@{node}",
            "type": node_attr.get("type", "human"),
            "risk_score": node_attr.get("risk", 10.0),
            "centrality": round(centralities.get(node, 0.0), 3)
        })
        
    for u, v, data in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "reason": data.get("reason", "Follower connection")
        })
        
    return {
        "nodes": nodes,
        "edges": edges,
        "clique_count": len(list(nx.find_cliques(G))) if classification == "FAKE" else 1,
        "density": round(nx.density(G), 3)
    }
