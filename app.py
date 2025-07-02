from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import hashlib
import random
from datetime import datetime
import os
import secrets

app = Flask(__name__)

# Generate a secure SECRET_KEY if not provided via environment variable
SECRET_KEY = os.environ.get('SECRET_KEY') # or secrets.token_hex(32)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///robot_study.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

# Database Models
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.String(50), unique=True, nullable=False)
    fingerprint_hash = db.Column(db.String(256), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    tab_switches = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VideoResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.String(50), db.ForeignKey('participant.participant_id'), nullable=False)
    video_id = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    attention_question = db.Column(db.Text, nullable=False)
    attention_answer = db.Column(db.String(100), nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)
    attention_correct = db.Column(db.Boolean, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

class Demographics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.String(50), db.ForeignKey('participant.participant_id'), nullable=False)
    age = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(30), nullable=False)
    education = db.Column(db.String(50), nullable=False)
    profession = db.Column(db.String(50), nullable=False)
    robot_experience = db.Column(db.String(50), nullable=False)
    tech_comfort = db.Column(db.String(50), nullable=False)

# Video Configuration
VIDEO_CONFIG = {
    'total_videos': 1,
    'videos_per_participant': 1,
    'video_folder': 'videos'
}

def create_fingerprint_hash(fingerprint_data):
    """Create a hash from browser fingerprint data for duplicate detection"""
    fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()

def select_videos_for_participant():
    """Select 10 random videos from the pool of 100 videos"""
    video_ids = list(range(1, VIDEO_CONFIG['total_videos'] + 1))
    selected = random.sample(video_ids, VIDEO_CONFIG['videos_per_participant'])
    
    # Create video data structure
    video_data = []
    attention_questions = [
        {
            'question': 'What color was the mobile robot?',
            'options': ['Blue', 'Red', 'White', 'Black'],
            'correct': 'blue'
        },
        {
            'question': 'How many humans were in the scene?',
            'options': ['1', '2', '3', '4'],
            'correct': '2'
        },
        {
            'question': 'What was the stationary robot doing?',
            'options': ['Standing still', 'Talking', 'Moving arms', 'Turning around'],
            'correct': 'talking'
        },
        {
            'question': 'In which direction did the mobile robot approach?',
            'options': ['From the left', 'From the right', 'From behind', 'From the front'],
            'correct': 'left'
        },
        {
            'question': 'What was the human holding?',
            'options': ['Nothing', 'A book', 'A cup', 'A phone'],
            'correct': 'cup'
        },
        {
            'question': 'How did the conversation end?',
            'options': ['Abruptly', 'Naturally', 'With interruption', 'Unclear'],
            'correct': 'naturally'
        },
        {
            'question': 'What gesture did the mobile robot make?',
            'options': ['No gesture', 'Wave', 'Point', 'Thumbs up'],
            'correct': 'wave'
        },
        {
            'question': 'What was the setting of the scene?',
            'options': ['Home', 'Office', 'Laboratory', 'Cafe'],
            'correct': 'office'
        },
        {
            'question': 'How long did the interaction last?',
            'options': ['Very short', 'Short', 'Medium', 'Long'],
            'correct': 'medium'
        },
        {
            'question': 'What was the overall mood?',
            'options': ['Tense', 'Friendly', 'Formal', 'Awkward'],
            'correct': 'friendly'
        }
    ]
    
    for i, video_id in enumerate(selected):
        question_data = attention_questions[i % len(attention_questions)]
        video_data.append({
            'id': video_id,
            'filename': f'video_{video_id}.mp4',
            'attentionQuestion': question_data['question'],
            'correctAnswer': question_data['correct'],
            'options': question_data['options']
        })
    
    return video_data

@app.route('/')
def index():
    """Serve the main survey page"""
    return send_from_directory('.', 'index.html')

@app.route('/videos/<filename>')
def serve_video(filename):
    """Serve video files"""
    return send_from_directory(VIDEO_CONFIG['video_folder'], filename)

@app.route('/api/check-participant', methods=['POST'])
def check_participant():
    """Check if participant has already completed the study"""
    try:
        data = request.get_json()
        fingerprint_hash = create_fingerprint_hash(data['fingerprint'])
        
        existing_participant = Participant.query.filter_by(
            fingerprint_hash=fingerprint_hash
        ).first()
        
        if existing_participant and existing_participant.completed:
            return jsonify({'alreadyParticipated': True})
        
        return jsonify({'alreadyParticipated': False})
    
    except Exception as e:
        print(f"Error checking participant: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/get-videos', methods=['POST'])
def get_videos():
    """Get video list for a participant"""
    try:
        data = request.get_json()
        participant_id = data.get('participantId')
        
        # Check if participant already has assigned videos
        existing_participant = Participant.query.filter_by(
            participant_id=participant_id
        ).first()
        
        if existing_participant:
            # Return existing video assignment (you'd need to store this)
            # For now, generate new ones
            pass
        
        videos = select_videos_for_participant()
        return jsonify({'videos': videos})
    
    except Exception as e:
        print(f"Error getting videos: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/submit-survey', methods=['POST'])
def submit_survey():
    """Submit completed survey data"""
    try:
        data = request.get_json()
        
        # Create participant record
        participant = Participant(
            participant_id=data['participantId'],
            fingerprint_hash=create_fingerprint_hash(
                data.get('fingerprint', {})
            ),
            start_time=datetime.fromisoformat(data['startTime'].replace('Z', '+00:00')),
            end_time=datetime.fromisoformat(data['endTime'].replace('Z', '+00:00')),
            completed=data['completed'],
            tab_switches=data.get('tabSwitches', 0)
        )
        db.session.add(participant)
        
        # Save video responses
        for video_data in data['videos']:
            attention_correct = (
                video_data['attentionAnswer'].replace('-', ' ').lower() == 
                video_data['correctAnswer'].lower()
            )
            
            video_response = VideoResponse(
                participant_id=data['participantId'],
                video_id=video_data['videoId'],
                filename=video_data['filename'],
                attention_question=video_data['attentionQuestion'],
                attention_answer=video_data['attentionAnswer'],
                correct_answer=video_data['correctAnswer'],
                attention_correct=attention_correct,
                rating=video_data['rating'],
                timestamp=datetime.fromisoformat(video_data['timestamp'].replace('Z', '+00:00'))
            )
            db.session.add(video_response)
        
        # Save demographics
        demographics = Demographics(
            participant_id=data['participantId'],
            age=data['demographics']['age'],
            gender=data['demographics']['gender'],
            education=data['demographics']['education'],
            profession=data['demographics']['profession'],
            robot_experience=data['demographics']['robotExperience'],
            tech_comfort=data['demographics']['techComfort']
        )
        db.session.add(demographics)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Survey submitted successfully'})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting survey: {e}")
        return jsonify({'error': 'Failed to submit survey'}), 500

@app.route('/api/admin/stats')
def admin_stats():
    """Get survey statistics for admin dashboard"""
    try:
        total_participants = Participant.query.count()
        completed_surveys = Participant.query.filter_by(completed=True).count()
        
        # Average ratings by video
        video_stats = db.session.query(
            VideoResponse.video_id,
            db.func.avg(VideoResponse.rating).label('avg_rating'),
            db.func.count(VideoResponse.id).label('response_count')
        ).group_by(VideoResponse.video_id).all()
        
        # Demographics distribution
        age_dist = db.session.query(
            Demographics.age,
            db.func.count(Demographics.id).label('count')
        ).group_by(Demographics.age).all()
        
        gender_dist = db.session.query(
            Demographics.gender,
            db.func.count(Demographics.id).label('count')
        ).group_by(Demographics.gender).all()
        
        return jsonify({
            'totalParticipants': total_participants,
            'completedSurveys': completed_surveys,
            'completionRate': (completed_surveys / total_participants * 100) if total_participants > 0 else 0,
            'videoStats': [
                {
                    'videoId': stat.video_id,
                    'avgRating': round(stat.avg_rating, 2),
                    'responseCount': stat.response_count
                } for stat in video_stats
            ],
            'demographics': {
                'age': [{'category': item.age, 'count': item.count} for item in age_dist],
                'gender': [{'category': item.gender, 'count': item.count} for item in gender_dist]
            }
        })
    
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/export')
def export_data():
    """Export all survey data as JSON"""
    try:
        participants = Participant.query.all()
        export_data = []
        
        for participant in participants:
            video_responses = VideoResponse.query.filter_by(
                participant_id=participant.participant_id
            ).all()
            demographics = Demographics.query.filter_by(
                participant_id=participant.participant_id
            ).first()
            
            export_data.append({
                'participantId': participant.participant_id,
                'startTime': participant.start_time.isoformat() if participant.start_time else None,
                'endTime': participant.end_time.isoformat() if participant.end_time else None,
                'completed': participant.completed,
                'tabSwitches': participant.tab_switches,
                'demographics': {
                    'age': demographics.age if demographics else None,
                    'gender': demographics.gender if demographics else None,
                    'education': demographics.education if demographics else None,
                    'profession': demographics.profession if demographics else None,
                    'robotExperience': demographics.robot_experience if demographics else None,
                    'techComfort': demographics.tech_comfort if demographics else None
                } if demographics else None,
                'videoResponses': [
                    {
                        'videoId': vr.video_id,
                        'filename': vr.filename,
                        'attentionQuestion': vr.attention_question,
                        'attentionAnswer': vr.attention_answer,
                        'attentionCorrect': vr.attention_correct,
                        'rating': vr.rating,
                        'timestamp': vr.timestamp.isoformat()
                    } for vr in video_responses
                ]
            })
        
        return jsonify(export_data)
    
    except Exception as e:
        print(f"Error exporting data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Database initialization
def init_db():
    """Initialize the database"""
    db.create_all()
    print("Database initialized successfully")

if __name__ == '__main__':
    # Create video directory if it doesn't exist
    os.makedirs(VIDEO_CONFIG['video_folder'], exist_ok=True)
    
    # Initialize database
    with app.app_context():
        init_db()
    
    print("Robot Conversation Study Server Starting...")
    print(f"Place your video files in the '{VIDEO_CONFIG['video_folder']}' directory")
    print("Videos should be named: video_1.mp4, video_2.mp4, ..., video_100.mp4")
    print("Access the survey at: http://localhost:5000")
    print("Admin stats at: http://localhost:5000/api/admin/stats")
    print("Export data at: http://localhost:5000/api/admin/export")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
