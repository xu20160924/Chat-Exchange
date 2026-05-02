# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from .models import db, Notification, User
from .i18n import t

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.get("/")
@login_required
def list_notifications():
    """顯示用戶的通知列表"""
    notifications = Notification.get_visible_notifications(current_user.id)
    return render_template("notifications/list.html", notifications=notifications)


@notifications_bp.post("/<int:notification_id>/dismiss")
@login_required
def dismiss_notification(notification_id):
    """關閉/忽略通知"""
    notification = Notification.query.get_or_404(notification_id)
    
    # 檢查用戶是否有權限關閉這個通知
    if not notification.is_visible_to_user(current_user.id):
        flash("您没有权限关闭此通知", "error")
        return redirect(url_for("notifications.list_notifications"))
    
    # 對於全局通知，我們不能直接刪除，只能標記為對該用戶不可見
    # 這裡我們可以創建一個用戶通知狀態表，但為了簡化，我們暫時跳過
    # 或者我們可以設置一個很短的過期時間
    if notification.is_global:
        # 設置為立即過期（對該用戶）
        notification.expires_at = datetime.utcnow()
    else:
        # 用戶特定通知可以直接刪除
        db.session.delete(notification)
    
    db.session.commit()
    flash("通知已關閉", "success")
    return redirect(url_for("notifications.list_notifications"))


# 管理員功能
@notifications_bp.get("/admin")
@login_required
def admin_list():
    """管理員通知管理頁面"""
    # 簡單的權限檢查 - 這裡可以根據需要改進
    if not current_user.email.endswith("@admin.com"):  # 簡單的管理員檢查
        flash("您没有管理员权限", "error")
        return redirect(url_for("main.index"))
    
    notifications = Notification.query.order_by(Notification.created_at.desc()).all()
    return render_template("notifications/admin.html", notifications=notifications)


@notifications_bp.get("/admin/create")
@login_required
def admin_create_form():
    """創建通知表單"""
    if not current_user.email.endswith("@admin.com"):
        flash("您没有管理员权限", "error")
        return redirect(url_for("main.index"))
    
    return render_template("notifications/create.html")


@notifications_bp.post("/admin/create")
@login_required
def admin_create():
    """創建新通知"""
    if not current_user.email.endswith("@admin.com"):
        flash("您没有管理员权限", "error")
        return redirect(url_for("main.index"))
    
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    notification_type = request.form.get("type", "info")
    priority = int(request.form.get("priority", 1))
    is_global = request.form.get("is_global") == "on"
    target_user_id = request.form.get("target_user_id")
    expires_days = request.form.get("expires_days")
    
    if not title or not content:
        flash("標題和內容不能為空", "error")
        return redirect(url_for("notifications.admin_create_form"))
    
    # 計算過期時間
    expires_at = None
    if expires_days and expires_days.isdigit():
        expires_at = datetime.utcnow() + timedelta(days=int(expires_days))
    
    notification = Notification(
        title=title,
        content=content,
        notification_type=notification_type,
        priority=priority,
        is_global=is_global,
        target_user_id=int(target_user_id) if target_user_id and not is_global else None,
        expires_at=expires_at
    )
    
    db.session.add(notification)
    db.session.commit()
    
    flash("通知創建成功", "success")
    return redirect(url_for("notifications.admin_list"))


@notifications_bp.post("/admin/<int:notification_id>/toggle")
@login_required
def admin_toggle(notification_id):
    """切換通知的激活狀態"""
    if not current_user.email.endswith("@admin.com"):
        flash("您没有管理员权限", "error")
        return redirect(url_for("main.index"))
    
    notification = Notification.query.get_or_404(notification_id)
    notification.is_active = not notification.is_active
    db.session.commit()
    
    status = "激活" if notification.is_active else "停用"
    flash(f"通知已{status}", "success")
    return redirect(url_for("notifications.admin_list"))


@notifications_bp.post("/admin/<int:notification_id>/delete")
@login_required
def admin_delete(notification_id):
    """刪除通知"""
    if not current_user.email.endswith("@admin.com"):
        flash("您没有管理员权限", "error")
        return redirect(url_for("main.index"))
    
    notification = Notification.query.get_or_404(notification_id)
    db.session.delete(notification)
    db.session.commit()
    
    flash("通知已刪除", "success")
    return redirect(url_for("notifications.admin_list"))


# API 端點 - 用於 AJAX 獲取通知 (All users, not just authenticated)
@notifications_bp.get("/api/visible")
def api_visible_notifications():
    """API: 獲取可見通知"""
    # Get user_id if authenticated, otherwise None for global notifications only
    try:
        from flask_login import current_user
        user_id = current_user.id if current_user.is_authenticated else None
    except:
        user_id = None
    
    notifications = Notification.get_visible_notifications(user_id)
    
    result = []
    for notif in notifications:
        result.append({
            "id": notif.id,
            "title": notif.title,
            "content": notif.content,
            "type": notif.notification_type,
            "priority": notif.priority,
            "created_at": notif.created_at.isoformat(),
            "expires_at": notif.expires_at.isoformat() if notif.expires_at else None
        })
    
    return jsonify({"notifications": result})
