# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify, current_app
from flask_login import login_required, current_user

from sqlalchemy import or_, and_
from datetime import date, datetime
from .models import db, User, Message, VisitStat, DailyUV, TotalUV, ContactMessage, IPPortRequest, PageVisit, ApiRequest, DiscussionCategory, DiscussionPost, DiscussionReply, DiscussionLike, AITemplate, AITemplateLike
from .i18n import t
from .timezone_utils import get_user_local_time
import os
import io
from werkzeug.utils import secure_filename
from PIL import Image
import uuid
import hashlib
import hmac
import json
from datetime import timezone

main_bp = Blueprint("main", __name__)





@main_bp.get("/")
def index():
    # Track unique visitor
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '127.0.0.1'))
    user_agent = request.headers.get('User-Agent', '')
    stat = VisitStat.track_unique_visitor(ip_address, user_agent)
    return render_template("index.html", stat=stat, users=[], hide_discussion_entry=True)


@main_bp.get("/robots.txt")
def robots_txt():
    """Serve robots.txt for search engine crawlers"""
    from flask import Response
    content = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /messages/
Disallow: /notifications/
Disallow: /api/
Disallow: /auth/logout

Sitemap: https://chat-exchange.online/sitemap.xml

# Crawl-delay for courtesy
Crawl-delay: 1
"""
    return Response(content, mimetype='text/plain')


@main_bp.get("/sitemap.xml")
def sitemap_xml():
    """Generate XML sitemap for search engines"""
    from flask import Response
    from datetime import datetime
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Static pages
    urls = [
        {'loc': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': '/search', 'priority': '0.9', 'changefreq': 'daily'},
        {'loc': '/auth/register', 'priority': '0.8', 'changefreq': 'weekly'},
        {'loc': '/auth/login', 'priority': '0.7', 'changefreq': 'weekly'},
    ]
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url_info in urls:
        xml_content += '  <url>\n'
        xml_content += f'    <loc>https://chat-exchange.online{url_info["loc"]}</loc>\n'
        xml_content += f'    <lastmod>{today}</lastmod>\n'
        xml_content += f'    <changefreq>{url_info["changefreq"]}</changefreq>\n'
        xml_content += f'    <priority>{url_info["priority"]}</priority>\n'
        xml_content += '  </url>\n'
    
    xml_content += '</urlset>'
    
    return Response(xml_content, mimetype='application/xml')


@main_bp.get("/search")
def search():
    speak = request.args.get("speak", "").strip().lower()  # I speak
    learn = request.args.get("learn", "").strip().lower()  # I'm learning
    q_location = request.args.get("location", "").strip().lower()
    mode = request.args.get("mode", "exchange").strip().lower()  # exchange | any
    
    # Age filtering
    age_min = request.args.get("age_min", "").strip()
    age_max = request.args.get("age_max", "").strip()
    
    # Sex filtering
    sex = request.args.get("sex", "").strip()

    # Check if any search criteria was provided
    has_search_params = bool(speak or learn or q_location or age_min or age_max or sex)
    
    # 若無任何條件，回傳空集合避免整庫掃描
    if not has_search_params:
        return render_template("search.html", users=[], searched=False, user_times={})

    query = User.query

    if mode == "exchange" and (speak or learn):
        # 互補配對：對方母語含我的學習，且對方學習含我的母語（若兩者都有填）
        conds = []
        if learn:
            conds.append(User.native_languages.ilike(f"%{learn}%"))
        if speak:
            conds.append(User.learning_languages.ilike(f"%{speak}%"))
        if conds:
            query = query.filter(and_(*conds))
    else:
        # 任一匹配：對方母語或學習語言命中任一條件
        lang_conds = []
        if speak:
            lang_conds.append(User.learning_languages.ilike(f"%{speak}%"))
            lang_conds.append(User.native_languages.ilike(f"%{speak}%"))
        if learn:
            lang_conds.append(User.native_languages.ilike(f"%{learn}%"))
            lang_conds.append(User.learning_languages.ilike(f"%{learn}%"))
        if lang_conds:
            query = query.filter(or_(*lang_conds))

    if q_location:
        query = query.filter(User.location.ilike(f"%{q_location}%"))

    # Age filtering
    if age_min:
        try:
            min_age = int(age_min)
            if min_age >= 18:
                query = query.filter(User.age >= min_age)
        except ValueError:
            pass  # Invalid age_min, ignore
    
    if age_max:
        try:
            max_age = int(age_max)
            if max_age >= 18:  # Only check minimum, no maximum restriction
                query = query.filter(User.age <= max_age)
        except ValueError:
            pass  # Invalid age_max, ignore

    # Sex filtering
    if sex:
        query = query.filter(User.sex == sex)

    # Exclude disabled users from search results
    query = query.filter(User.disabled == False)

    users = query.order_by(User.created_at.desc()).limit(100).all()
    
    # Calculate local time for each user based on their location
    user_times = {}
    for user in users:
        if user.location:
            local_time_info = get_user_local_time(user.location)
            if local_time_info:
                user_times[user.id] = local_time_info
    
    return render_template("search.html", users=users, user_times=user_times, searched=True)


@main_bp.get("/users/<int:user_id>")
def profile(user_id: int):
    user = User.query.get_or_404(user_id)
    return render_template("users/profile.html", profile=user)


@main_bp.get("/settings/profile")
@login_required
def edit_profile_page():
    return render_template("users/edit_profile.html")


@main_bp.post("/settings/profile")
@login_required
def edit_profile_submit():
    # Handle password change if provided
    current_password = request.form.get("current_password", "").strip()
    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()
    
    if current_password or new_password or confirm_password:
        # If any password field is filled, all must be filled
        if not (current_password and new_password and confirm_password):
            flash(t("Please fill in all password fields"), "error")
            return redirect(url_for("main.edit_profile_page"))
        
        # Verify current password
        if not current_user.check_password(current_password):
            flash(t("Current password is incorrect"), "error")
            return redirect(url_for("main.edit_profile_page"))
        
        # Check if new passwords match
        if new_password != confirm_password:
            flash(t("New passwords do not match"), "error")
            return redirect(url_for("main.edit_profile_page"))
        
        # Validate new password length
        if len(new_password) < 6:
            flash(t("New password must be at least 6 characters long"), "error")
            return redirect(url_for("main.edit_profile_page"))
        
        # Update password
        current_user.set_password(new_password)
        flash(t("Password updated successfully!"), "success")
    
    # Username cannot be changed after registration - keep original name
    # current_user.name = request.form.get("name", current_user.name)  # Disabled - username is immutable
    current_user.location = request.form.get("location", "")
    current_user.native_languages = request.form.get("native_languages", "")
    current_user.learning_languages = request.form.get("learning_languages", "")
    current_user.bio = request.form.get("bio", "")
    current_user.learning_goal = request.form.get("learning_goal", "")
    current_user.hobbies = request.form.get("hobbies", "")
    current_user.current_level = request.form.get("current_level", "")
    current_user.sex = request.form.get("sex", "")
    
    # Handle age field
    age_str = request.form.get("age", "").strip()
    if age_str:
        try:
            age = int(age_str)
            if age >= 18:  # Must be 18 or older, no maximum
                current_user.age = age
            else:
                flash(t("Age must be greater than or equal to 18"), "error")
                return redirect(url_for("main.edit_profile_page"))
        except ValueError:
            flash(t("Please enter a valid age"), "error")
            return redirect(url_for("main.edit_profile_page"))
    else:
        current_user.age = None

    # Handle avatar upload if file is present
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and file.filename != '':
            # Validate file
            if allowed_file(file.filename):
                try:
                    # Read and validate file size
                    file_data = file.read()
                    if len(file_data) <= MAX_FILE_SIZE:
                        file.seek(0)  # Reset file pointer
                        
                        # Process image
                        img = Image.open(file)
                        img.verify()
                        file.seek(0)
                        img = Image.open(file)
                        
                        # Convert RGBA to RGB if necessary
                        if img.mode in ('RGBA', 'LA', 'P'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                            img = background
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Crop to square and resize
                        width, height = img.size
                        if width != height:
                            size = min(width, height)
                            left = (width - size) // 2
                            top = (height - size) // 2
                            img = img.crop((left, top, left + size, top + size))
                        
                        img = img.resize(AVATAR_SIZE, Image.Resampling.LANCZOS)
                        
                        # Determine format
                        ext = file.filename.rsplit('.', 1)[1].lower()
                        if ext in ('jpg', 'jpeg'):
                            mime_type = 'image/jpeg'
                            format_name = 'JPEG'
                        else:
                            mime_type = 'image/png'
                            format_name = 'PNG'
                        
                        # Save to BytesIO
                        img_buffer = io.BytesIO()
                        if format_name == 'JPEG':
                            img.save(img_buffer, format_name, quality=90, optimize=True)
                        else:
                            img.save(img_buffer, format_name, optimize=True)
                        
                        # Store in database
                        current_user.avatar_data = img_buffer.getvalue()
                        current_user.avatar_mime_type = mime_type
                        current_user.avatar = None
                    else:
                        flash(t("File too large. Maximum size is 5MB"), "error")
                        return redirect(url_for("main.edit_profile_page"))
                except Exception as e:
                    flash(t("Error uploading avatar. Please try again"), "error")
                    return redirect(url_for("main.edit_profile_page"))
            else:
                flash(t("Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WEBP"), "error")
                return redirect(url_for("main.edit_profile_page"))
    
    # Handle avatar deletion
    if request.form.get("delete_avatar") == "true":
        current_user.avatar_data = None
        current_user.avatar_mime_type = None
        current_user.avatar = None

    db.session.commit()
    flash(t("Profile updated successfully!"), "success")
    return redirect(url_for("main.edit_profile_page"))


# Avatar upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
AVATAR_SIZE = (400, 400)  # Standard avatar size


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main_bp.post("/settings/upload-avatar")
@login_required
def upload_avatar():
    """Handle avatar upload with validation and processing - stores in database"""
    # Check if file was uploaded
    if 'avatar' not in request.files:
        flash(t("No file selected"), "error")
        return redirect(url_for("main.edit_profile_page"))
    
    file = request.files['avatar']
    
    # Check if file has a name
    if file.filename == '':
        flash(t("No file selected"), "error")
        return redirect(url_for("main.edit_profile_page"))
    
    # Validate file extension
    if not allowed_file(file.filename):
        flash(t("Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WEBP"), "error")
        return redirect(url_for("main.edit_profile_page"))
    
    try:
        # Read file and check size
        file_data = file.read()
        if len(file_data) > MAX_FILE_SIZE:
            flash(t("File too large. Maximum size is 5MB"), "error")
            return redirect(url_for("main.edit_profile_page"))
        
        # Reset file pointer for PIL
        file.seek(0)
        
        # Open and validate image
        try:
            img = Image.open(file)
            img.verify()  # Verify it's a valid image
            file.seek(0)  # Reset again after verify
            img = Image.open(file)  # Reopen after verify
        except Exception as e:
            flash(t("Invalid image file"), "error")
            return redirect(url_for("main.edit_profile_page"))
        
        # Convert RGBA to RGB if necessary (for JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize image to standard size (square, centered crop)
        width, height = img.size
        if width != height:
            # Crop to square (center)
            size = min(width, height)
            left = (width - size) // 2
            top = (height - size) // 2
            img = img.crop((left, top, left + size, top + size))
        
        # Resize to standard avatar size
        img = img.resize(AVATAR_SIZE, Image.Resampling.LANCZOS)
        
        # Determine output format
        ext = file.filename.rsplit('.', 1)[1].lower()
        # Use JPEG for better compression
        if ext in ('jpg', 'jpeg'):
            mime_type = 'image/jpeg'
            format_name = 'JPEG'
        else:
            mime_type = 'image/png'
            format_name = 'PNG'
        
        # Save image to BytesIO buffer
        img_buffer = io.BytesIO()
        if format_name == 'JPEG':
            img.save(img_buffer, format_name, quality=90, optimize=True)
        else:
            img.save(img_buffer, format_name, optimize=True)
        
        # Get binary data
        img_binary = img_buffer.getvalue()
        
        # Store in database
        current_user.avatar_data = img_binary
        current_user.avatar_mime_type = mime_type
        current_user.avatar = None  # Clear old filename field
        db.session.commit()
        
        flash(t("Avatar updated successfully"), "success")
        return redirect(url_for("main.edit_profile_page"))
        
    except Exception as e:
        flash(t("Error uploading avatar. Please try again"), "error")
        return redirect(url_for("main.edit_profile_page"))


@main_bp.post("/settings/delete-avatar")
@login_required
def delete_avatar():
    """Delete custom avatar and revert to default"""
    if current_user.avatar_data:
        # Clear avatar data from database
        current_user.avatar_data = None
        current_user.avatar_mime_type = None
        current_user.avatar = None
        db.session.commit()
        flash(t("Avatar deleted successfully"), "success")
    
    return redirect(url_for("main.edit_profile_page"))


@main_bp.get("/user/<int:user_id>/avatar")
def serve_avatar(user_id):
    """Serve avatar image from database"""
    user = User.query.get_or_404(user_id)
    
    if not user.avatar_data:
        # Return 404 if user has no custom avatar
        from flask import abort
        abort(404)
    
    # Get version parameter for cache busting
    version = request.args.get('v', '')
    
    # Return image from database with proper content type
    # Use ETag for cache validation instead of long max-age
    import hashlib
    etag = hashlib.md5(user.avatar_data[:100]).hexdigest()
    
    return Response(
        user.avatar_data,
        mimetype=user.avatar_mime_type or 'image/jpeg',
        headers={
            'Cache-Control': 'public, max-age=86400',  # Cache for 1 day (was 1 year)
            'ETag': f'"{etag}"',
            'Content-Disposition': f'inline; filename="avatar_{user_id}.jpg"'
        }
    )


@main_bp.get("/admin/analytics")
@login_required
def admin_analytics():
    """Admin analytics page - only accessible to admin users"""
    # Simple admin check - users with @admin.com email
    if not current_user.email.endswith("@admin.com"):
        return redirect(url_for("main.index"))
    
    # Get VisitStat
    stat = VisitStat.query.get(1)
    if not stat:
        stat = VisitStat(id=1, total_count=0, total_uv=0, today_date=date.today(), today_count=0, today_uv=0)
    
    # Get daily summary for last 30 days
    daily_summary = DailyUV.get_daily_summary(30) if DailyUV else []
    
    # Get recent visitors with their last visited page (exclude localhost/127.0.0.1)
    recent_visitors_raw = TotalUV.query.filter(
        TotalUV.ip_address.notin_(['127.0.0.1', 'localhost', '::1'])
    ).order_by(TotalUV.last_visit.desc()).limit(20).all() if TotalUV else []
    
    # Enhance recent visitors with last visited page path
    recent_visitors = []
    for visitor in recent_visitors_raw:
        # Get the last page visit for this visitor
        last_page_visit = PageVisit.query.filter_by(
            ip_address=visitor.ip_address
        ).order_by(PageVisit.visit_time.desc()).first()
        
        # Create a visitor dict with additional page path info
        visitor_data = {
            'ip_address': visitor.ip_address,
            'user_agent': visitor.user_agent,
            'location': visitor.location,
            'country': visitor.country,
            'city': visitor.city,
            'region': visitor.region,
            'language': visitor.language,
            'first_visit': visitor.first_visit,
            'last_visit': visitor.last_visit,
            'total_visits': visitor.total_visits,
            'last_page': last_page_visit.path if last_page_visit else 'N/A'
        }
        recent_visitors.append(visitor_data)
    
    # Get contact messages stats
    contact_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all() if ContactMessage else []
    unread_contact_count = ContactMessage.get_unread_count() if ContactMessage else 0
    
    # Get country statistics
    country_stats = []
    total_visitors = 0
    if TotalUV:
        from sqlalchemy import func
        country_data = db.session.query(
            TotalUV.country, 
            func.count(TotalUV.id)
        ).filter(
            TotalUV.country.isnot(None),
            TotalUV.country != 'Unknown',
            TotalUV.country != 'Local'
        ).group_by(TotalUV.country).order_by(func.count(TotalUV.id).desc()).limit(10).all()
        
        country_stats = [(country, count) for country, count in country_data]
        total_visitors = sum(count for _, count in country_data)
    
    # Get language statistics
    language_stats = []
    if DailyUV:
        language_stats = DailyUV.get_language_stats(30)
    
    # Get total language statistics
    total_language_stats = []
    if TotalUV:
        total_language_stats = TotalUV.get_total_language_stats()
    
    # Get user and message counts
    from sqlalchemy import func
    total_users = db.session.query(func.count(User.id)).scalar() or 0
    total_messages = db.session.query(func.count(Message.id)).scalar() or 0
    
    return render_template("admin/analytics.html", 
                         stat=stat, 
                         daily_summary=daily_summary,
                         recent_visitors=recent_visitors,
                         contact_messages=contact_messages,
                         unread_contact_count=unread_contact_count,
                         country_stats=country_stats,
                         total_visitors=total_visitors,
                         language_stats=language_stats,
                         total_language_stats=total_language_stats,
                         total_users=total_users,
                         total_messages=total_messages)


@main_bp.get("/admin/ip-stats")
@login_required
def admin_ip_stats():
    """Admin IP:Port access statistics page"""
    if not current_user.email.endswith("@admin.com"):
        return redirect(url_for("main.index"))
    
    # Get VisitStat
    stat = VisitStat.query.get(1)
    if not stat:
        stat = VisitStat(id=1, total_count=0, total_uv=0, today_date=date.today(), today_count=0, today_uv=0, total_ip_access=0, today_ip_access=0)
    
    # Calculate IP access percentage
    ip_access_percentage = 0
    if stat.total_count > 0:
        ip_access_percentage = (stat.total_ip_access / stat.total_count) * 100
    
    # Calculate today's IP access percentage
    today_ip_access_percentage = 0
    if stat.today_count > 0:
        today_ip_access_percentage = (stat.today_ip_access / stat.today_count) * 100
    
    return render_template("admin/ip_stats.html", 
                         stat=stat,
                         ip_access_percentage=ip_access_percentage,
                         today_ip_access_percentage=today_ip_access_percentage)


@main_bp.get("/admin/crawler-stats")
@login_required
def admin_crawler_stats():
    """Admin crawler and page visit statistics page"""
    if not current_user.email.endswith("@admin.com"):
        return redirect(url_for("main.index"))
    
    from .models import CrawlerRequest, PageVisit
    
    # Get crawler stats for last 7 days
    crawler_stats = CrawlerRequest.get_crawler_stats(days=7)
    
    # Get recent crawler requests (last 50)
    recent_crawlers = CrawlerRequest.get_recent_crawler_requests(limit=50)
    
    # Get visit stats for last 7 days
    visit_stats = PageVisit.get_visit_stats(days=7)
    
    # Get popular pages (excluding crawlers)
    popular_pages_users = PageVisit.get_popular_pages(days=7, exclude_crawlers=True, limit=20)
    
    # Get popular pages (including crawlers)
    popular_pages_all = PageVisit.get_popular_pages(days=7, exclude_crawlers=False, limit=20)
    
    return render_template("admin/crawler_stats.html",
                         crawler_stats=crawler_stats,
                         recent_crawlers=recent_crawlers,
                         visit_stats=visit_stats,
                         popular_pages_users=popular_pages_users,
                         popular_pages_all=popular_pages_all)


@main_bp.get("/admin/api-stats")
@login_required
def admin_api_stats():
    """Admin API request statistics page"""
    if not current_user.email.endswith("@admin.com"):
        return redirect(url_for("main.index"))
    
    # Get endpoint statistics
    endpoint_stats = ApiRequest.get_endpoint_stats(days=7)
    
    # Get search analytics
    search_analytics = ApiRequest.get_search_analytics(days=7)
    
    # Get detailed search requests
    detailed_search_requests = ApiRequest.get_detailed_search_requests(days=7, limit=50)
    
    # Get recent API requests
    recent_requests = ApiRequest.query.order_by(ApiRequest.created_at.desc()).limit(50).all()
    
    # Get request count by hour for last 24 hours
    from datetime import timedelta
    from sqlalchemy import func
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    hourly_requests = db.session.query(
        func.date_format(ApiRequest.created_at, '%Y-%m-%d %H:00:00').label('hour'),
        func.count(ApiRequest.id).label('request_count')
    ).filter(
        ApiRequest.created_at >= start_time,
        ApiRequest.created_at <= end_time
    ).group_by('hour').order_by('hour').all()
    
    return render_template("admin/api_stats.html",
                         endpoint_stats=endpoint_stats,
                         search_analytics=search_analytics,
                         detailed_search_requests=detailed_search_requests,
                         recent_requests=recent_requests,
                         hourly_requests=hourly_requests)


@main_bp.get("/admin/api-request/<int:request_id>")
@login_required
def admin_api_request_details(request_id):
    """Get detailed parameters for a specific API request"""
    if not current_user.email.endswith("@admin.com"):
        return redirect(url_for("main.index"))
    
    from flask import jsonify
    request_details = ApiRequest.get_request_parameters(request_id)
    
    if not request_details:
        return jsonify({"error": "Request not found"}), 404
    
    return jsonify(request_details)


@main_bp.post("/contact")
@login_required
def contact_submit():
    """Handle contact form submission"""
    # Get name and email from hidden fields (auto-filled from current_user)
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    
    # Get subject and message from user input
    subject = request.form.get("subject", "").strip()
    message = request.form.get("message", "").strip()
    
    # Validate only the user-input fields (subject and message are required)
    if not subject or not message:
        flash(t("Please fill in all fields"), "error")
        return redirect(url_for("main.index"))
    
    # Use current_user data if form fields are empty (shouldn't happen, but safeguard)
    if not name:
        name = current_user.name
    if not email:
        email = current_user.email
    
    # Get visitor info
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '127.0.0.1'))
    user_agent = request.headers.get('User-Agent', '')
    
    # Create contact message
    contact_msg = ContactMessage(
        name=name,
        email=email,
        subject=subject,
        message=message,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.session.add(contact_msg)
    db.session.commit()
    
    # Use URL parameter to trigger success modal instead of flash message
    return redirect(url_for("main.index", contact_sent="1"))


@main_bp.get("/admin/contact")
@login_required
def admin_contact_messages():
    """Admin contact messages page"""
    if not current_user.email.endswith("@admin.com"):
        return redirect(url_for("main.index"))
    
    # Get contact messages
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    unread_count = ContactMessage.get_unread_count()
    
    return render_template("admin/contact_messages.html", 
                         messages=messages, 
                         unread_count=unread_count)


@main_bp.post("/admin/contact/<int:message_id>/read")
@login_required
def admin_mark_read(message_id):
    """Mark contact message as read"""
    if not current_user.email.endswith("@admin.com"):
        return redirect(url_for("main.index"))
    
    message = ContactMessage.query.get_or_404(message_id)
    message.is_read = True
    db.session.commit()
    
    flash(t("Message marked as read"), "success")
    return redirect(url_for("main.admin_contact_messages"))


@main_bp.post("/admin/contact/<int:message_id>/reply")
@login_required
def admin_reply_message(message_id):
    """Reply to contact message"""
    if not current_user.email.endswith("@admin.com"):
        return redirect(url_for("main.index"))
    
    message = ContactMessage.query.get_or_404(message_id)
    reply_text = request.form.get("reply", "").strip()
    
    if reply_text:
        message.admin_reply = reply_text
        message.replied_at = datetime.utcnow()
        message.is_read = True
        db.session.commit()
        flash(t("Reply sent successfully"), "success")
    else:
        flash(t("Reply cannot be empty"), "error")
    
    return redirect(url_for("main.admin_contact_messages"))


@main_bp.get("/admin/users")
@login_required
def admin_user_management():
    """Admin user management page"""
    if not current_user.email.endswith("@admin.com"):
        return redirect(url_for("main.index"))
    
    # Get all users with pagination
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Calculate total statistics across all users (not just current page)
    total_users = User.query.count()
    active_users = User.query.filter_by(disabled=False).count()
    disabled_users = User.query.filter_by(disabled=True).count()
    
    return render_template("admin/user_management.html", 
                         users=users,
                         total_users=total_users,
                         active_users=active_users,
                         disabled_users=disabled_users)


@main_bp.post("/admin/users/<int:user_id>/toggle")
@login_required
def admin_toggle_user(user_id):
    """Toggle user disabled status"""
    if not current_user.email.endswith("@admin.com"):
        return redirect(url_for("main.index"))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent disabling admin users
    if user.email.endswith("@admin.com"):
        flash(t("Cannot disable admin users"), "error")
        return redirect(url_for("main.admin_user_management"))
    
    user.disabled = not user.disabled
    db.session.commit()
    
    status = t("disabled") if user.disabled else t("enabled")
    flash(t("User has been {status}").format(status=status), "success")
    return redirect(url_for("main.admin_user_management"))


@main_bp.post("/admin/users/<int:user_id>/delete")
@login_required
def admin_delete_user(user_id):
    """Delete user account"""
    if not current_user.email.endswith("@admin.com"):
        return redirect(url_for("main.index"))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting admin users
    if user.email.endswith("@admin.com"):
        flash(t("Cannot delete admin users"), "error")
        return redirect(url_for("main.admin_user_management"))
    
    # Delete user and related data
    db.session.delete(user)
    db.session.commit()
    
    flash(t("User account has been deleted"), "success")
    return redirect(url_for("main.admin_user_management"))


# =====================
# Discussion Board Routes
# =====================

@main_bp.route('/discussions')
def discussions_index():
    """Main discussion board page with posts"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', type=int)
    sort = request.args.get('sort', 'latest')  # latest, hot, replies
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Get all categories
    categories = DiscussionCategory.query.order_by(DiscussionCategory.order).all()
    
    # Build query for posts
    query = DiscussionPost.query
    
    # Filter by category
    current_category = category
    if category:
        query = query.filter_by(category_id=category)
    
    # Sort posts
    if sort == 'latest':
        query = query.order_by(DiscussionPost.is_pinned.desc(), DiscussionPost.created_at.desc())
    elif sort == 'hot':
        query = query.order_by(DiscussionPost.is_pinned.desc(), DiscussionPost.likes_count.desc(), DiscussionPost.last_reply_at.desc())
    elif sort == 'replies':
        query = query.order_by(DiscussionPost.is_pinned.desc(), DiscussionPost.replies_count.desc(), DiscussionPost.last_reply_at.desc())
    
    # Paginate posts
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    posts = pagination.items
    
    # Get hot posts (for sidebar)
    hot_posts = DiscussionPost.query.order_by(DiscussionPost.likes_count.desc()).limit(10).all()
    
    # If AJAX request, return JSON data
    if is_ajax:
        # Convert posts to JSON-serializable format
        posts_data = []
        for post in posts:
            author = post.author
            post_data = {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
                'views': post.views,
                'likes': post.likes_count,
                'reply_count': post.replies_count,
                'is_pinned': post.is_pinned,
                'category': {
                    'id': post.category.id,
                    'name': post.category.name,
                    'color': post.category.color,
                    'icon': post.category.icon
                },
                'author': {
                    'id': author.id,
                    'name': author.name
                }
            }
            posts_data.append(post_data)
        
        # Convert hot posts to JSON-serializable format
        hot_posts_data = []
        for post in hot_posts[:5]:  # Limit to 5 for sidebar
            hot_posts_data.append({
                'id': post.id,
                'title': post.title,
                'views': post.views
            })
        
        # Pagination data
        pagination_data = {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num
        }
        
        return jsonify({
            'posts': posts_data,
            'hot_posts': hot_posts_data,
            'pagination': pagination_data,
            'current_category': current_category,
            'current_sort': sort
        })
    
    # Regular HTML request - render template
    return render_template(
        'discussions/index.html',
        categories=categories,
        current_category=current_category,
        sort=sort,
        pagination=pagination,
        posts=posts,
        hot_posts=hot_posts
    )


@main_bp.route('/discussions/post/<int:post_id>')
def discussions_post_detail(post_id):
    """Discussion post detail page with replies"""
    # Get the post
    post = DiscussionPost.query.get_or_404(post_id)
    
    # Increment view count
    post.views += 1
    db.session.commit()
    
    # Get all categories (for sidebar)
    categories = DiscussionCategory.query.order_by(DiscussionCategory.order).all()
    
    # Get replies with nested replies
    replies = post.replies
    
    # Get hot posts (for sidebar)
    hot_posts = DiscussionPost.query.order_by(DiscussionPost.likes_count.desc()).limit(10).all()
    
    # Check if current user liked the post
    is_liked = False
    reply_liked = {}
    if current_user.is_authenticated:
        is_liked = DiscussionLike.query.filter_by(user_id=current_user.id, post_id=post_id).first() is not None
        
        # Check which replies the user has liked
        for reply in replies:
            reply_liked[reply.id] = DiscussionLike.query.filter_by(user_id=current_user.id, reply_id=reply.id).first() is not None
    
    return render_template(
        'discussions/post_detail.html',
        post=post,
        categories=categories,
        replies=replies,
        hot_posts=hot_posts,
        is_liked=is_liked,
        reply_liked=reply_liked
    )


@main_bp.route('/discussions/new', methods=['GET'])
@login_required
def discussions_new_post():
    """Form for creating a new discussion post"""
    # Get all categories
    categories = DiscussionCategory.query.order_by(DiscussionCategory.order).all()
    
    return render_template('discussions/new_post.html', categories=categories)


@main_bp.route('/discussions/post/create', methods=['POST'])
@login_required
def discussions_create_post():
    """Create a new discussion post"""
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    category_id = request.form.get('category_id', type=int)
    
    # Debug logging
    import logging
    logging.info(f"Form data - title: '{title}', content: '{content}', category_id: {category_id}")
    logging.info(f"Raw form data: {request.form}")
    
    # Validate input with detailed messages
    if not title:
        flash(t('Please fill in all required fields') + ' (Missing: Title)', 'error')
        return redirect(url_for('main.discussions_new_post'))
    
    if not content:
        flash(t('Please fill in all required fields') + ' (Missing: Content)', 'error')
        return redirect(url_for('main.discussions_new_post'))
    
    if not category_id:
        flash(t('Please fill in all required fields') + ' (Missing: Category)', 'error')
        return redirect(url_for('main.discussions_new_post'))
    
    if len(title) > 200:
        flash(t('Title cannot exceed 200 characters'), 'error')
        return redirect(url_for('main.discussions_new_post'))
    
    # Create new post
    post = DiscussionPost(
        title=title,
        content=content,
        category_id=category_id,
        author_id=current_user.id
    )
    
    db.session.add(post)
    db.session.commit()
    
    flash(t('Post created successfully'), 'success')
    return redirect(url_for('main.discussions_post_detail', post_id=post.id))


@main_bp.route('/discussions/post/<int:post_id>/reply', methods=['POST'])
@login_required
def discussions_add_reply(post_id):
    """Add a reply to a discussion post"""
    content = request.form.get('content', '').strip()
    parent_reply_id = request.form.get('parent_reply', type=int)
    
    # Validate input
    if not content:
        flash(t('Please fill in the reply content'), 'error')
        return redirect(url_for('main.discussions_post_detail', post_id=post_id))
    
    # Get post
    post = DiscussionPost.query.get_or_404(post_id)
    
    # Create reply
    reply = DiscussionReply(
        post_id=post_id,
        author_id=current_user.id,
        content=content,
        parent_reply_id=parent_reply_id
    )
    
    # Update post's last reply time and reply count
    post.last_reply_at = datetime.now()
    post.replies_count += 1
    
    db.session.add(reply)
    db.session.commit()
    
    # Redirect back to post detail, scrolling to the new reply
    return redirect(url_for('main.discussions_post_detail', post_id=post_id) + f'#reply-{reply.id}')


@main_bp.route('/discussions/post/<int:post_id>/like', methods=['POST'])
@login_required
def discussions_like_post(post_id):
    """Like/unlike a discussion post"""
    # Get post
    post = DiscussionPost.query.get_or_404(post_id)
    
    # Check if already liked
    existing_like = DiscussionLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if existing_like:
        # Unlike
        post.likes_count -= 1
        db.session.delete(existing_like)
        liked = False
    else:
        # Like
        post.likes_count += 1
        new_like = DiscussionLike(user_id=current_user.id, post_id=post_id)
        db.session.add(new_like)
        liked = True
    
    db.session.commit()
    
    # Return JSON response for AJAX
    return {
        'success': True,
        'liked': liked,
        'likes': post.likes_count
    }


@main_bp.route('/test-width')
def test_width():
    """Test page to verify container width settings"""
    return render_template('test_width.html')


@main_bp.route('/discussions/reply/<int:reply_id>/like', methods=['POST'])
@login_required
def discussions_like_reply(reply_id):
    """Like/unlike a discussion reply"""
    # Get reply
    reply = DiscussionReply.query.get_or_404(reply_id)
    
    # Check if already liked
    existing_like = DiscussionLike.query.filter_by(user_id=current_user.id, reply_id=reply_id).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        liked = False
    else:
        # Like
        new_like = DiscussionLike(user_id=current_user.id, reply_id=reply_id)
        db.session.add(new_like)
        liked = True
    
    db.session.commit()
    
    # Count likes using the relationship
    likes_count = len(reply.likes)
    
    # Return JSON response for AJAX
    return {
        'success': True,
        'liked': liked,
        'likes': likes_count
    }


@main_bp.route('/ai-templates/')
def ai_templates_list():
    """List all AI templates"""
    templates = AITemplate.query.filter(AITemplate.status == 'completed').order_by(AITemplate.created_at.desc()).all()
    return render_template('ai_templates/list.html', templates=templates)


@main_bp.route('/ai-templates/new')
def ai_templates_new():
    """Create new AI template page"""
    return render_template('ai_templates/new.html')


@main_bp.route('/ai-templates/create', methods=['POST'])
@login_required
def ai_templates_create():
    """Create new AI template"""
    prompt = request.form.get('prompt', '')
    template_type = request.form.get('template_type', 'image')
    
    if not prompt:
        flash('Prompt is required', 'error')
        return redirect(url_for('main.ai_templates_new'))
    
    template = AITemplate(
        prompt=prompt,
        template_type=template_type,
        user_id=current_user.id,
        status='pending'
    )
    db.session.add(template)
    db.session.commit()
    
    return redirect(url_for('main.ai_templates_show', template_id=template.id))


@main_bp.route('/ai-templates/<int:template_id>')
def ai_templates_show(template_id):
    """Show AI template details"""
    template = AITemplate.query.get_or_404(template_id)
    return render_template('ai_templates/show.html', template=template)


@main_bp.route('/ai-templates/<int:template_id>/generate', methods=['POST'])
@login_required
def ai_templates_generate(template_id):
    """Generate AI content for a template"""
    template = AITemplate.query.get_or_404(template_id)
    
    flash('AI generation is currently unavailable', 'info')
    return redirect(url_for('main.ai_templates_show', template_id=template_id))


@main_bp.route('/ai-templates/admin/generate')
@login_required
def ai_templates_admin_generate():
    """Admin generate page"""
    if not str(current_user.email or "").endswith("@admin.com"):
        return redirect(url_for('main.index'))
    return render_template('ai_templates/admin_generate.html')


@main_bp.route('/ai-templates/admin/generate/image')
@login_required
def ai_templates_admin_generate_image():
    """Admin generate image page"""
    if not str(current_user.email or "").endswith("@admin.com"):
        return redirect(url_for('main.index'))
    return render_template('ai_templates/show.html', template=template)


@main_bp.route('/ai-templates/<int:template_id>/like', methods=['POST'])
@login_required
def ai_templates_like(template_id):
    """Like an AI template"""
    template = AITemplate.query.get_or_404(template_id)
    
    existing_like = AITemplateLike.query.filter_by(
        user_id=current_user.id,
        template_id=template_id
    ).first()
    
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({'liked': False, 'likes_count': template.likes_count})
    
    like = AITemplateLike(user_id=current_user.id, template_id=template_id)
    db.session.add(like)
    db.session.commit()
    return jsonify({'liked': True, 'likes_count': template.likes_count})


@main_bp.route('/serve/ai-result/<int:template_id>')
def serve_ai_result(template_id):
    """Serve AI generated result file"""
    template = AITemplate.query.get_or_404(template_id)
    
    if not template.result_data:
        return "No result available", 404
    
    return Response(template.result_data, mimetype=template.result_mime_type)


