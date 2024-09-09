from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Sample Predefined Questions and Answers
questions = [
    "Hi", "Hello", "Hey",
    "How do I reset my password?", 
    "Where can I view my tasks?", 
    "How do I contact support?", 
    "Send a project kickoff meeting email", 
    "Send a project progress update email", 
    "Send a request for information email", 
    "Send a change order notification email", 
    "Send a project completion notification email",
    "How to recover permanently deleted files",
    "Where can I find the active projects?",
    "Where can I find the completed projects?",
    "Where can I find the bookmarked projects?",
    "Where can I find the deleted projects?",
    "How do I access the chat room?",
    "How do I view resources?",
    "How do I view transactions?",
    "How do I view tasks and events?",
    "How do I view dashboards?",
    "How do I view unread messages?",
    "How do I view pending tasks?",
    "How do I make a project starred?",
    "How do I bookmark a project?",
    "How do I unbookmark a project?",
    "How do I unstar a project?",
    "How do I delete a project?",
    "How do I filter projects?",
    "How do I search for a project?",
    "How to create a project",
    "How to enter a project name",
    "How to enter a Start Date",
    "How to enter a Project Image",
    "How to enter a End Date",
    "How to enter a Estimated Budget",
    "How to enter a Project Details",
    "How to submit project form",
    "How to reset project form",
    "How to exit out of the project form",
    "How to bookmark chats",
    "How to send text",
    "How to edit a message",
    "How to delete a message",
    "How to add files",
    "How to add emoji",
    "How to add reactions",
    "How to remove a project member",
    "How to go to move to view resources, transactions, dashboard, events & tasks",
    "How to edit a project",
    "How to view transactions",
    "How to view resources",
    "How to view group chat",
    "How to view tasks and events",
    "How to add a member to a project",
    "How to search for events",
    "How to view the gantt charts",
    "How to filter events",
    "How to add a task",
    "How to add an event",
    "How to add a resource",
    "How to filter resources",
    "How to search for resources",
    "How to add a file",
    "How to bookmark a file",
    "How to delete a file",
    "How to unbookmark a file",
    "How to search for a file",
    "How to add a Transaction",
    "How to filter Transactions",
    "How to search for a Transaction",
    "How to return to the home page, project page"
]

answers = [
    "Hello, I am doing well, hope you are too. How can I help?", "Hey there, I am doing well, hope you are too. Where can I be of assistance...", "Hi, I am doing well, hope you are too. I am a virtual assistant. Feel free to ask me for help!",
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

    We are on track with our project schedule, and I appreciate everyone's hard work and dedication. If you have any questions or concerns, please feel free to reach out.

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
    """,
    
    "Unfortunately, permanently deleted files cannot be recovered once they are removed from the system. Ensure that you back up important files.",
    "The active projects are located on the middle left-hand side of the screen. You'll see a list of projects on the second row.",
    "The completed projects are located on the middle left-hand side of the screen, on the fifth row.",
    "The bookmarked projects are located on the middle left-hand side of the screen, on the fifth row.",
    "The deleted projects are located on the middle left-hand side of the screen, on the sixth row.",
    "Click on the 'Select' option and scroll down. You'll see the chat room as the first option.",
    "Click on the 'Select' option and scroll down. You'll see 'View Resources' as the second option.",
    "Click on the 'Select' option and scroll down. You'll see 'View Transactions' as the third option.",
    "Click on the 'Select' option and scroll down. You'll see 'Tasks and Events' as the last option.",
    "Click on the 'Select' option and scroll down. You'll see 'Dashboards' as the fourth option.",
    "In the middle of the page, click on the value (2).",
    "In the middle of the page, click on the value (3).",
    "Click on the star icon, and make sure it turns red.",
    "Select the project with the checkbox and then click on 'Bookmark.'",
    "Select the project with the checkbox, then click on 'Unbookmark.'",
    "Select the starred project, and make sure it is unhighlighted.",
    "Select the project with the checkbox and click on 'Delete.'",
    "Click on 'All time All Projects,' select the desired segment, and click the 'Apply Filter' button.",
    "On the top right, click on the search icon and filter.",
    "On the top left, click the 'Create a New Project' button and fill in the details.",
    "Enter the project name in the designated text box on the project creation form.",
    "Select the start date from the calendar picker in the project creation form.",
    "Upload or select the project image using the 'Upload Image' option in the project creation form.",
    "Select the end date from the calendar picker in the project creation form.",
    "Input the estimated budget in the budget field within the project creation form.",
    "Add the project details in the description box provided in the project creation form.",
    "After filling in all the required information, click on the 'Submit' button to finalize the project creation.",
    "Click on the 'Reset' button to clear all fields in the project creation form.",
    "Click on the 'Cancel' or 'Close' button to exit the project form without saving.",
    "To bookmark a chat, click on the three dots next to the chat you want to bookmark and select the 'Bookmark' option.",
    "To send a text, type your message in the text input box at the bottom of the chat window and press the 'Enter' key or click on the 'Send' button.",
    "Right-click on the message and click on the 'Edit' button.",
    "Right-click on the message and click on the 'Delete' button.",
    "On the bottom left of the chat area, click on the paperclip icon and select your desired file.",
    "On the bottom right of the chat area, click on the emoji icon and select your desired emoji.",
    "To add a reaction, hover over the message you want to react to and click on the emoji icon that appears, then choose the appropriate reaction.",
    "On the middle left of the page, click on the cancel button next to the member's name.",
    "Click on the 'Back' or 'Home' button.",
    "Click on 'Edit Project' on the top left, second row after the Home button.",
    "Click on 'View Transactions' on the project page.",
    "Click on 'View Resources' on the project page.",
    "Click on 'View All' to see the group chat.",
    "Click on the 'View Tasks and Events' button on the project page.",
    "On the middle left-hand side of the screen, click on the plus button to add a member.",
    "Use the search bar at the top of the 'Events' page to search for specific events.",
    "Click on the '+Full View' button on the page to view the Gantt charts.",
    "Click on the 'All Time All Projects' dropdown menu and select the filter you need, then click the 'Apply Filter' button.",
    "Click on the 'Add Task' button on the tasks page and fill out the necessary details in the form that appears.",
    "On the events page, click on the 'Add Event' button, fill in the required details, and submit to create a new event.",
    "To add a resource, click on the 'Add Resource' button on the resource page, upload the desired file or link, and provide necessary details.",
    "Click on 'All Time All Projects,' select the desired segment, and click on the 'Apply Filter' button.",
    "On the top right of the resource page, use the search bar to find specific resources.",
    "On the resources page, click on 'Add File,' select the file you want to upload, and provide a description if necessary.",
    "Select the file with the checkbox, then click on 'Bookmark.'",
    "Select the file with the checkbox, then click on 'Delete' to remove it from the resources page.",
    "Select the project with the checkbox and then click on UnBookmark",
    "Use the search bar at the top right of the resources page to look for specific files.",
    "On the 'Transactions' page, click on the 'Add Transaction' button and fill out the transaction details in the form provided.",
    "Click on 'All Time All Projects,' select the specific filter you'd like to apply, and click 'Apply Filter.'",
    "Use the search bar at the top right of the transactions page to look for specific transactions.",
    "Click on the 'Home' or 'Back' button to return to the home page or project page."
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

