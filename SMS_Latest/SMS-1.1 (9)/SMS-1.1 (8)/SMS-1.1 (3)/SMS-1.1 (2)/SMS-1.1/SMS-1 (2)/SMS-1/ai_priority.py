"""
AI Complaint Priority Classifier
Simple NLP-based system to classify complaint priority levels
"""

import re

# Define keywords for each priority level with weights
URGENT_KEYWORDS = {
    # Water related emergencies
    'leak': 10, 'leaking': 10, 'overflow': 10, 'flooding': 10, 'flood': 10,
    'water': 8, 'tap': 8, 'pipe': 8, 'burst': 10, 'broken': 8,
    
    # Electrical emergencies
    'electricity': 9, 'power': 8, 'shock': 10, 'short': 9, 'circuit': 8,
    'outage': 9, 'blackout': 10, 'no power': 10, 'wiring': 8,
    
    # Lift/Stuck emergencies
    'lift': 10, 'elevator': 10, 'stuck': 10, 'trap': 10, 'trapped': 10,
    'stuck inside': 10, 'cannot move': 10,
    
    # Security/Safety emergencies
    'break': 9, 'burglar': 10, 'theft': 9, 'robbery': 10, 'intruder': 10,
    'emergency': 9, 'urgent': 8, 'immediately': 8, 'asap': 7, 'now': 7,
    
    # Fire/Safety hazards
    'fire': 10, 'smoke': 9, 'burning': 10, 'gas leak': 10, 'explosion': 10,
    
    # Medical emergencies
    'medical': 9, 'ambulance': 10, 'hospital': 8, 'injury': 9, 'accident': 9
}

MEDIUM_KEYWORDS = {
    # Maintenance issues
    'repair': 7, 'fix': 7, 'broken': 6, 'damage': 7, 'damaged': 7,
    'not working': 7, 'malfunction': 8, 'fault': 7, 'issue': 6,
    
    # Noise complaints
    'noise': 7, 'loud': 6, 'sound': 5, 'disturb': 7, 'disturbing': 7,
    'music': 5, 'party': 6, 'construction': 7,
    
    # Parking issues
    'parking': 6, 'car': 5, 'vehicle': 5, 'blocking': 7,
    
    # General maintenance
    'maintenance': 7, 'service': 6, 'clean': 5, 'dirty': 6,
    
    # Common area issues
    'common area': 6, 'hallway': 6, 'corridor': 6, 'lobby': 6,
    
    # Plumbing issues (non-emergency)
    'drain': 6, 'clogged': 7, 'block': 6, 'slow': 5
}

NORMAL_KEYWORDS = {
    # General inquiries
    'information': 4, 'question': 4, 'help': 4, 'assistance': 4,
    'guidance': 4, 'direction': 4,
    
    # Suggestions
    'suggestion': 5, 'idea': 4, 'improvement': 5, 'better': 4,
    
    # General complaints
    'complaint': 4, 'dislike': 4, 'unhappy': 4, 'dissatisfied': 5,
    
    # Requests
    'request': 4, 'please': 3, 'would like': 4, 'want': 3,
    
    # Feedback
    'feedback': 4, 'opinion': 4, 'thought': 3
}

def preprocess_text(text):
    """Preprocess complaint text for analysis"""
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text

def calculate_priority_score(complaint_text):
    """Calculate priority score based on keywords"""
    if not complaint_text:
        return 0.0
    
    # Preprocess text
    processed_text = preprocess_text(complaint_text)
    
    # Initialize scores
    urgent_score = 0
    medium_score = 0
    normal_score = 0
    
    # Check for urgent keywords
    for keyword, weight in URGENT_KEYWORDS.items():
        if keyword in processed_text:
            urgent_score += weight
    
    # Check for medium keywords
    for keyword, weight in MEDIUM_KEYWORDS.items():
        if keyword in processed_text:
            medium_score += weight
    
    # Check for normal keywords
    for keyword, weight in NORMAL_KEYWORDS.items():
        if keyword in processed_text:
            normal_score += weight
    
    # Calculate total score (weighted)
    total_score = (urgent_score * 3) + (medium_score * 2) + normal_score
    
    return total_score

def classify_priority(complaint_text):
    """Classify complaint priority level"""
    score = calculate_priority_score(complaint_text)
    
    # Thresholds for classification
    if score >= 25:  # High urgency keywords present
        return 'High', score
    elif score >= 10:  # Medium urgency keywords present
        return 'Normal', score
    else:  # Low urgency or general inquiry
        return 'Low', score

def get_priority_color(priority):
    """Get color code for priority level"""
    colors = {
        'High': 'danger',    # Red
        'Normal': 'warning',   # Yellow
        'Low': 'success'    # Green
    }
    return colors.get(priority, 'secondary')

def get_priority_badge(priority):
    """Get badge text with emoji for priority level"""
    badges = {
        'High': '🔴 High',
        'Normal': '🟡 Normal',
        'Low': '🟢 Low'
    }
    return badges.get(priority, priority)

# Example usage:
# priority, score = classify_priority("There is water leaking from the pipe in apartment A-101")
# print(f"Priority: {priority}, Score: {score}")