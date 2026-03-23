# from django.db import models

# class YogaSession(models.Model):
#     date = models.DateTimeField(auto_now_add=True)
#     duration = models.IntegerField()  # seconds

#     @property
#     def duration_minutes(self):
#         return round(self.duration / 60, 2)

#     def __str__(self):
#         return f"{self.date} - {self.duration}s"


# class WeekdaySession(models.Model):
#     date = models.DateTimeField(auto_now_add=True)
#     duration = models.IntegerField()  # seconds
#     blink_count = models.IntegerField(default=0)
#     bad_posture_time = models.IntegerField(default=0)  # seconds

#     @property
#     def duration_minutes(self):
#         return round(self.duration / 60, 2)

#     @property
#     def bad_posture_minutes(self):
#         return round(self.bad_posture_time / 60, 2)

#     def __str__(self):
#         return f"{self.date} - {self.duration}s"
from django.db import models


class YogaSession(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField()  # seconds

    @property
    def duration_minutes(self):
        return round(self.duration / 60, 2)

    def __str__(self):
        return f"{self.date} - {self.duration}s"


class WeekdaySession(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField()  # seconds
    blink_count = models.IntegerField(default=0)
    bad_posture_time = models.IntegerField(default=0)  # seconds

    @property
    def duration_minutes(self):
        return round(self.duration / 60, 2)

    @property
    def bad_posture_minutes(self):
        return round(self.bad_posture_time / 60, 2)

    def __str__(self):
        return f"{self.date} - {self.duration}s"


class ExamSession(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField()  # seconds
    eyes_away_time = models.IntegerField(default=0)  # seconds
    multiple_person_time = models.IntegerField(default=0)  # seconds
    alert_count = models.IntegerField(default=0)

    @property
    def duration_minutes(self):
        return round(self.duration / 60, 2)
    
    @property
    def eyes_away_minutes(self):
        return round(self.eyes_away_time / 60, 2)
    
    @property
    def multiple_person_minutes(self):
        return round(self.multiple_person_time / 60, 2)
    
    @property
    def violation_percentage(self):
        """Calculate percentage of time with violations"""
        if self.duration == 0:
            return 0
        total_violation = self.eyes_away_time + self.multiple_person_time
        return round((total_violation / self.duration) * 100, 1)

    def __str__(self):
        return f"Exam {self.date} - {self.duration}s - {self.alert_count} alerts"