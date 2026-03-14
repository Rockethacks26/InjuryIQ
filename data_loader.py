import pandas as pd

df = pd.read_csv('player_injuries_impact.csv')

def get_injury_context(position=None, age=None, injury_type=None):
    """Find similar players from dataset to give Gemini real context"""
    filtered = df.copy()
    
    # Filter by position if provided
    if position:
        filtered = filtered[filtered['Position'].str.contains(position, case=False, na=False)]
    
    # Filter by age range if provided
    if age:
        filtered = filtered[
            (filtered['Age'] >= age - 3) & 
            (filtered['Age'] <= age + 3)
        ]
    
    # Filter by injury type if provided
    if injury_type:
        filtered = filtered[filtered['Injury'].str.contains(injury_type, case=False, na=False)]
    
    if filtered.empty:
        filtered = df.sample(min(5, len(df)))
    
    # Build context string for Gemini
    context = "REAL PREMIER LEAGUE INJURY DATA (2019-2023):\n"
    for _, row in filtered.head(5).iterrows():
        context += f"- {row['Name']} ({row['Position']}, Age {row['Age']}): "
        context += f"suffered {row['Injury']} on {row['Date of Injury']}. "
        context += f"FIFA rating: {row['FIFA rating']}\n"
    
    # Get most common injuries for this position
    if not filtered.empty:
        common_injuries = filtered['Injury'].value_counts().head(3)
        context += f"\nMost common injuries for this profile:\n"
        for injury, count in common_injuries.items():
            context += f"  - {injury}: {count} cases\n"
    
    return context

def get_injury_stats():
    """Get overall injury statistics"""
    stats = {
        "total_records": len(df),
        "most_common_injuries": df['Injury'].value_counts().head(5).to_dict(),
        "positions": df['Position'].value_counts().to_dict()
    }
    return stats

if __name__ == "__main__":
    print(get_injury_context(position="Forward", age=25))
    print("\n---\n")
    print(get_injury_stats())