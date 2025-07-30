"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
from pymongo import MongoClient

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mergington_high']
activities_collection = db['activities']

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Initialize database with activities if empty
def init_db():
    if activities_collection.count_documents({}) == 0:
        # Initial activities data to insert
        activities_to_insert = [
            {
                "name": name,
                **details
            } for name, details in {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    # Sports related activities
    "Soccer Team": {
        "description": "Join the school soccer team and compete in local leagues",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 18,
        "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
    },
    "Basketball Club": {
        "description": "Practice basketball skills and play friendly matches",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["liam@mergington.edu", "ava@mergington.edu"]
    },
    # Artistic activities
    "Drama Club": {
        "description": "Participate in school plays and improve acting skills",
        "schedule": "Mondays, 3:30 PM - 5:00 PM",
        "max_participants": 20,
        "participants": ["charlotte@mergington.edu", "jack@mergington.edu"]
    },
    "Art Workshop": {
        "description": "Explore painting, drawing, and other visual arts",
        "schedule": "Fridays, 2:00 PM - 3:30 PM",
        "max_participants": 16,
        "participants": ["amelia@mergington.edu", "benjamin@mergington.edu"]
    },
    # Intellectual activities
    "Math Olympiad": {
        "description": "Prepare for math competitions and solve challenging problems",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 10,
        "participants": ["ethan@mergington.edu", "isabella@mergington.edu"]
    },
    "Science Club": {
        "description": "Conduct experiments and explore scientific concepts",
        "schedule": "Wednesdays, 4:00 PM - 5:00 PM",
        "max_participants": 14,
        "participants": ["noah@mergington.edu", "grace@mergington.edu"]
    }
}.items()]
        activities_collection.insert_many(activities_to_insert)

# Initialize the database on startup
init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

@app.get("/activities")
def get_activities():
    # Convert MongoDB cursor to dictionary
    activities_dict = {}
    for activity in activities_collection.find():
        # Remove MongoDB's _id field and store with activity name as key
        activity_data = activity.copy()
        del activity_data['_id']
        activities_dict[activity_data['name']] = {
            "description": activity_data['description'],
            "schedule": activity_data['schedule'],
            "max_participants": activity_data['max_participants'],
            "participants": activity_data['participants']
        }
    return activities_dict

@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Find the activity
    activity = activities_collection.find_one({"name": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Atomically validate and add student to activity
    result = activities_collection.update_one(
        {
            "name": activity_name,
            "participants": {"$ne": email},  # Ensure student is not already signed up
            "$expr": {"$lt": [{"$size": "$participants"}, "$max_participants"]}  # Ensure activity is not full
        },
        {"$addToSet": {"participants": email}}  # Add student to participants
    )

    if result.modified_count == 1:
        return {"message": f"Successfully signed up for {activity_name}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to sign up for activity")

@app.delete("/activities/{activity_name}/signup")
async def remove_from_activity(activity_name: str, email: str):
    """Remove a student from an activity"""
    # Find the activity
    activity = activities_collection.find_one({"name": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    # Remove student from activity
    result = activities_collection.update_one(
        {"name": activity_name},
        {"$pull": {"participants": email}}
    )

    if result.modified_count == 1:
        return {"message": f"Successfully removed from {activity_name}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to remove from activity")
