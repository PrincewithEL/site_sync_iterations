from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Sample Predefined Questions and Answers
questions = [
    "How do I reset my password?", 
    "Where can I view my tasks?", 
    "How do I contact support?", 
    "Send a project kickoff meeting email", 
    "Send a project progress update email", 
    "Send a request for information email", 
    "Send a change order notification email", 
    "Send a project completion notification email"
]

answers = [
    "To reset your password, go to settings...", 
    "You can view your tasks in the Tasks section...", 
    "Contact support via email at support@example.com...", 

    """
    Subject: Project Kickoff Meeting - [Project Name]

    Dear Team,

    I hope this message finds you well.

    We are pleased to announce the kickoff of the [Project Name]. Our initial meeting is scheduled for [Date] at [Time] in [Location/Online Platform]. This meeting will cover the project scope, objectives, timelines, roles, and responsibilities.

    Please review the attached agenda and come prepared with any questions or input you may have. We look forward to collaborating with you on this project.

    Best regards,  
    [Your Name]  
    [Your Position]  
    [Your Company]  
    [Contact Information]
    """,

    """
    Subject: Project Progress Update - [Project Name]

    Dear Team,

    I wanted to provide you with an update on the progress of the [Project Name]. As of [Date], we have accomplished the following:

    - [Key Milestone 1]
    - [Key Milestone 2]
    - [Key Milestone 3]

    The upcoming tasks are:

    - [Task 1]
    - [Task 2]
    - [Task 3]

    We are on track with our project schedule, and I appreciate everyone’s hard work and dedication. If you have any questions or concerns, please feel free to reach out.

    Thank you for your continued support.

    Best regards,  
    [Your Name]  
    [Your Position]  
    [Your Company]  
    [Contact Information]
    """,

    """
    Subject: Request for Information - [Project Name]

    Dear [Recipient's Name],

    I hope you are doing well.

    We require additional information regarding [specific aspect of the project]. Please provide the following details by [Due Date]:

    - [Specific Information 1]
    - [Specific Information 2]
    - [Specific Information 3]

    Your prompt response will help us stay on schedule and ensure the smooth progress of the project. Should you need any clarification, do not hesitate to contact me.

    Thank you in advance for your cooperation.

    Best regards,  
    [Your Name]  
    [Your Position]  
    [Your Company]  
    [Contact Information]
    """,

    """
    Subject: Change Order Notification - [Change Order Number]

    Dear [Recipient's Name],

    This email is to inform you of a change order for the [Project Name]. The details of the change are as follows:

    - **Change Order Number:** [Change Order Number]
    - **Description of Change:** [Brief Description]
    - **Impact on Cost:** [Cost Impact]
    - **Impact on Schedule:** [Schedule Impact]

    Please review the attached documentation and confirm your acceptance of these changes. If you have any questions or need further clarification, please let me know.

    Thank you for your attention to this matter.

    Best regards,  
    [Your Name]  
    [Your Position]  
    [Your Company]  
    [Contact Information]
    """,
    
    """
    Subject: Project Completion Notification - [Project Name]

    Dear Team,

    I am pleased to announce that the [Project Name] has been successfully completed as of [Completion Date]. The project has met its objectives, and all deliverables have been finalized.

    Please find the final project report and documentation attached. We will be conducting a project debrief meeting on [Date] to discuss the project outcomes and lessons learned.

    Thank you all for your hard work and dedication throughout the project. It has been a pleasure working with you.

    Best regards,  
    [Your Name]  
    [Your Position]  
    [Your Company]  
    [Contact Information]
    """
]


# Threshold for low similarity
SIMILARITY_THRESHOLD = 0.2  # You can adjust this threshold as needed

def get_response(user_query):
    # Preprocess and vectorize
    vectorizer = TfidfVectorizer().fit_transform(questions + [user_query])
    vectors = vectorizer.toarray()
    
    # Calculate similarity
    similarity = cosine_similarity([vectors[-1]], vectors[:-1])
    
    # Get the best matching question
    best_match_idx = similarity.argmax()
    best_match_score = similarity[0][best_match_idx]
    
    # Check if the similarity score is below the threshold
    if best_match_score < SIMILARITY_THRESHOLD:
        return (
            "I'm sorry, I couldn't find an answer to your question. "
            "Please contact our support team for further assistance: "
            "sitesync2024@gmail.com OR 0700000000."
        )
    
    return answers[best_match_idx]

# Example user input
user_input = "How can I change my password?"
response = get_response(user_input)
print(response)

