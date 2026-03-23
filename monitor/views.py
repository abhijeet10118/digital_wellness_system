# from django.shortcuts import render
# from django.http import StreamingHttpResponse, JsonResponse
# import json
# import threading
# import time

# from .models import YogaSession, WeekdaySession
# from .camera.weekday import WeekdayCamera
# from .camera.weekend import WeekendCamera
# from .rag_chatbot import chatbot

# # Global camera instances with lock
# weekday_cam = None
# weekend_cam = None
# camera_lock = threading.Lock()
# current_camera = None
# video_stream_active = False


# def cleanup_all_cameras():
#     """Cleanup all camera instances and their MediaPipe models"""
#     global weekday_cam, weekend_cam, current_camera, video_stream_active
    
#     video_stream_active = False
#     time.sleep(0.3)
    
#     with camera_lock:
#         print("🧹 Starting complete camera cleanup...")
        
#         if weekday_cam is not None:
#             print("🧹 Cleaning up weekday camera")
#             try:
#                 if hasattr(weekday_cam, 'face_mesh') and weekday_cam.face_mesh:
#                     weekday_cam.face_mesh.close()
#                 if hasattr(weekday_cam, 'pose') and weekday_cam.pose:
#                     weekday_cam.pose.close()
#                 weekday_cam.release()
#             except Exception as e:
#                 print(f"Warning during weekday cleanup: {e}")
#             weekday_cam = None
        
#         if weekend_cam is not None:
#             print("🧹 Cleaning up weekend camera")
#             try:
#                 if hasattr(weekend_cam, 'pose') and weekend_cam.pose:
#                     weekend_cam.pose.close()
#                 weekend_cam.release()
#             except Exception as e:
#                 print(f"Warning during weekend cleanup: {e}")
#             weekend_cam = None
        
#         current_camera = None
#         time.sleep(0.5)
#         print("✅ All cameras cleaned up and released")


# def frame_generator(camera):
#     """Generate frames from the camera object"""
#     global video_stream_active
#     video_stream_active = True
    
#     try:
#         while video_stream_active:
#             frame = camera.get_frame()
#             if frame is None:
#                 time.sleep(0.01)
#                 continue
            
#             yield (
#                 b"--frame\r\n"
#                 b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
#             )
#     except GeneratorExit:
#         print("🛑 Frame generator stopped")
#     except Exception as e:
#         print(f"❌ Frame generator error: {e}")
#     finally:
#         video_stream_active = False


# def video_feed(request):
#     global weekday_cam, weekend_cam, current_camera, video_stream_active

#     mode = request.GET.get("mode", "weekday")
#     print(f"📹 VIDEO FEED REQUEST: {mode}")

#     video_stream_active = False
#     time.sleep(0.5)

#     with camera_lock:
#         if mode == "weekday":
#             print("✅ Initializing WeekdayCamera")
            
#             if weekend_cam is not None:
#                 try:
#                     if hasattr(weekend_cam, 'pose') and weekend_cam.pose:
#                         weekend_cam.pose.close()
#                     weekend_cam.release()
#                 except Exception as e:
#                     print(f"Warning during weekend cleanup: {e}")
#                 weekend_cam = None
#                 time.sleep(0.5)
            
#             if weekday_cam is not None:
#                 try:
#                     if hasattr(weekday_cam, 'face_mesh') and weekday_cam.face_mesh:
#                         weekday_cam.face_mesh.close()
#                     if hasattr(weekday_cam, 'pose') and weekday_cam.pose:
#                         weekday_cam.pose.close()
#                     weekday_cam.release()
#                 except Exception as e:
#                     print(f"Warning during old weekday cleanup: {e}")
#                 weekday_cam = None
#                 time.sleep(0.5)
            
#             weekday_cam = WeekdayCamera()
#             camera = weekday_cam
#             current_camera = "weekday"
            
#         else:  # weekend mode
#             print("✅ Initializing WeekendCamera")
            
#             if weekday_cam is not None:
#                 try:
#                     if hasattr(weekday_cam, 'face_mesh') and weekday_cam.face_mesh:
#                         weekday_cam.face_mesh.close()
#                     if hasattr(weekday_cam, 'pose') and weekday_cam.pose:
#                         weekday_cam.pose.close()
#                     weekday_cam.release()
#                 except Exception as e:
#                     print(f"Warning during weekday cleanup: {e}")
#                 weekday_cam = None
#                 time.sleep(0.5)
            
#             if weekend_cam is not None:
#                 try:
#                     if hasattr(weekend_cam, 'pose') and weekend_cam.pose:
#                         weekend_cam.pose.close()
#                     weekend_cam.release()
#                 except Exception as e:
#                     print(f"Warning during old weekend cleanup: {e}")
#                 weekend_cam = None
#                 time.sleep(0.5)
            
#             weekend_cam = WeekendCamera()
#             camera = weekend_cam
#             current_camera = "weekend"

#     return StreamingHttpResponse(
#         frame_generator(camera),
#         content_type="multipart/x-mixed-replace; boundary=frame"
#     )


# def home_page(request):
#     """Home page - cleanup cameras and release hardware"""
#     print("🏠 Loading Home Page - Stopping streams and cleaning up cameras")
#     cleanup_all_cameras()
#     return render(request, "monitor/home.html")


# def weekday_page(request):
#     print("🌐 Loading Weekday Page")
#     return render(request, "monitor/weekday.html")


# def weekend_page(request):
#     print("🌐 Loading Weekend Page")
#     return render(request, "monitor/weekend.html")


# def reset_weekday_session(request):
#     """Reset session-specific counters when starting a new session"""
#     global weekday_cam
    
#     if request.method == "POST":
#         try:
#             if weekday_cam is not None:
#                 weekday_cam.session_blink_count = 0
#                 weekday_cam.total_bad_posture_time = 0
#                 weekday_cam.bad_posture_start = None
#                 print("🔄 Session counters reset")
#             return JsonResponse({"status": "reset"})
#         except Exception as e:
#             print(f"Warning: Reset error: {e}")
#             return JsonResponse({"status": "error"})
    
#     return JsonResponse({"status": "invalid"})


# def save_weekday_session(request):
#     global weekday_cam
    
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body.decode("utf-8"))
#             duration = data.get("duration")

#             if duration is None:
#                 return JsonResponse({"status": "error", "message": "No duration"})

#             blink_count = 0
#             bad_posture_time = 0
            
#             if weekday_cam is not None:
#                 blink_count = getattr(weekday_cam, 'session_blink_count', 0)
#                 bad_posture_time = int(getattr(weekday_cam, 'total_bad_posture_time', 0))
                
#                 if bad_posture_time > duration:
#                     bad_posture_time = duration

#             WeekdaySession.objects.create(
#                 duration=int(duration),
#                 blink_count=blink_count,
#                 bad_posture_time=bad_posture_time
#             )
            
#             if weekday_cam is not None:
#                 weekday_cam.session_blink_count = 0
#                 weekday_cam.total_bad_posture_time = 0
#                 weekday_cam.bad_posture_start = None
            
#             print(f"💾 Weekday session saved: {duration}s")
#             return JsonResponse({
#                 "status": "saved",
#                 "blink_count": blink_count,
#                 "bad_posture_time": bad_posture_time
#             })

#         except Exception as e:
#             print(f"❌ Error saving weekday session: {e}")
#             return JsonResponse({"status": "error", "message": str(e)})

#     return JsonResponse({"status": "invalid"})


# def save_session(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body.decode("utf-8"))
#             duration = data.get("duration")

#             if duration is None:
#                 return JsonResponse({"status": "error", "message": "No duration"})

#             YogaSession.objects.create(duration=int(duration))
#             print(f"💾 Yoga session saved: {duration} seconds")
#             return JsonResponse({"status": "saved"})

#         except Exception as e:
#             print(f"❌ Error saving yoga session: {e}")
#             return JsonResponse({"status": "error", "message": str(e)})

#     return JsonResponse({"status": "invalid"})


# def session_history(request):
#     sessions = YogaSession.objects.all().order_by("-date")
#     print(f"📊 Loading {sessions.count()} yoga sessions")
#     return render(request, "monitor/history.html", {"sessions": sessions})


# def weekday_history(request):
#     sessions = WeekdaySession.objects.all().order_by("-date")
#     print(f"📊 Loading {sessions.count()} weekday sessions")
#     return render(request, "monitor/history_weekday.html", {"sessions": sessions})


# def combined_history(request):
#     """Combined history view showing weekday and weekend sessions"""
#     weekday_sessions = WeekdaySession.objects.all().order_by("-date")
#     weekend_sessions = YogaSession.objects.all().order_by("-date")
    
#     print(f"📊 Loading combined history - Weekday: {weekday_sessions.count()}, Weekend: {weekend_sessions.count()}")
    
#     context = {
#         'weekday_sessions': weekday_sessions,
#         'weekend_sessions': weekend_sessions,
#     }
    
#     return render(request, "monitor/combined_history.html", context)


# def chatbot_query(request):
#     """Handle chatbot queries"""
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body.decode('utf-8'))
#             question = data.get('question', '').strip()
            
#             if not question:
#                 return JsonResponse({
#                     'success': False,
#                     'answer': 'Please ask a question.'
#                 })
            
#             response = chatbot.answer_question(question)
#             return JsonResponse(response)
        
#         except Exception as e:
#             return JsonResponse({
#                 'success': False,
#                 'answer': f'Error: {str(e)}'
#             })
    
#     return JsonResponse({
#         'success': False,
#         'answer': 'Only POST requests are allowed.'
#     })
from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse
import json
import threading
import time
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Avg

from .models import YogaSession, WeekdaySession
from .camera.weekday import WeekdayCamera
from .camera.weekend import WeekendCamera
from .rag_chatbot import chatbot

# Global camera instances with lock
weekday_cam = None
weekend_cam = None
camera_lock = threading.Lock()
current_camera = None
video_stream_active = False


def cleanup_all_cameras():
    """Cleanup all camera instances and their MediaPipe models"""
    global weekday_cam, weekend_cam, current_camera, video_stream_active
    
    video_stream_active = False
    time.sleep(0.3)
    
    with camera_lock:
        print("🧹 Starting complete camera cleanup...")
        
        if weekday_cam is not None:
            print("🧹 Cleaning up weekday camera")
            try:
                if hasattr(weekday_cam, 'face_mesh') and weekday_cam.face_mesh:
                    weekday_cam.face_mesh.close()
                if hasattr(weekday_cam, 'pose') and weekday_cam.pose:
                    weekday_cam.pose.close()
                weekday_cam.release()
            except Exception as e:
                print(f"Warning during weekday cleanup: {e}")
            weekday_cam = None
        
        if weekend_cam is not None:
            print("🧹 Cleaning up weekend camera")
            try:
                if hasattr(weekend_cam, 'pose') and weekend_cam.pose:
                    weekend_cam.pose.close()
                weekend_cam.release()
            except Exception as e:
                print(f"Warning during weekend cleanup: {e}")
            weekend_cam = None
        
        current_camera = None
        time.sleep(0.5)
        print("✅ All cameras cleaned up and released")


def frame_generator(camera):
    """Generate frames from the camera object"""
    global video_stream_active
    video_stream_active = True
    
    try:
        while video_stream_active:
            frame = camera.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue
            
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )
    except GeneratorExit:
        print("🛑 Frame generator stopped")
    except Exception as e:
        print(f"❌ Frame generator error: {e}")
    finally:
        video_stream_active = False


def video_feed(request):
    global weekday_cam, weekend_cam, current_camera, video_stream_active

    mode = request.GET.get("mode", "weekday")
    print(f"📹 VIDEO FEED REQUEST: {mode}")

    video_stream_active = False
    time.sleep(0.5)

    with camera_lock:
        if mode == "weekday":
            print("✅ Initializing WeekdayCamera")
            
            if weekend_cam is not None:
                try:
                    if hasattr(weekend_cam, 'pose') and weekend_cam.pose:
                        weekend_cam.pose.close()
                    weekend_cam.release()
                except Exception as e:
                    print(f"Warning during weekend cleanup: {e}")
                weekend_cam = None
                time.sleep(0.5)
            
            if weekday_cam is not None:
                try:
                    if hasattr(weekday_cam, 'face_mesh') and weekday_cam.face_mesh:
                        weekday_cam.face_mesh.close()
                    if hasattr(weekday_cam, 'pose') and weekday_cam.pose:
                        weekday_cam.pose.close()
                    weekday_cam.release()
                except Exception as e:
                    print(f"Warning during old weekday cleanup: {e}")
                weekday_cam = None
                time.sleep(0.5)
            
            weekday_cam = WeekdayCamera()
            camera = weekday_cam
            current_camera = "weekday"
            
        else:  # weekend mode
            print("✅ Initializing WeekendCamera")
            
            if weekday_cam is not None:
                try:
                    if hasattr(weekday_cam, 'face_mesh') and weekday_cam.face_mesh:
                        weekday_cam.face_mesh.close()
                    if hasattr(weekday_cam, 'pose') and weekday_cam.pose:
                        weekday_cam.pose.close()
                    weekday_cam.release()
                except Exception as e:
                    print(f"Warning during weekday cleanup: {e}")
                weekday_cam = None
                time.sleep(0.5)
            
            if weekend_cam is not None:
                try:
                    if hasattr(weekend_cam, 'pose') and weekend_cam.pose:
                        weekend_cam.pose.close()
                    weekend_cam.release()
                except Exception as e:
                    print(f"Warning during old weekend cleanup: {e}")
                weekend_cam = None
                time.sleep(0.5)
            
            weekend_cam = WeekendCamera()
            camera = weekend_cam
            current_camera = "weekend"

    return StreamingHttpResponse(
        frame_generator(camera),
        content_type="multipart/x-mixed-replace; boundary=frame"
    )


def home_page(request):
    """Home page - cleanup cameras and release hardware"""
    print("🏠 Loading Home Page - Stopping streams and cleaning up cameras")
    cleanup_all_cameras()
    return render(request, "monitor/home.html")


def dashboard_page(request):
    """Dashboard page with comprehensive statistics"""
    print("📊 Loading Dashboard Page")
    cleanup_all_cameras()
    
    # Get all sessions
    weekday_sessions = WeekdaySession.objects.all()
    yoga_sessions = YogaSession.objects.all()
    
    # Calculate time ranges
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    
    # Calculate statistics
    weekday_stats = {
        'total_sessions': weekday_sessions.count(),
        'total_duration': weekday_sessions.aggregate(Sum('duration'))['duration__sum'] or 0,
        'total_blinks': weekday_sessions.aggregate(Sum('blink_count'))['blink_count__sum'] or 0,
        'avg_blinks_per_session': weekday_sessions.aggregate(Avg('blink_count'))['blink_count__avg'] or 0,
        'total_bad_posture': weekday_sessions.aggregate(Sum('bad_posture_time'))['bad_posture_time__sum'] or 0,
    }
    
    # Calculate posture quality
    if weekday_stats['total_duration'] > 0:
        posture_quality = ((weekday_stats['total_duration'] - weekday_stats['total_bad_posture']) 
                          / weekday_stats['total_duration'] * 100)
        weekday_stats['posture_quality'] = max(0, min(100, posture_quality))
    else:
        weekday_stats['posture_quality'] = 0
    
    weekday_stats['total_hours'] = weekday_stats['total_duration'] / 3600
    
    # Yoga stats
    yoga_stats = {
        'total_sessions': yoga_sessions.count(),
        'total_duration': yoga_sessions.aggregate(Sum('duration'))['duration__sum'] or 0,
    }
    yoga_stats['total_hours'] = yoga_stats['total_duration'] / 3600
    
    # This week stats
    week_weekday = weekday_sessions.filter(date__gte=week_ago)
    week_yoga = yoga_sessions.filter(date__gte=week_ago)
    
    this_week_stats = {
        'sessions': week_weekday.count() + week_yoga.count(),
        'hours': ((week_weekday.aggregate(Sum('duration'))['duration__sum'] or 0) +
                  (week_yoga.aggregate(Sum('duration'))['duration__sum'] or 0)) / 3600,
    }
    
    # Overall stats
    total_sessions = weekday_stats['total_sessions'] + yoga_stats['total_sessions']
    total_hours = weekday_stats['total_hours'] + yoga_stats['total_hours']
    avg_session_minutes = (weekday_stats['total_duration'] + yoga_stats['total_duration']) / total_sessions / 60 if total_sessions > 0 else 0
    
    stats = {
        'weekday': weekday_stats,
        'yoga': yoga_stats,
        'this_week': this_week_stats,
        'total_sessions': total_sessions,
        'total_hours': total_hours,
        'avg_session_minutes': avg_session_minutes,
    }
    
    # Generate insights
    insights = generate_health_insights(stats)
    
    context = {
        'stats': stats,
        'insights': insights,
    }
    
    return render(request, "monitor/dashboard.html", context)


def generate_health_insights(stats):
    """Generate personalized health insights based on user statistics"""
    insights = []
    
    weekday = stats['weekday']
    yoga = stats['yoga']
    
    # Blink rate insights
    if weekday['total_sessions'] > 0:
        avg_blinks = weekday['avg_blinks_per_session']
        if avg_blinks < 40:
            insights.append({
                'icon': '⚠️',
                'title': 'Low Blink Rate Detected',
                'message': f'Your average blink rate is {avg_blinks:.0f} blinks per session. This is below the healthy range (50-70). Try the 20-20-20 rule: every 20 minutes, look 20 feet away for 20 seconds, and blink consciously.',
                'type': 'danger'
            })
        elif avg_blinks < 50:
            insights.append({
                'icon': '👁️',
                'title': 'Blink Rate Could Improve',
                'message': f'Your average blink rate is {avg_blinks:.0f} blinks per session. Aim for 50-70 blinks to prevent eye strain. Practice conscious blinking exercises during breaks.',
                'type': 'warning'
            })
        else:
            insights.append({
                'icon': '✅',
                'title': 'Healthy Blink Rate',
                'message': f'Great job! Your average blink rate of {avg_blinks:.0f} blinks per session is within the healthy range. Keep it up!',
                'type': 'success'
            })
    
    # Posture insights
    if weekday['total_sessions'] > 0:
        posture = weekday['posture_quality']
        if posture < 60:
            insights.append({
                'icon': '🚨',
                'title': 'Posture Needs Attention',
                'message': f'Your posture quality is {posture:.0f}%, which means you maintain good posture only {posture:.0f}% of the time. Focus on sitting upright, keeping shoulders relaxed, and maintaining proper distance from the screen.',
                'type': 'danger'
            })
        elif posture < 80:
            insights.append({
                'icon': '📏',
                'title': 'Good Posture, Room for Improvement',
                'message': f'Your posture quality is {posture:.0f}%. You\'re doing well, but there\'s room for improvement. Set reminders to check your posture every 30 minutes.',
                'type': 'warning'
            })
        else:
            insights.append({
                'icon': '🏆',
                'title': 'Excellent Posture',
                'message': f'Outstanding! Your posture quality is {posture:.0f}%. You\'re maintaining healthy posture habits. Keep up the excellent work!',
                'type': 'success'
            })
    
    # Session frequency insights
    week_sessions = stats['this_week']['sessions']
    if week_sessions == 0:
        insights.append({
            'icon': '📅',
            'title': 'No Sessions This Week',
            'message': 'You haven\'t tracked any sessions this week. Start a monitoring session to track your health progress!',
            'type': 'warning'
        })
    elif week_sessions < 3:
        insights.append({
            'icon': '📈',
            'title': 'Increase Session Frequency',
            'message': f'You\'ve completed {week_sessions} session(s) this week. Try to track at least 5 sessions per week for better health insights.',
            'type': 'warning'
        })
    else:
        insights.append({
            'icon': '🎯',
            'title': 'Consistent Tracking',
            'message': f'Great consistency! You\'ve tracked {week_sessions} sessions this week. Regular monitoring helps build healthy habits.',
            'type': 'success'
        })
    
    # Yoga practice insights
    if yoga['total_sessions'] == 0:
        insights.append({
            'icon': '🧘',
            'title': 'Try Yoga Mode',
            'message': 'You haven\'t tried Yoga Mode yet! Weekend yoga sessions can help relieve stress, improve flexibility, and counteract the effects of prolonged sitting.',
            'type': 'warning'
        })
    elif yoga['total_sessions'] < 4:
        insights.append({
            'icon': '🌟',
            'title': 'Increase Yoga Practice',
            'message': f'You\'ve completed {yoga["total_sessions"]} yoga session(s). Aim for at least 2-3 yoga sessions per week for optimal wellness benefits.',
            'type': 'warning'
        })
    else:
        insights.append({
            'icon': '🧘‍♀️',
            'title': 'Active Yoga Practitioner',
            'message': f'Fantastic! You\'ve completed {yoga["total_sessions"]} yoga sessions totaling {yoga["total_hours"]:.1f} hours. Yoga is excellent for counteracting desk work.',
            'type': 'success'
        })
    
    # Work-life balance insight
    if weekday['total_hours'] > 0 and yoga['total_hours'] > 0:
        ratio = weekday['total_hours'] / yoga['total_hours']
        if ratio > 10:
            insights.append({
                'icon': '⚖️',
                'title': 'Balance Work and Wellness',
                'message': f'You\'ve spent {weekday["total_hours"]:.1f} hours in work mode but only {yoga["total_hours"]:.1f} hours in yoga. Consider adding more yoga sessions to balance out your screen time.',
                'type': 'warning'
            })
        else:
            insights.append({
                'icon': '💚',
                'title': 'Great Work-Wellness Balance',
                'message': f'You\'re maintaining a good balance with {weekday["total_hours"]:.1f} hours of monitored work and {yoga["total_hours"]:.1f} hours of yoga practice.',
                'type': 'success'
            })
    
    return insights


def weekday_page(request):
    print("🌐 Loading Weekday Page")
    return render(request, "monitor/weekday.html")


def weekend_page(request):
    print("🌐 Loading Weekend Page")
    return render(request, "monitor/weekend.html")


def reset_weekday_session(request):
    """Reset session-specific counters when starting a new session"""
    global weekday_cam
    
    if request.method == "POST":
        try:
            if weekday_cam is not None:
                weekday_cam.session_blink_count = 0
                weekday_cam.total_bad_posture_time = 0
                weekday_cam.bad_posture_start = None
                print("🔄 Session counters reset")
            return JsonResponse({"status": "reset"})
        except Exception as e:
            print(f"Warning: Reset error: {e}")
            return JsonResponse({"status": "error"})
    
    return JsonResponse({"status": "invalid"})


def save_weekday_session(request):
    global weekday_cam
    
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            duration = data.get("duration")

            if duration is None:
                return JsonResponse({"status": "error", "message": "No duration"})

            blink_count = 0
            bad_posture_time = 0
            
            if weekday_cam is not None:
                blink_count = getattr(weekday_cam, 'session_blink_count', 0)
                bad_posture_time = int(getattr(weekday_cam, 'total_bad_posture_time', 0))
                
                if bad_posture_time > duration:
                    bad_posture_time = duration

            WeekdaySession.objects.create(
                duration=int(duration),
                blink_count=blink_count,
                bad_posture_time=bad_posture_time
            )
            
            if weekday_cam is not None:
                weekday_cam.session_blink_count = 0
                weekday_cam.total_bad_posture_time = 0
                weekday_cam.bad_posture_start = None
            
            print(f"💾 Weekday session saved: {duration}s")
            return JsonResponse({
                "status": "saved",
                "blink_count": blink_count,
                "bad_posture_time": bad_posture_time
            })

        except Exception as e:
            print(f"❌ Error saving weekday session: {e}")
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "invalid"})


def save_session(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            duration = data.get("duration")

            if duration is None:
                return JsonResponse({"status": "error", "message": "No duration"})

            YogaSession.objects.create(duration=int(duration))
            print(f"💾 Yoga session saved: {duration} seconds")
            return JsonResponse({"status": "saved"})

        except Exception as e:
            print(f"❌ Error saving yoga session: {e}")
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "invalid"})


def session_history(request):
    sessions = YogaSession.objects.all().order_by("-date")
    print(f"📊 Loading {sessions.count()} yoga sessions")
    return render(request, "monitor/history.html", {"sessions": sessions})


def weekday_history(request):
    sessions = WeekdaySession.objects.all().order_by("-date")
    print(f"📊 Loading {sessions.count()} weekday sessions")
    return render(request, "monitor/history_weekday.html", {"sessions": sessions})


def combined_history(request):
    """Combined history view showing weekday and weekend sessions"""
    weekday_sessions = WeekdaySession.objects.all().order_by("-date")
    weekend_sessions = YogaSession.objects.all().order_by("-date")
    
    print(f"📊 Loading combined history - Weekday: {weekday_sessions.count()}, Weekend: {weekend_sessions.count()}")
    
    context = {
        'weekday_sessions': weekday_sessions,
        'weekend_sessions': weekend_sessions,
    }
    
    return render(request, "monitor/combined_history.html", context)


def chatbot_query(request):
    """Handle chatbot queries with enhanced data access"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            question = data.get('question', '').strip()
            
            if not question:
                return JsonResponse({
                    'success': False,
                    'answer': 'Please ask a question.'
                })
            
            # Get response from enhanced chatbot
            response = chatbot.answer_question(question)
            return JsonResponse(response)
        
        except Exception as e:
            print(f"❌ Chatbot error: {e}")
            return JsonResponse({
                'success': False,
                'answer': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'answer': 'Only POST requests are allowed.'
    })