"""Temporary college curriculum data.

Replace the dictionary in ``get_course_curriculum`` with a college API call later.
The views and templates will keep working because they only use the returned shape.
"""


COURSE_CATALOG = {
    'cse': {
        'name': 'Computer Science',
        'department': 'School of Computing',
        'years': {
            1: [
                ('Programming Fundamentals', 'Python basics, problem solving, functions, and files.'),
                ('Mathematics for Computing', 'Logic, matrices, probability, and discrete mathematics.'),
                ('Digital Systems', 'Computer organization and introductory electronics.'),
                ('Communication Skills', 'Professional writing and presentation practice.'),
            ],
            2: [
                ('Data Structures', 'Arrays, stacks, queues, trees, graphs, and complexity.'),
                ('Database Management Systems', 'SQL, normalization, and database design.'),
                ('Object-Oriented Programming', 'Classes, inheritance, testing, and clean code.'),
                ('Computer Networks', 'TCP/IP, routing, protocols, and network security basics.'),
            ],
            3: [
                ('Operating Systems', 'Processes, memory, scheduling, and file systems.'),
                ('Software Engineering', 'Requirements, design, agile delivery, and quality.'),
                ('Web Development', 'Frontend, backend, APIs, authentication, and deployment.'),
                ('Machine Learning Foundations', 'Supervised learning, evaluation, and ethical AI.'),
            ],
        },
    },
    'aiml': {
        'name': 'AI & Machine Learning',
        'department': 'School of AI',
        'years': {
            1: [('Python for AI', 'Python programming, data types, and problem solving.'), ('Mathematics for AI', 'Linear algebra, calculus, probability, and statistics.'), ('Computing Basics', 'Digital systems and computer fundamentals.')],
            2: [('Data Structures', 'Efficient algorithms and core data structures.'), ('Data Analytics', 'Data cleaning, visualization, and exploratory analysis.'), ('Machine Learning', 'Regression, classification, and model evaluation.')],
            3: [('Deep Learning', 'Neural networks, CNNs, and sequence models.'), ('Natural Language Processing', 'Text processing, language models, and applications.'), ('MLOps', 'Deployment, monitoring, and responsible AI.')],
        },
    },
    'mech': {
        'name': 'Mechanical Engineering',
        'department': 'School of Engineering',
        'years': {
            1: [('Engineering Mathematics', 'Mathematical foundations for engineers.'), ('Engineering Graphics', 'Technical drawing and CAD basics.'), ('Materials Science', 'Engineering materials and their properties.')],
            2: [('Thermodynamics', 'Energy, heat, work, and engines.'), ('Mechanics of Solids', 'Stress, strain, and structural behaviour.'), ('Manufacturing Processes', 'Machining, casting, joining, and production.')],
            3: [('Machine Design', 'Component design, tolerances, and safety.'), ('Fluid Mechanics', 'Fluid behaviour and industrial applications.'), ('Industrial Engineering', 'Operations, quality, and productivity.')],
        },
    },
    'bba': {
        'name': 'Bachelor of Business Administration',
        'department': 'School of Business',
        'years': {
            1: [('Business Communication', 'Professional communication and presentations.'), ('Principles of Management', 'Planning, leadership, and organization.'), ('Financial Accounting', 'Accounting concepts and financial statements.')],
            2: [('Marketing Management', 'Customers, branding, research, and campaigns.'), ('Human Resource Management', 'Hiring, performance, and workplace culture.'), ('Business Statistics', 'Data-driven business decisions.')],
            3: [('Strategic Management', 'Competitive strategy and business planning.'), ('Entrepreneurship', 'Opportunity discovery and startup development.'), ('Business Analytics', 'Using data for business decisions.')],
        },
    },
    'mba': {
        'name': 'Master of Business Administration',
        'department': 'Graduate School of Business',
        'years': {
            1: [('Managerial Economics', 'Economic thinking for management decisions.'), ('Corporate Finance', 'Investment, valuation, and capital structure.'), ('Leadership and Teams', 'Leading people and organizational change.')],
            2: [('Business Strategy', 'Integrated strategy and competitive advantage.'), ('Operations Management', 'Supply chains, process design, and quality.'), ('Capstone Project', 'Applied business problem solving.')],
        },
    },
}


def get_course_curriculum(course_code, year=None):
    """Return dummy course information in the same format a college API would return."""
    course = COURSE_CATALOG.get(course_code) or COURSE_CATALOG['cse']
    selected_year = year if year in course['years'] else min(course['years'])
    subjects = [
        {
            'code': f"{course_code.upper()}{selected_year}{index + 1:02d}",
            'name': name,
            'summary': summary,
            'credits': 4 if index < 3 else 2,
            'modules': [
                'Core concepts and terminology',
                'Guided practice and assignments',
                'Internal assessment and revision',
                'End-semester application project',
            ],
        }
        for index, (name, summary) in enumerate(course['years'][selected_year])
    ]
    return {
        'source': 'Demo college API data',
        'course_name': course['name'],
        'department': course['department'],
        'year': selected_year,
        'subjects': subjects,
    }
