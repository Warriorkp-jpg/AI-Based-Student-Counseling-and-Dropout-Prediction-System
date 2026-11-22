

def calculate_risk(student):
    
    score = 0

    # Academic
    if student.cgpa < 5:
        score += 3
    elif student.cgpa < 7:
        score += 2

    # Attendance
    if student.attendance < 50:
        score += 3
    elif student.attendance < 75:
        score += 2

    # Stress
    if student.stress_level > 7:
        score += 3
    elif student.stress_level > 5:
        score += 2

    # Financial
    if student.financial_problem:
        score += 2

    # Final Decision
    if score >= 7:
        return "High"
    elif score >= 4:
        return "Medium"
    else:
        return "Low"
        
        
        
def generate_suggestions(student):
    suggestions = []

    # Academic
    if student.cgpa < 5:
        suggestions.append("Focus on improving your academic performance. Consider extra study hours.")

    elif student.cgpa < 7:
        suggestions.append("You are doing okay, but you can improve your CGPA with better consistency.")

    # Attendance
    if student.attendance < 50:
        suggestions.append("Your attendance is very low. Attend classes regularly.")

    elif student.attendance < 75:
        suggestions.append("Try to improve your attendance for better understanding.")

    # Stress
    if student.stress_level > 7:
        suggestions.append("You seem highly stressed. Take breaks and talk to someone.")

    elif student.stress_level > 5:
        suggestions.append("Manage stress with proper planning and relaxation techniques.")

    # Financial
    if student.financial_problem:
        suggestions.append("Financial issue detected. Contact administration for support.")

        
   
    
    # A new account can reach the dashboard before optional profile details are filled in.
    if (student.annual_income or 0) <= 10000:
        suggestions.append("""Annual income is less than 1lakh
                           The most usefull scholarship for you is : ....
                           """)

    # Default
    if not suggestions:
        suggestions.append("NOT ENOUGH DATA TO ANALYSE THE PERFORMANCE")

    return suggestions
