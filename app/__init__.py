# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
from datetime import date, datetime
from .models import db, User, VisitStat, PageVisit, CrawlerRequest, ApiRequest
from .i18n import t, get_lang, set_lang, SUPPORTED_LANGS
import logging
import time

login_manager = LoginManager()
login_manager.login_view = "auth.login_page"
login_manager.login_message = None  # Disable the default "Please log in to access this page." message

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app():
    # Load environment variables from .env file
    load_dotenv()
    
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object("config.Config")

    # Set up detailed logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler('request_tracking.log'),
            logging.FileHandler('app_lifecycle.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Log Flask app initialization
    logger.info("🚀 Flask application initialization started")
    logger.info(f"📅 App init time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    logger.info("🔧 Initializing database connection...")
    db.init_app(app)
    logger.info("✅ Database connection initialized")
    
    logger.info("🔧 Initializing login manager...")
    login_manager.init_app(app)
    logger.info("✅ Login manager initialized")

    @app.context_processor
    def inject_i18n():
        stat = VisitStat.query.get(1)
        # IP access is now blocked, so is_ip_access is always False
        return {"t": t, "current_lang": get_lang(), "langs": SUPPORTED_LANGS, "visit_stat": stat, "is_ip_access": False}

    @app.route("/lang/<code>")
    def switch_lang(code: str):
        """Switch language and redirect back"""
        if code == "auto":
            # Clear explicit language choice to enable auto-detection
            session.pop("lang", None)
            session.pop("lang_explicit", None)
        else:
            set_lang(code)
        return redirect(request.referrer or url_for("main.index"))

    @app.route('/ads.txt')
    def ads_txt():
        """Serve Google AdSense ads.txt file for domain verification"""
        from flask import send_from_directory
        import os
        root_dir = os.path.join(app.root_path, '..')
        return send_from_directory(root_dir, 'ads.txt', mimetype='text/plain')

    @app.route('/.well-known/acme-challenge/<path:filename>')
    def letsencrypt_challenge(filename):
        """Serve Let's Encrypt challenge files for SSL certificate validation"""
        from flask import send_from_directory
        import os
        challenge_dir = os.path.join(app.root_path, '..', '.well-known', 'acme-challenge')
        return send_from_directory(challenge_dir, filename)

    @app.before_request
    def track_and_redirect():
        """Track all requests and redirect IP access to domain"""
        # Store start time for this request
        request._start_time = time.time()
        request._request_id = f"{time.time():.6f}"
        
        logger = logging.getLogger(__name__)
        logger.info(f"[{request._request_id}] 🔵 REQUEST START: {request.method} {request.path} from {request.environ.get('REMOTE_ADDR', '?')}")
        
        # Skip for static files, favicons, Let's Encrypt challenges, and notifications API
        if (request.path.startswith('/static/') or 
            request.path.startswith('/favicon') or 
            request.path.startswith('/.well-known/acme-challenge/') or
            request.path == '/notifications/api/visible'):
            logger.info(f"[{request._request_id}] ⚪ SKIP: Static/favicon/challenge/notifications API - {request.path}")
            return None
        
        # Get request info
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '127.0.0.1'))
        
        # Skip tracking for localhost/127.0.0.1 to exclude development traffic
        if ip_address in ['127.0.0.1', 'localhost', '::1'] or request.host in ['127.0.0.1:5000', 'localhost:5000', '127.0.0.1:5001', 'localhost:5001']:
            logger.info(f"[{request._request_id}] ⚪ SKIP: Localhost/development request from {ip_address}")
            return None
        
        user_agent = request.headers.get('User-Agent', '')
        referer = request.headers.get('Referer', None)
        
        # Capture detailed request parameters for API tracking
        query_params = dict(request.args) if request.args else None
        form_data = dict(request.form) if request.form else None
        
        # Capture important headers
        important_headers = {
            'User-Agent': request.headers.get('User-Agent'),
            'Referer': request.headers.get('Referer'),
            'Accept': request.headers.get('Accept'),
            'Accept-Language': request.headers.get('Accept-Language'),
            'Accept-Encoding': request.headers.get('Accept-Encoding'),
            'Connection': request.headers.get('Connection'),
            'X-Forwarded-For': request.headers.get('X-Forwarded-For'),
            'X-Real-IP': request.headers.get('X-Real-IP')
        }
        
        # Get user context
        user_id = None
        is_authenticated = False
        try:
            from flask_login import current_user
            if current_user.is_authenticated:
                user_id = current_user.id
                is_authenticated = True
        except:
            pass
        
        logger.info(f"[{request._request_id}] 📝 START PageVisit.track_visit")
        track_start = time.time()
        
        try:
            # Track page visit (distinguishes crawlers automatically)
            PageVisit.track_visit(
                path=request.path,
                user_agent=user_agent,
                ip_address=ip_address,
                referer=referer
            )
            track_duration = (time.time() - track_start) * 1000
            logger.info(f"[{request._request_id}] ✅ END PageVisit.track_visit ({track_duration:.2f}ms)")
        except Exception as e:
            track_duration = (time.time() - track_start) * 1000
            logger.error(f"[{request._request_id}] ❌ ERROR PageVisit.track_visit ({track_duration:.2f}ms): {e}")
        
        # Track crawler requests separately if it's a crawler
        is_crawler, crawler_name = CrawlerRequest.is_crawler(user_agent)
        if is_crawler:
            logger.info(f"[{request._request_id}] 🤖 START CrawlerRequest.track_crawler (crawler={crawler_name})")
            crawler_start = time.time()
            
            try:
                CrawlerRequest.track_crawler(
                    user_agent=user_agent,
                    ip_address=ip_address,
                    path=request.path,
                    method=request.method
                )
                crawler_duration = (time.time() - crawler_start) * 1000
                logger.info(f"[{request._request_id}] ✅ END CrawlerRequest.track_crawler ({crawler_duration:.2f}ms)")
            except Exception as e:
                crawler_duration = (time.time() - crawler_start) * 1000
                logger.error(f"[{request._request_id}] ❌ ERROR CrawlerRequest.track_crawler ({crawler_duration:.2f}ms): {e}")
        
        # Block IP:port access - only allow domain access
        # Note: Configure allowed domains via environment variable if needed
        logger.debug(f"[{request._request_id}] Request from {request.host}")
        
        # Track detailed API request
        logger.info(f"[{request._request_id}] 📊 START ApiRequest.track_request")
        api_start = time.time()
        
        try:
            ApiRequest.track_request(
                request_id=request._request_id,
                method=request.method,
                path=request.path,
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
                query_params=query_params,
                form_data=form_data,
                headers=important_headers,
                user_id=user_id,
                is_authenticated=is_authenticated
            )
            api_duration = (time.time() - api_start) * 1000
            logger.info(f"[{request._request_id}] ✅ END ApiRequest.track_request ({api_duration:.2f}ms)")
        except Exception as e:
            api_duration = (time.time() - api_start) * 1000
            logger.error(f"[{request._request_id}] ❌ ERROR ApiRequest.track_request ({api_duration:.2f}ms): {e}")
        
        before_request_duration = (time.time() - request._start_time) * 1000
        logger.info(f"[{request._request_id}] ⚡ BEFORE_REQUEST COMPLETE ({before_request_duration:.2f}ms total)")

    @app.after_request
    def log_request_complete(response):
        """Log request completion and total time"""
        if hasattr(request, '_start_time') and hasattr(request, '_request_id'):
            total_duration = (time.time() - request._start_time) * 1000
            logger = logging.getLogger(__name__)
            logger.info(f"[{request._request_id}] ✅ REQUEST COMPLETE: {response.status_code} - Total time: {total_duration:.2f}ms")
            
            # Update API request with response info
            try:
                api_request = ApiRequest.query.filter_by(request_id=request._request_id).first()
                if api_request:
                    api_request.status_code = response.status_code
                    api_request.response_time_ms = total_duration
                    db.session.commit()
                    logger.info(f"[{request._request_id}] 📊 UPDATED ApiRequest with response info")
            except Exception as e:
                logger.error(f"[{request._request_id}] ❌ ERROR updating ApiRequest: {e}")
            
            # Log slow requests (>1 second)
            if total_duration > 1000:
                logger.warning(f"[{request._request_id}] ⚠️  SLOW REQUEST: {total_duration:.2f}ms for {request.method} {request.path}")
        
        return response

    logger.info("🔧 Setting up database tables...")
    with app.app_context():
        # Import additional modules that define db models (so metadata includes them)
        # Keep this isolated to avoid affecting existing modules.
        # 只創建現有的表，不創建 notification 表（手動創建）
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"📊 Existing tables: {existing_tables}")
        
        # 創建除 notification 之外的所有表
        metadata = db.metadata
        tables_created = []
        for table_name, table in metadata.tables.items():
            if table_name != 'notification' and table_name not in existing_tables:
                try:
                    table.create(db.engine)
                    tables_created.append(table_name)
                    logger.info(f"✅ Created table: {table_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to create table {table_name}: {e}")
        
        if tables_created:
            logger.info(f"📊 Database tables created: {tables_created}")
        else:
            logger.info("📊 All required tables already exist")
    
    logger.info("✅ Database setup completed")

    logger.info("🔧 Registering blueprints...")
    from .auth import auth_bp
    from .views import main_bp
    from .messaging import msg_bp
    from .notifications import notifications_bp

    app.register_blueprint(auth_bp)
    logger.info("✅ Auth blueprint registered")
    app.register_blueprint(main_bp)
    logger.info("✅ Main blueprint registered")
    app.register_blueprint(msg_bp)
    logger.info("✅ Messaging blueprint registered")
    app.register_blueprint(notifications_bp)
    logger.info("✅ Notifications blueprint registered")

    # After request logging
    @app.after_request
    def log_response(response):
        """Log response details"""
        if hasattr(request, '_start_time') and hasattr(request, '_request_id'):
            total_duration = (time.time() - request._start_time) * 1000
            logger = logging.getLogger(__name__)
            logger.info(f"[{request._request_id}] 🟢 RESPONSE: {response.status_code} | Total: {total_duration:.2f}ms")
        return response
    
    # Teardown handler to properly close database sessions
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Remove database sessions at the end of the request"""
        from flask import has_request_context
        
        logger = logging.getLogger(__name__)
        request_id = None
        teardown_start = time.time()
        
        # Safely get request_id only if we're in a request context
        if has_request_context():
            try:
                if hasattr(request, '_request_id'):
                    request_id = request._request_id
                    logger.info(f"[{request_id}] 🧹 TEARDOWN: Cleaning up session")
            except RuntimeError:
                pass  # Not in request context
        
        try:
            db.session.remove()
            if exception:
                db.session.rollback()
                if request_id:
                    logger.error(f"[{request_id}] ❌ EXCEPTION in teardown: {exception}")
                else:
                    logger.error(f"❌ EXCEPTION in teardown (no request context): {exception}")
        except Exception as e:
            logger.error(f"❌ Error in teardown handler: {e}")
        
        # Log teardown completion only if we have request context
        if request_id:
            teardown_duration = (time.time() - teardown_start) * 1000
            logger.info(f"[{request_id}] ✅ TEARDOWN COMPLETE ({teardown_duration:.2f}ms)")

    logger.info("🎉 Flask application initialization completed successfully!")
    logger.info(f"📅 App ready time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return app
