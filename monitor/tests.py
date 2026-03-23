from django.test import TestCase, Client
from django.urls import reverse
from .models import YogaSession, WeekdaySession, ExamSession
import json

class ModelTests(TestCase):
    def test_yoga_session_creation(self):
        """Test YogaSession model"""
        session = YogaSession.objects.create(duration=600)
        self.assertEqual(session.duration, 600)
        self.assertEqual(session.duration_minutes, 10.0)
    
    def test_weekday_session_creation(self):
        """Test WeekdaySession model"""
        session = WeekdaySession.objects.create(
            duration=3600,
            blink_count=100,
            bad_posture_time=300
        )
        self.assertEqual(session.duration, 3600)
        self.assertEqual(session.blink_count, 100)
        self.assertEqual(session.bad_posture_time, 300)
        self.assertEqual(session.duration_minutes, 60.0)
        self.assertEqual(session.bad_posture_minutes, 5.0)
    
    def test_exam_session_creation(self):
        """Test ExamSession model"""
        session = ExamSession.objects.create(
            duration=7200,
            eyes_away_time=120,
            multiple_person_time=30,
            alert_count=5
        )
        self.assertEqual(session.duration, 7200)
        self.assertEqual(session.duration_minutes, 120.0)
        self.assertEqual(session.alert_count, 5)

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_home_page(self):
        """Test home page loads"""
        response = self.client.get(reverse('home_page'))
        self.assertEqual(response.status_code, 200)
    
    def test_weekday_page(self):
        """Test weekday page loads"""
        response = self.client.get(reverse('weekday_page'))
        self.assertEqual(response.status_code, 200)
    
    def test_weekend_page(self):
        """Test weekend page loads"""
        response = self.client.get(reverse('weekend_page'))
        self.assertEqual(response.status_code, 200)
    
    def test_exam_page(self):
        """Test exam page loads"""
        response = self.client.get(reverse('exam_page'))
        self.assertEqual(response.status_code, 200)
    
    def test_save_weekday_session(self):
        """Test saving weekday session"""
        data = {'duration': 1800}
        response = self.client.post(
            reverse('save_weekday_session'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(WeekdaySession.objects.count(), 1)
    
    def test_save_yoga_session(self):
        """Test saving yoga session"""
        data = {'duration': 1200}
        response = self.client.post(
            reverse('save_session'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(YogaSession.objects.count(), 1)
    
    def test_save_exam_session(self):
        """Test saving exam session"""
        data = {
            'duration': 3600,
            'eyes_away_time': 180,
            'multiple_person_time': 60,
            'alert_count': 3
        }
        response = self.client.post(
            reverse('save_exam_session'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ExamSession.objects.count(), 1)
    
    def test_combined_history(self):
        """Test combined history view"""
        # Create test data
        WeekdaySession.objects.create(duration=1800, blink_count=50, bad_posture_time=300)
        YogaSession.objects.create(duration=1200)
        ExamSession.objects.create(duration=3600, eyes_away_time=120, alert_count=2)
        
        response = self.client.get(reverse('combined_history'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('weekday_sessions', response.context)
        self.assertIn('weekend_sessions', response.context)
        self.assertIn('exam_sessions', response.context)

class CameraAPITests(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_get_available_cameras(self):
        """Test getting available cameras"""
        response = self.client.get(reverse('get_available_cameras'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertIn('cameras', data)