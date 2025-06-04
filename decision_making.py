from langchain.tools import Tool

def decision_agent(candidate_category):
    """Makes dynamic decisions based on candidate category."""
    
    if "High Fit" in candidate_category:
        return "Send Interview Invite"
    elif "Medium Fit" in candidate_category:
        return "Send to HR for Manual Review"
    else:
        return "Send Rejection Email"


decision_tool = Tool(
    name="Decision-Making Agent",
    func=decision_agent,
    description="Decides next steps for candidates"
)
