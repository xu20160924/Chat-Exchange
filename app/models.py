# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .timezone_utils import get_shanghai_now, get_shanghai_today, SHANGHAI_TZ
from sqlalchemy.dialects.mysql import INTEGER


db = SQLAlchemy()


# AI Prompt Template Model
class AITemplate(db.Model):
    __tablename__ = 'ai_templates'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    user_id = db.Column(INTEGER(unsigned=True), nullable=True)
    prompt = db.Column(db.Text, nullable=False)  # The prompt text
    prompt_type = db.Column(db.String(50), nullable=False)  # image or video
    model = db.Column(db.String(128), nullable=True)  # Model used for generation
    result_url = db.Column(db.String(500), nullable=True)  # URL of the generated result
    result_data = db.Column(db.LargeBinary, nullable=True)  # Binary data for the result (optional)
    result_mime_type = db.Column(db.String(50), nullable=True)  # MIME type for binary result
    status = db.Column(db.String(50), nullable=False, default='pending')  # pending, generating, completed, failed
    error_message = db.Column(db.Text, nullable=True)  # Error message if failed
    likes_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=get_shanghai_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=get_shanghai_now, onupdate=get_shanghai_now)
    



class AITemplateLike(db.Model):
    __tablename__ = 'ai_template_likes'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    user_id = db.Column(INTEGER(unsigned=True), nullable=False)
    template_id = db.Column(INTEGER(unsigned=True), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=get_shanghai_now)
    

    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'template_id', name='_user_template_like_uc'),
    )


# Discussion Board Models
class DiscussionCategory(db.Model):
    __tablename__ = 'discussion_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(10), nullable=True)  # Emoji icon
    color = db.Column(db.String(7), nullable=True)  # Hex color
    order = db.Column(db.Integer, default=0)  # Display order
    created_at = db.Column(db.DateTime, nullable=False, default=get_shanghai_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=get_shanghai_now, onupdate=get_shanghai_now)

    posts = db.relationship('DiscussionPost', backref='category', lazy=True, cascade='all,delete')


class DiscussionPost(db.Model):
    __tablename__ = 'discussion_posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('discussion_categories.id', ondelete='CASCADE'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    
    views = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    replies_count = db.Column(db.Integer, default=0)
    
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, nullable=False, default=get_shanghai_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=get_shanghai_now, onupdate=get_shanghai_now)
    last_reply_at = db.Column(db.DateTime, nullable=False, default=get_shanghai_now)

    author = db.relationship('User', backref=db.backref('discussion_posts', lazy=True))
    replies = db.relationship('DiscussionReply', backref='post', lazy=True, cascade='all,delete', order_by='DiscussionReply.created_at')
    likes = db.relationship('DiscussionLike', backref='post', lazy=True, cascade='all,delete', foreign_keys='DiscussionLike.post_id')


class DiscussionReply(db.Model):
    __tablename__ = 'discussion_replies'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('discussion_posts.id', ondelete='CASCADE'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    parent_reply_id = db.Column(db.Integer, db.ForeignKey('discussion_replies.id', ondelete='CASCADE'), nullable=True)  # Nested replies
    
    # TODO: Uncomment after running migration (add_likes_count_to_replies.sql)
    # likes_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, nullable=False, default=get_shanghai_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=get_shanghai_now, onupdate=get_shanghai_now)

    author = db.relationship('User', backref=db.backref('discussion_replies', lazy=True))
    parent_reply = db.relationship('DiscussionReply', backref='child_replies', remote_side=[id], lazy=True)
    likes = db.relationship('DiscussionLike', backref='reply', lazy=True, cascade='all,delete', foreign_keys='DiscussionLike.reply_id')


class DiscussionLike(db.Model):
    __tablename__ = 'discussion_likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('discussion_posts.id', ondelete='CASCADE'), nullable=True)
    reply_id = db.Column(db.Integer, db.ForeignKey('discussion_replies.id', ondelete='CASCADE'), nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=get_shanghai_now)

    user = db.relationship('User', backref=db.backref('discussion_likes', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='_user_post_like_uc'),
        db.UniqueConstraint('user_id', 'reply_id', name='_user_reply_like_uc'),
    )


# class DiscussionPostView(db.Model):
#     """Track unique views for discussion posts"""
#     __tablename__ = 'discussion_post_views'
#     id = db.Column(db.Integer, primary_key=True)
#     post_id = db.Column(db.Integer, db.ForeignKey('discussion_posts.id', ondelete='CASCADE'), nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=True)  # NULL for anonymous
#     ip_address = db.Column(db.String(45), nullable=False)  # IPv4 or IPv6
#     viewed_at = db.Column(db.DateTime, nullable=False, default=get_shanghai_now)
# 
#     post = db.relationship('DiscussionPost', backref=db.backref('unique_views', lazy=True, cascade='all,delete'))
#     user = db.relationship('User', backref=db.backref('discussion_views', lazy=True))
# 
#     __table_args__ = (
#         db.Index('idx_post_user', 'post_id', 'user_id'),
#         db.Index('idx_post_ip', 'post_id', 'ip_address'),
#     )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120))
    native_languages = db.Column(db.String(255))  # comma-separated
    learning_languages = db.Column(db.String(255))  # comma-separated
    bio = db.Column(db.Text)
    learning_goal = db.Column(db.String(255))
    hobbies = db.Column(db.String(255))
    current_level = db.Column(db.String(64))
    sex = db.Column(db.String(16))  # Male/Female/Other/Prefer not to say
    age = db.Column(db.Integer)  # User's age
    avatar = db.Column(db.String(255))  # DEPRECATED: Keep for backward compatibility during migration
    avatar_data = db.Column(db.LargeBinary)  # Avatar image stored as binary data
    avatar_mime_type = db.Column(db.String(50))  # MIME type (image/jpeg, image/png, etc.)
    disabled = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=get_shanghai_now)

    sent_messages = db.relationship(
        "Message",
        foreign_keys="Message.sender_id",
        backref="sender",
        lazy=True,
        cascade="all,delete"
    )
    received_messages = db.relationship(
        "Message",
        foreign_keys="Message.recipient_id",
        backref="recipient",
        lazy=True,
        cascade="all,delete"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def get_avatar_url(self) -> str:
        """Get avatar URL - from database or default based on sex"""
        if self.avatar_data:
            # Serve avatar from database with cache-busting timestamp
            # Using created_at as version to bust cache when avatar changes
            import hashlib
            # Create a hash of the first 100 bytes of avatar_data as version
            version = hashlib.md5(self.avatar_data[:100]).hexdigest()[:8]
            return f'/user/{self.id}/avatar?v={version}'
        # Default avatar based on sex
        if self.sex == 'Female':
            return '/static/avatar_female.svg'
        return '/static/avatar_male.svg'


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # optional: simple thread key based on sender/recipient pair (unordered)
    thread_key = db.Column(db.String(64), index=True)

    @staticmethod
    def make_thread_key(user_a_id: int, user_b_id: int) -> str:
        a, b = sorted([int(user_a_id), int(user_b_id)])
        return f"{a}:{b}"


class VerificationCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), index=True, nullable=False)
    code = db.Column(db.String(8), nullable=False)
    purpose = db.Column(db.String(32), nullable=False, default="register")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    used_at = db.Column(db.DateTime)

    @staticmethod
    def generate_code(length: int = 6) -> str:
        from random import randint
        return f"{randint(0, 999999):06d}"[:length]

    @staticmethod
    def create(email: str, purpose: str = "register", ttl_minutes: int = 10) -> "VerificationCode":
        code = VerificationCode.generate_code(6)
        item = VerificationCode(
            email=email.lower().strip(),
            code=code,
            purpose=purpose,
            expires_at=get_shanghai_now() + timedelta(minutes=ttl_minutes),
        )
        db.session.add(item)
        db.session.commit()
        return item

    def mark_used(self) -> None:
        self.used_at = get_shanghai_now()
        db.session.commit()

    def is_valid(self) -> bool:
        return self.used_at is None and get_shanghai_now() <= self.expires_at


class VisitStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_count = db.Column(db.Integer, nullable=False, default=0)
    total_uv = db.Column(db.Integer, nullable=False, default=0)  # Total unique visitors
    today_date = db.Column(db.Date, nullable=False, default=get_shanghai_today)
    today_count = db.Column(db.Integer, nullable=False, default=0)
    today_uv = db.Column(db.Integer, nullable=False, default=0)  # Today's unique visitors
    total_ip_access = db.Column(db.Integer, nullable=False, default=0)  # Total requests via IP:port
    today_ip_access = db.Column(db.Integer, nullable=False, default=0)  # Today's requests via IP:port

    @staticmethod
    def touch() -> "VisitStat":
        stat = VisitStat.query.get(1)
        if stat is None:
            stat = VisitStat(id=1, total_count=0, total_uv=0, today_date=get_shanghai_today(), today_count=0, today_uv=0, total_ip_access=0, today_ip_access=0)
            db.session.add(stat)
        # rollover by date
        if stat.today_date != get_shanghai_today():
            stat.today_date = get_shanghai_today()
            stat.today_count = 0
            stat.today_uv = 0
            stat.today_ip_access = 0
        stat.total_count += 1
        stat.today_count += 1
        db.session.commit()
        return stat

    @staticmethod
    def track_ip_access() -> "VisitStat":
        """Track requests coming from IP:port (before redirect)"""
        stat = VisitStat.query.get(1)
        if stat is None:
            stat = VisitStat(id=1, total_count=0, total_uv=0, today_date=get_shanghai_today(), today_count=0, today_uv=0, total_ip_access=0, today_ip_access=0)
            db.session.add(stat)
        # rollover by date
        if stat.today_date != get_shanghai_today():
            stat.today_date = get_shanghai_today()
            stat.today_count = 0
            stat.today_uv = 0
            stat.today_ip_access = 0
        stat.total_ip_access += 1
        stat.today_ip_access += 1
        db.session.commit()
        return stat

    @staticmethod
    def track_unique_visitor(ip_address: str, user_agent: str, is_ip_access: bool = False) -> "VisitStat":
        """Track unique visitor based on IP and User-Agent"""
        stat = VisitStat.query.get(1)
        if stat is None:
            stat = VisitStat(id=1, total_count=0, total_uv=0, today_date=get_shanghai_today(), today_count=0, today_uv=0, total_ip_access=0, today_ip_access=0)
            db.session.add(stat)
        
        # rollover by date
        if stat.today_date != get_shanghai_today():
            stat.today_date = get_shanghai_today()
            stat.today_count = 0
            stat.today_uv = 0
            stat.today_ip_access = 0
        
        # Get user's language preference
        from .i18n import get_lang
        user_language = get_lang()
        
        # Check if this is a unique visitor today
        # Use SHA256 hash to handle long user agent strings (e.g., WeChat)
        import hashlib
        visitor_key_raw = f"{ip_address}:{user_agent}"
        visitor_key = hashlib.sha256(visitor_key_raw.encode('utf-8')).hexdigest()
        today_visitor = DailyUV.query.filter_by(
            visit_date=get_shanghai_today(),
            visitor_key=visitor_key
        ).first()
        
        if not today_visitor:
            # New unique visitor today
            stat.today_uv += 1
            
            # Get location information
            from .ip_utils import get_ip_location
            location_data = get_ip_location(ip_address)
            
            daily_uv = DailyUV(
                visit_date=get_shanghai_today(),
                visitor_key=visitor_key,
                ip_address=ip_address,
                user_agent=user_agent,
                location=location_data.get('location_string') if location_data else None,
                country=location_data.get('country') if location_data else None,
                city=location_data.get('city') if location_data else None,
                region=location_data.get('region') if location_data else None,
                language=user_language
            )
            db.session.add(daily_uv)
        else:
            # Existing visitor today - increment visit count
            today_visitor.visit_count += 1
            today_visitor.last_visit = get_shanghai_now()
        
        # Check if this is a unique visitor overall
        total_visitor = TotalUV.query.filter_by(visitor_key=visitor_key).first()
        if not total_visitor:
            # New unique visitor overall
            stat.total_uv += 1
            
            # Get location information
            if 'location_data' not in locals():
                from .ip_utils import get_ip_location
                location_data = get_ip_location(ip_address)
            
            total_uv = TotalUV(
                visitor_key=visitor_key,
                ip_address=ip_address,
                user_agent=user_agent,
                location=location_data.get('location_string') if location_data else None,
                country=location_data.get('country') if location_data else None,
                city=location_data.get('city') if location_data else None,
                region=location_data.get('region') if location_data else None,
                language=user_language,
                first_visit=get_shanghai_now(),
                last_visit=get_shanghai_now(),
                total_visits=1
            )
            db.session.add(total_uv)
        else:
            # Update existing visitor
            total_visitor.last_visit = get_shanghai_now()
            total_visitor.total_visits += 1
            # Update location and language if they changed
            if 'location_data' not in locals():
                from .ip_utils import get_ip_location
                location_data = get_ip_location(ip_address)
            if location_data:
                total_visitor.location = location_data.get('location_string')
                total_visitor.country = location_data.get('country')
                total_visitor.city = location_data.get('city')
                total_visitor.region = location_data.get('region')
            # Update language preference
            total_visitor.language = user_language
        
        stat.total_count += 1
        stat.today_count += 1
        
        # Track IP access if this is a direct IP:port request
        if is_ip_access:
            stat.total_ip_access += 1
            stat.today_ip_access += 1
        
        db.session.commit()
        return stat


class DailyUV(db.Model):
    """Track daily unique visitors"""
    id = db.Column(db.Integer, primary_key=True)
    visit_date = db.Column(db.Date, nullable=False, index=True)
    visitor_key = db.Column(db.String(64), nullable=False, index=True)  # SHA256 hash of IP:UserAgent
    ip_address = db.Column(db.String(45), nullable=False)  # IPv4/IPv6
    user_agent = db.Column(db.String(2000), nullable=False)  # Support long user agents (WeChat, etc.)
    location = db.Column(db.String(255), nullable=True)  # City, Region, Country
    country = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(10), nullable=True)  # User's language preference
    visit_count = db.Column(db.Integer, default=1)
    last_visit = db.Column(db.DateTime, default=get_shanghai_now)

    @staticmethod
    def get_language_stats(days: int = 30) -> list:
        """Get language statistics for the last N days"""
        end_date = get_shanghai_today()
        start_date = end_date - timedelta(days=days-1)
        
        return db.session.query(
            DailyUV.language,
            db.func.count(DailyUV.id).label('visitor_count'),
            db.func.sum(DailyUV.visit_count).label('total_visits')
        ).filter(
            DailyUV.visit_date >= start_date,
            DailyUV.visit_date <= end_date,
            DailyUV.language.isnot(None)
        ).group_by(DailyUV.language).order_by(db.func.count(DailyUV.id).desc()).all()

    @staticmethod
    def get_daily_summary(days: int = 30) -> list:
        """Get daily UV summary for the last N days"""
        end_date = get_shanghai_today()
        start_date = end_date - timedelta(days=days-1)
        
        return db.session.query(
            DailyUV.visit_date,
            db.func.count(DailyUV.id).label('unique_visitors'),
            db.func.sum(DailyUV.visit_count).label('total_visits')
        ).filter(
            DailyUV.visit_date >= start_date,
            DailyUV.visit_date <= end_date
        ).group_by(DailyUV.visit_date).order_by(DailyUV.visit_date.desc()).all()


class TotalUV(db.Model):
    """Track total unique visitors"""
    id = db.Column(db.Integer, primary_key=True)
    visitor_key = db.Column(db.String(64), nullable=False, unique=True, index=True)  # SHA256 hash of IP:UserAgent
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(2000), nullable=False)  # Support long user agents (WeChat, etc.)
    location = db.Column(db.String(255), nullable=True)  # City, Region, Country
    country = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(10), nullable=True)  # User's language preference
    first_visit = db.Column(db.DateTime, nullable=False)
    last_visit = db.Column(db.DateTime, default=get_shanghai_now)
    total_visits = db.Column(db.Integer, default=1)

    @staticmethod
    def get_total_language_stats() -> list:
        """Get total language statistics across all visitors"""
        return db.session.query(
            TotalUV.language,
            db.func.count(TotalUV.id).label('visitor_count'),
            db.func.sum(TotalUV.total_visits).label('total_visits')
        ).filter(
            TotalUV.language.isnot(None)
        ).group_by(TotalUV.language).order_by(db.func.count(TotalUV.id).desc()).all()

    @staticmethod
    def update_visitor(visitor_key: str, ip_address: str, user_agent: str):
        """Update visitor information"""
        visitor = TotalUV.query.filter_by(visitor_key=visitor_key).first()
        if visitor:
            visitor.last_visit = get_shanghai_now()
            visitor.total_visits += 1
            visitor.ip_address = ip_address
            visitor.user_agent = user_agent
        else:
            visitor = TotalUV(
                visitor_key=visitor_key,
                ip_address=ip_address,
                user_agent=user_agent,
                first_visit=get_shanghai_now(),
                last_visit=get_shanghai_now(),
                total_visits=1
            )
            db.session.add(visitor)
        db.session.commit()
        return visitor


class ApiRequest(db.Model):
    """Track detailed API requests with parameters"""
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(50), nullable=False, index=True)  # Unique request identifier
    method = db.Column(db.String(10), nullable=False)  # GET, POST, etc.
    path = db.Column(db.String(500), nullable=False, index=True)  # Request path with index for filtering
    endpoint = db.Column(db.String(100), nullable=True, index=True)  # Endpoint name with index for grouping
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(2000), nullable=True)
    referer = db.Column(db.String(500), nullable=True)
    
    # Request parameters
    query_params = db.Column(db.Text, nullable=True)  # JSON string of query parameters
    form_data = db.Column(db.Text, nullable=True)  # JSON string of form data
    headers = db.Column(db.Text, nullable=True)  # JSON string of important headers
    
    # Response info
    status_code = db.Column(db.Integer, nullable=True)
    response_time_ms = db.Column(db.Float, nullable=True)
    
    # User context
    user_id = db.Column(INTEGER(unsigned=True), db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    is_authenticated = db.Column(db.Boolean, default=False)
    
    # Timestamps with index for time-based queries
    created_at = db.Column(db.DateTime, nullable=False, default=get_shanghai_now, index=True)
    
    @staticmethod
    def track_request(request_id: str, method: str, path: str, ip_address: str, 
                     user_agent: str = None, referer: str = None, 
                     query_params: dict = None, form_data: dict = None,
                     headers: dict = None, status_code: int = None,
                     response_time_ms: float = None, user_id: int = None,
                     is_authenticated: bool = False):
        """Track a detailed API request"""
        import json
        
        # Determine endpoint name from path
        endpoint = None
        if path.startswith('/search'):
            endpoint = 'search'
        elif path.startswith('/users/'):
            endpoint = 'profile'
        elif path.startswith('/admin/'):
            endpoint = 'admin'
        elif path.startswith('/auth/'):
            endpoint = 'auth'
        elif path == '/':
            endpoint = 'home'
        
        # Convert complex data to JSON strings
        query_params_json = json.dumps(query_params) if query_params else None
        form_data_json = json.dumps(form_data) if form_data else None
        headers_json = json.dumps(headers) if headers else None
        
        api_request = ApiRequest(
            request_id=request_id,
            method=method,
            path=path,
            endpoint=endpoint,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
            query_params=query_params_json,
            form_data=form_data_json,
            headers=headers_json,
            status_code=status_code,
            response_time_ms=response_time_ms,
            user_id=user_id,
            is_authenticated=is_authenticated
        )
        
        db.session.add(api_request)
        db.session.commit()
        return api_request
    
    @staticmethod
    def get_endpoint_stats(days: int = 7):
        """Get statistics for different endpoints"""
        from datetime import timedelta
        from sqlalchemy import func
        
        end_date = get_shanghai_now()
        start_date = end_date - timedelta(days=days)
        
        return db.session.query(
            ApiRequest.endpoint,
            func.count(ApiRequest.id).label('request_count'),
            func.avg(ApiRequest.response_time_ms).label('avg_response_time'),
            func.count(func.distinct(ApiRequest.ip_address)).label('unique_ips')
        ).filter(
            ApiRequest.created_at >= start_date,
            ApiRequest.created_at <= end_date,
            ApiRequest.endpoint.isnot(None)
        ).group_by(ApiRequest.endpoint).order_by(func.count(ApiRequest.id).desc()).all()
    
    @staticmethod
    def get_search_analytics(days: int = 7):
        """Get detailed search analytics"""
        from datetime import timedelta
        from sqlalchemy import func
        import json
        
        end_date = get_shanghai_now()
        start_date = end_date - timedelta(days=days)
        
        # Get search requests with parameters
        search_requests = db.session.query(
            ApiRequest.query_params,
            ApiRequest.created_at,
            ApiRequest.ip_address,
            ApiRequest.user_agent
        ).filter(
            ApiRequest.endpoint == 'search',
            ApiRequest.created_at >= start_date,
            ApiRequest.created_at <= end_date,
            ApiRequest.query_params.isnot(None)
        ).all()
        
        # Parse and analyze search parameters
        search_analytics = {
            'total_searches': len(search_requests),
            'speak_languages': {},
            'learn_languages': {},
            'locations': {},
            'modes': {},
            'age_ranges': {},
            'sex_preferences': {}
        }
        
        for req in search_requests:
            try:
                params = json.loads(req.query_params)
                
                # Analyze speak languages
                if 'speak' in params and params['speak']:
                    lang = params['speak'].lower()
                    search_analytics['speak_languages'][lang] = search_analytics['speak_languages'].get(lang, 0) + 1
                
                # Analyze learn languages
                if 'learn' in params and params['learn']:
                    lang = params['learn'].lower()
                    search_analytics['learn_languages'][lang] = search_analytics['learn_languages'].get(lang, 0) + 1
                
                # Analyze locations
                if 'location' in params and params['location']:
                    loc = params['location'].lower()
                    search_analytics['locations'][loc] = search_analytics['locations'].get(loc, 0) + 1
                
                # Analyze modes
                if 'mode' in params and params['mode']:
                    mode = params['mode'].lower()
                    search_analytics['modes'][mode] = search_analytics['modes'].get(mode, 0) + 1
                
                # Analyze age ranges
                if 'age_min' in params and params['age_min']:
                    age_min = params['age_min']
                    search_analytics['age_ranges'][f"min_{age_min}"] = search_analytics['age_ranges'].get(f"min_{age_min}", 0) + 1
                if 'age_max' in params and params['age_max']:
                    age_max = params['age_max']
                    search_analytics['age_ranges'][f"max_{age_max}"] = search_analytics['age_ranges'].get(f"max_{age_max}", 0) + 1
                
                # Analyze sex preferences
                if 'sex' in params and params['sex']:
                    sex = params['sex'].lower()
                    search_analytics['sex_preferences'][sex] = search_analytics['sex_preferences'].get(sex, 0) + 1
                    
            except (json.JSONDecodeError, KeyError):
                continue
        
        return search_analytics
    
    @staticmethod
    def get_detailed_search_requests(days: int = 7, limit: int = 100):
        """Get detailed search requests with full parameters"""
        from datetime import timedelta
        import json
        
        end_date = get_shanghai_now()
        start_date = end_date - timedelta(days=days)
        
        requests = ApiRequest.query.filter(
            ApiRequest.endpoint == 'search',
            ApiRequest.created_at >= start_date,
            ApiRequest.created_at <= end_date,
            ApiRequest.query_params.isnot(None)
        ).order_by(ApiRequest.created_at.desc()).limit(limit).all()
        
        detailed_requests = []
        for req in requests:
            try:
                params = json.loads(req.query_params) if req.query_params else {}
                detailed_requests.append({
                    'id': req.id,
                    'created_at': req.created_at,
                    'ip_address': req.ip_address,
                    'user_agent': req.user_agent,
                    'is_authenticated': req.is_authenticated,
                    'user_id': req.user_id,
                    'response_time_ms': req.response_time_ms,
                    'status_code': req.status_code,
                    'parameters': params
                })
            except (json.JSONDecodeError, KeyError):
                continue
        
        return detailed_requests
    
    @staticmethod
    def get_request_parameters(request_id: int):
        """Get detailed parameters for a specific request"""
        import json
        
        request = ApiRequest.query.get(request_id)
        if not request:
            return None
        
        result = {
            'id': request.id,
            'method': request.method,
            'path': request.path,
            'endpoint': request.endpoint,
            'created_at': request.created_at,
            'ip_address': request.ip_address,
            'user_agent': request.user_agent,
            'referer': request.referer,
            'is_authenticated': request.is_authenticated,
            'user_id': request.user_id,
            'response_time_ms': request.response_time_ms,
            'status_code': request.status_code
        }
        
        # Parse JSON parameters
        try:
            if request.query_params:
                result['query_params'] = json.loads(request.query_params)
            if request.form_data:
                result['form_data'] = json.loads(request.form_data)
            if request.headers:
                result['headers'] = json.loads(request.headers)
        except (json.JSONDecodeError, KeyError):
            pass
        
        return result


class ContactMessage(db.Model):
    """Store contact form submissions"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    admin_reply = db.Column(db.Text, nullable=True)
    replied_at = db.Column(db.DateTime, nullable=True)

    @staticmethod
    def get_unread_count():
        """Get count of unread contact messages"""
        return ContactMessage.query.filter_by(is_read=False).count()

    @staticmethod
    def get_recent_messages(limit=10):
        """Get recent contact messages"""
        return ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(limit).all()


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(32), nullable=False, default="info")  # info, success, warning, error
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_global = db.Column(db.Boolean, default=True, nullable=False)  # 全局通知還是特定用戶
    target_user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True)  # 如果is_global=False
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)  # 過期時間，None表示永不過期
    priority = db.Column(db.Integer, default=1, nullable=False)  # 1=低, 2=中, 3=高
    
    # 關聯
    target_user = db.relationship("User", foreign_keys=[target_user_id], backref="notifications")
    
    def is_expired(self):
        """檢查通知是否已過期"""
        if self.expires_at is None:
            return False
        return get_shanghai_now() > self.expires_at
    
    def is_visible_to_user(self, user_id):
        """檢查通知是否對特定用戶可見"""
        if not self.is_active:
            return False
        if self.is_expired():
            return False
        if self.is_global:
            return True
        return self.target_user_id == user_id
    
    @staticmethod
    def get_visible_notifications(user_id=None):
        """獲取可見的通知列表"""
        query = Notification.query.filter_by(is_active=True)
        
        if user_id is not None:
            # 獲取全局通知和用戶特定通知
            query = query.filter(
                db.or_(
                    Notification.is_global == True,
                    Notification.target_user_id == user_id
                )
            )
        
        # 過濾已過期的通知
        now = get_shanghai_now()
        query = query.filter(
            db.or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > now
            )
        )
        
        return query.order_by(Notification.priority.desc(), Notification.created_at.desc()).all()


class IPPortRequest(db.Model):
    """Track requests from specific IP:port combinations"""
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)  # IPv4/IPv6
    port = db.Column(db.Integer, nullable=True, index=True)  # Port number
    ip_port_key = db.Column(db.String(100), nullable=False, unique=True, index=True)  # Combined key like "192.168.1.1:8080"
    total_requests = db.Column(db.Integer, default=0, nullable=False)
    first_request = db.Column(db.DateTime, default=get_shanghai_now, nullable=False)
    last_request = db.Column(db.DateTime, default=get_shanghai_now, nullable=False)
    user_agent = db.Column(db.String(500), nullable=True)
    
    @staticmethod
    def track_request(ip_address: str, port: int = None, user_agent: str = None):
        """Track a request from IP:port combination"""
        # Create the IP:port key
        if port:
            ip_port_key = f"{ip_address}:{port}"
        else:
            ip_port_key = ip_address
        
        # Find or create the record
        record = IPPortRequest.query.filter_by(ip_port_key=ip_port_key).first()
        
        if record:
            # Update existing record
            record.total_requests += 1
            record.last_request = get_shanghai_now()
            if user_agent:
                record.user_agent = user_agent
        else:
            # Create new record
            record = IPPortRequest(
                ip_address=ip_address,
                port=port,
                ip_port_key=ip_port_key,
                total_requests=1,
                first_request=get_shanghai_now(),
                last_request=get_shanghai_now(),
                user_agent=user_agent
            )
            db.session.add(record)
        
        db.session.commit()
        return record
    
    @staticmethod
    def get_top_ips(limit: int = 20):
        """Get top IP:port combinations by request count"""
        return IPPortRequest.query.order_by(IPPortRequest.total_requests.desc()).limit(limit).all()
    
    @staticmethod
    def get_stats():
        """Get overall statistics"""
        total_records = IPPortRequest.query.count()
        total_requests = db.session.query(db.func.sum(IPPortRequest.total_requests)).scalar() or 0
        
        return {
            'total_unique_ips': total_records,
            'total_requests': total_requests,
            'average_requests_per_ip': total_requests / total_records if total_records > 0 else 0
        }


class CrawlerRequest(db.Model):
    """Track crawler/bot requests separately from regular users"""
    id = db.Column(db.Integer, primary_key=True)
    crawler_name = db.Column(db.String(100), nullable=False, index=True)  # e.g., "Googlebot", "Bingbot"
    user_agent = db.Column(db.String(2000), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    path = db.Column(db.String(500), nullable=False, index=True)  # Requested URL path
    method = db.Column(db.String(10), nullable=False, default='GET')  # HTTP method
    status_code = db.Column(db.Integer, nullable=True)  # Response status code
    request_time = db.Column(db.DateTime, default=get_shanghai_now, nullable=False, index=True)
    
    @staticmethod
    def is_crawler(user_agent: str) -> tuple:
        """
        Detect if a user agent is a crawler/bot
        Returns: (is_crawler: bool, crawler_name: str or None)
        """
        if not user_agent:
            return False, None
        
        user_agent_lower = user_agent.lower()
        
        # Common crawler patterns
        crawler_patterns = {
            'googlebot': 'Googlebot',
            'bingbot': 'Bingbot',
            'slurp': 'Yahoo Slurp',
            'duckduckbot': 'DuckDuckBot',
            'baiduspider': 'Baiduspider',
            'yandexbot': 'YandexBot',
            'sogou': 'Sogou Spider',
            'exabot': 'Exabot',
            'facebot': 'Facebook Bot',
            'ia_archiver': 'Alexa Crawler',
            'msnbot': 'MSNBot',
            'twitterbot': 'TwitterBot',
            'applebot': 'AppleBot',
            'linkedinbot': 'LinkedInBot',
            'discordbot': 'DiscordBot',
            'telegrambot': 'TelegramBot',
            'slackbot': 'SlackBot',
            'whatsapp': 'WhatsApp',
            'spider': 'Generic Spider',
            'crawler': 'Generic Crawler',
            'bot': 'Generic Bot',
            'scraper': 'Scraper',
        }
        
        for pattern, name in crawler_patterns.items():
            if pattern in user_agent_lower:
                return True, name
        
        return False, None
    
    @staticmethod
    def track_crawler(user_agent: str, ip_address: str, path: str, method: str = 'GET', status_code: int = None):
        """Track a crawler request"""
        is_crawler, crawler_name = CrawlerRequest.is_crawler(user_agent)
        
        if not is_crawler:
            return None
        
        request = CrawlerRequest(
            crawler_name=crawler_name,
            user_agent=user_agent,
            ip_address=ip_address,
            path=path,
            method=method,
            status_code=status_code,
            request_time=get_shanghai_now()
        )
        db.session.add(request)
        db.session.commit()
        return request
    
    @staticmethod
    def get_crawler_stats(days: int = 7):
        """Get crawler statistics for the last N days"""
        start_date = get_shanghai_now() - timedelta(days=days)
        
        # Crawler count by name
        crawler_counts = db.session.query(
            CrawlerRequest.crawler_name,
            db.func.count(CrawlerRequest.id).label('request_count')
        ).filter(
            CrawlerRequest.request_time >= start_date
        ).group_by(CrawlerRequest.crawler_name).order_by(db.func.count(CrawlerRequest.id).desc()).all()
        
        # Most visited paths
        path_counts = db.session.query(
            CrawlerRequest.path,
            db.func.count(CrawlerRequest.id).label('visit_count')
        ).filter(
            CrawlerRequest.request_time >= start_date
        ).group_by(CrawlerRequest.path).order_by(db.func.count(CrawlerRequest.id).desc()).limit(20).all()
        
        # Total requests
        total_requests = CrawlerRequest.query.filter(CrawlerRequest.request_time >= start_date).count()
        
        return {
            'crawler_counts': crawler_counts,
            'path_counts': path_counts,
            'total_requests': total_requests,
            'period_days': days
        }
    
    @staticmethod
    def get_recent_crawler_requests(limit: int = 50):
        """Get recent crawler requests"""
        return CrawlerRequest.query.order_by(CrawlerRequest.request_time.desc()).limit(limit).all()


class PageVisit(db.Model):
    """Track page visits for all users (including regular users and crawlers)"""
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(500), nullable=False, index=True)
    user_agent = db.Column(db.String(2000), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    is_crawler = db.Column(db.Boolean, default=False, nullable=False, index=True)
    crawler_name = db.Column(db.String(100), nullable=True)
    referer = db.Column(db.String(500), nullable=True)  # Where the user came from
    visit_time = db.Column(db.DateTime, default=get_shanghai_now, nullable=False, index=True)
    
    @staticmethod
    def track_visit(path: str, user_agent: str, ip_address: str, referer: str = None):
        """Track a page visit"""
        # Check if it's a crawler
        is_crawler, crawler_name = CrawlerRequest.is_crawler(user_agent)
        
        visit = PageVisit(
            path=path,
            user_agent=user_agent,
            ip_address=ip_address,
            is_crawler=is_crawler,
            crawler_name=crawler_name,
            referer=referer,
            visit_time=get_shanghai_now()
        )
        db.session.add(visit)
        db.session.commit()
        return visit
    
    @staticmethod
    def get_popular_pages(days: int = 7, exclude_crawlers: bool = True, limit: int = 20):
        """Get most popular pages"""
        start_date = get_shanghai_now() - timedelta(days=days)
        
        query = db.session.query(
            PageVisit.path,
            db.func.count(PageVisit.id).label('visit_count')
        ).filter(PageVisit.visit_time >= start_date)
        
        if exclude_crawlers:
            query = query.filter(PageVisit.is_crawler == False)
        
        return query.group_by(PageVisit.path).order_by(db.func.count(PageVisit.id).desc()).limit(limit).all()
    
    @staticmethod
    def get_visit_stats(days: int = 7):
        """Get visit statistics"""
        start_date = get_shanghai_now() - timedelta(days=days)
        
        total_visits = PageVisit.query.filter(PageVisit.visit_time >= start_date).count()
        crawler_visits = PageVisit.query.filter(
            PageVisit.visit_time >= start_date,
            PageVisit.is_crawler == True
        ).count()
        user_visits = total_visits - crawler_visits
        
        return {
            'total_visits': total_visits,
            'user_visits': user_visits,
            'crawler_visits': crawler_visits,
            'crawler_percentage': (crawler_visits / total_visits * 100) if total_visits > 0 else 0,
            'period_days': days
        }
