# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
from .models import db, User, Message

msg_bp = Blueprint("msg", __name__, url_prefix="/messages")


@msg_bp.get("")
@login_required
def inbox():
    # 以 thread_key 聚合最近訊息
    threads = {}
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id)
    ).order_by(Message.created_at.desc()).all()

    for m in messages:
        threads.setdefault(m.thread_key, m)

    # 對象使用者資訊
    entries = []
    for key, last_msg in threads.items():
        a_str, b_str = key.split(":")
        other_id = int(a_str) if int(a_str) != current_user.id else int(b_str)
        other_user = User.query.get(other_id)
        entries.append({"other": other_user, "last": last_msg})

    return render_template("inbox.html", entries=entries)


@msg_bp.get("/<int:other_id>")
@login_required
def thread(other_id: int):
    other = User.query.get_or_404(other_id)
    if other.id == current_user.id:
        abort(400)

    key = Message.make_thread_key(current_user.id, other.id)
    messages = Message.query.filter_by(thread_key=key).order_by(Message.created_at.asc()).all()
    return render_template("thread.html", other=other, messages=messages)


@msg_bp.post("/<int:other_id>")
@login_required
def send_message(other_id: int):
    other = User.query.get_or_404(other_id)
    if other.id == current_user.id:
        abort(400)

    body = request.form.get("body", "").strip()
    if not body:
        return redirect(url_for("msg.thread", other_id=other.id))

    key = Message.make_thread_key(current_user.id, other.id)
    msg = Message(sender_id=current_user.id, recipient_id=other.id, body=body, thread_key=key)
    db.session.add(msg)
    db.session.commit()
    return redirect(url_for("msg.thread", other_id=other.id))
