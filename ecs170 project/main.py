from constraint import Problem
import pickle
import copy
import major_reqs
from major_reqs import CourseNode

# Initialize the CSP
problem = Problem()

# Array of courses the student has already taken
courses_taken = ["Math", "Biology"]

# Define course data with time slots, prerequisites, and units
course_data = {
    "Math": {
        "slots": [
            [(2, 16, 18), (4, 16, 18)],  # Tuesday & Thursday 4-6pm
            [(1, 13, 15), (3, 13, 15)]   # Monday & Wednesday 1-3pm
        ],
        "prerequisites": [],
        "units": 4,
        "course_type": "STEM",
    },
    "Biology": {
        "slots": [
            [(2, 8, 10), (4, 8, 10)]    # Tuesday & Thursday 8-10am
        ],
        "prerequisites": [],
        "units": 3,
        "course_type": "STEM",
    },
    "Physics": {
        "slots": [
            [(1, 11, 13), (3, 11, 13)],  # Monday & Wednesday 11am-1pm
            [(2, 10, 12), (4, 10, 12)]   # Tuesday & Thursday 10am-12pm
        ],
        "prerequisites": [["Math"]],
        "units": 5,
        "course_type": "STEM",
    },
    "ComputerScience": {
        "slots": [
            [(2, 14, 16), (4, 14, 16)],  # Tuesday & Thursday 2-4pm
            [(1, 9, 11), (3, 9, 11)]     # Monday & Wednesday 9-11am
        ],
        "prerequisites": [["Math", "Physics"]],
        "units": 4,
        "course_type": "GE",
    },
    "Chemistry": {
        "slots": [
            [(2, 8, 10), (4, 8, 10)],    # Tuesday & Thursday 8-10am
            [(1, 15, 17), (3, 15, 17)]   # Monday & Wednesday 3-5pm
        ],
        "prerequisites": [["Math"], ["Biology", "Physics"]],
        "units": 3,
        "course_type": "GE",
    },
}


    
with open("major_reqs_tree.pickle", "rb") as file:
    majorRequirements = pickle.load(file)
major_reqs.checkOffMajorReqs(majorRequirements, courses_taken)

def convert_to_am_pm(hour):
    # Separate the hour and the fractional part (minutes)
    full_hour = int(hour)
    minutes = int((hour - full_hour) * 60)

    if full_hour == 0:
        return f"12:{minutes:02d} AM"
    elif full_hour == 12:
        return f"12:{minutes:02d} PM"
    elif full_hour < 12:
        return f"{full_hour}:{minutes:02d} AM"
    else:
        return f"{full_hour - 12}:{minutes:02d} PM"

def get_user_preferences():
    # Get preferred time range
    start_time = int(input("Enter preferred start time (24-hour format, e.g., 10 for 10 AM): "))
    end_time = int(input("Enter preferred end time (24-hour format, e.g., 16 for 4 PM): "))
    preferred_times = range(start_time, end_time)

    # Get preferred days
    print("\nSelect preferred days:")
    print("1: Monday")
    print("2: Tuesday")
    print("3: Wednesday")
    print("4: Thursday")
    preferred_days = []
    days_input = input("Enter day numbers separated by spaces (e.g., 1 2 4): ")
    preferred_days = [int(day) for day in days_input.split()]

    # Get gap preferences
    max_gap = float(input("\nEnter maximum desired gap between classes (in hours, e.g., 2): "))
    min_gap = float(input("Enter minimum desired break between classes (in hours, e.g., 0.5): "))

    return {
        "preferred_times": preferred_times,
        "preferred_days": preferred_days,
        "max_gap": max_gap,
        "min_gap": min_gap
    }

print("Welcome to Schedule Builder!")
print("Let's set up your schedule preferences!")
user_preferences = get_user_preferences()
print("\nGenerating schedule based on your preferences...")
# Add variables for each course with its available multi-day slots
for course, data in course_data.items():
    problem.addVariable(course, data["slots"])

# Constraint: No overlapping time slots for any two courses
def no_overlap(slot1, slot2):
    for day1, start1, end1 in slot1:
        for day2, start2, end2 in slot2:
            if day1 == day2 and not (end1 <= start2 or start1 >= end2):
                return False
    return True

# Apply the no-overlap constraint between each pair of courses
courses = list(course_data.keys())
for i in range(len(courses)):
    for j in range(i + 1, len(courses)):
        problem.addConstraint(no_overlap, (courses[i], courses[j]))

# Helper function to check if prerequisites are met based on `courses_taken`
def prerequisites_met(prereq_groups):
    for group in prereq_groups:
        if any(prereq in courses_taken for prereq in group):
            continue  # At least one course in the group is taken
        return False  # No course in this group is taken
    return True

# Apply prerequisite constraints based on courses already taken
for course, data in course_data.items():
    if data["prerequisites"]:
        prereq_groups = data["prerequisites"]
        # Add constraint if prerequisites are not met for this course
        if not prerequisites_met(prereq_groups):
            problem.addConstraint(lambda x: False, [course])  # Prevent scheduling course

# Constraint: Total units should not exceed 17
def unit_limit(*selected_courses):
    total_units = sum(course_data[course]["units"] for course in selected_courses if isinstance(course, str))
    return total_units <= 17

# Apply the unit constraint
problem.addConstraint(unit_limit, courses)

# Function to calculate the soft score for a schedule
def calculate_soft_score(solution, preferences):
    score = 0
    preferred_times = preferences["preferred_times"]
    preferred_days = preferences["preferred_days"]
    max_gap = preferences["max_gap"]

    daily_schedules = {}  # To group classes by days
    majorRequirementsCopy = copy.deepcopy(majorRequirements)

    for course, schedule in solution.items():
        for day, start, end in schedule:
            # Reward preferred times
            if start in preferred_times:
                score += 10
            else:
                score -= 5

            # Reward preferred days
            if day in preferred_days:
                score += 5
            else:
                score -= 2

            # Reward for having major requirements 
            score += major_reqs.getCourseScore(majorRequirementsCopy, course) * 10

            # Group schedules by day to calculate gaps
            if day not in daily_schedules:
                daily_schedules[day] = []
            daily_schedules[day].append((start, end))

    # Penalize large gaps between classes on the same day
    for day, times in daily_schedules.items():
        times.sort()  # Sort times by start time
        for i in range(len(times) - 1):
            gap = times[i + 1][0] - times[i][1]
            if gap > max_gap:
                score -= (gap - max_gap) * 5  # Penalize larger gaps more heavily

    return score

# Solve the CSP
solutions = problem.getSolutions()

# Rank solutions based on soft score
ranked_solutions = sorted(
    [(solution, calculate_soft_score(solution, user_preferences)) for solution in solutions],
    key=lambda x: x[1],
    reverse=True
)

# Display ranked solutions
if ranked_solutions:
    for idx, (solution, score) in enumerate(ranked_solutions, start=1):
        total_units = sum(course_data[course]["units"] for course in solution)
        print(f"Solution {idx} (Score: {score}, Total Units: {total_units}):")
        for course, schedule in solution.items():
            print(f"  {course} scheduled on:")
            for day, start, end in schedule:
                day_str = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday'}.get(day, f"Day {day}")
                print(f"    {day_str}: {convert_to_am_pm(start)} to {convert_to_am_pm(end)}")
        print("\n")
        # Only show top 5 solutions to avoid overwhelming the user
        if idx >= 5:
            break
else:
    # Relax constraints and try again with just the hard constraints
    problem = Problem()
    for course, data in course_data.items():
        problem.addVariable(course, data["slots"])
    
    # Keep only essential constraints (no overlaps and prerequisites)
    for i in range(len(courses)):
        for j in range(i + 1, len(courses)):
            problem.addConstraint(no_overlap, (courses[i], courses[j]))
    
    basic_solutions = problem.getSolutions()
    print("Here are some possible schedules (without preference optimization):")
    
    for idx, solution in enumerate(basic_solutions[:3], start=1):
        total_units = sum(course_data[course]["units"] for course in solution)
        print(f"Basic Solution {idx} (Total Units: {total_units}):")
        for course, schedule in solution.items():
            print(f"  {course} scheduled on:")
            for day, start, end in schedule:
                day_str = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday'}.get(day, f"Day {day}")
                print(f"    {day_str}: {start}:00 to {end}:00")
        print("\n")

def convert_to_am_pm(hour):
    # Separate the hour and the fractional part (minutes)
    full_hour = int(hour)
    minutes = int((hour - full_hour) * 60)

    if full_hour == 0:
        return f"12:{minutes:02d} AM"
    elif full_hour == 12:
        return f"12:{minutes:02d} PM"
    elif full_hour < 12:
        return f"{full_hour}:{minutes:02d} AM"
    else:
        return f"{full_hour - 12}:{minutes:02d} PM"
