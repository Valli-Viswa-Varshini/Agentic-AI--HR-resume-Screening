from langchain.tools import Tool


def categorize_candidate(score):
    """Categorizes candidates dynamically based on AI-generated rules."""
    

    print(f"Received score: {score} (Type: {type(score)})") 
    
    try:

        score = float(score) 
        print(f"Converted score: {score} (Type: {type(score)})") 

        if score >= 80:
            return "High Fit (Selected for Interview)"
        elif 60 <= score < 80:
            return "Medium Fit (Needs HR Review)"
        else:
            return "Underfit (Not Suitable)"

    
    except ValueError:
        
        return f"Invalid Score Format: {score}"  

# Testing with score 100
#print(categorize_candidate(100))  # Expected: High Fit (Selected for Interview)


categorization_tool = Tool(
    name="Candidate Categorization Agent",
    func=categorize_candidate,
    description="Classifies candidates based on AI-generated matching scores"
)
