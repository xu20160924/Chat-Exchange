from typing import Dict
# -*- coding: utf-8 -*-
from flask import session, request

SUPPORTED_LANGS = [
    ("en", "English"),
    ("es", "Español"),
    ("fr", "Français"),
    ("de", "Deutsch"),
    ("it", "Italiano"),
    ("pt", "Português"),
    ("ar", "العربية"),
    ("ja", "日本語"),
    ("zh", "中文"),
    ("ko", "한국어"),
    ("ru", "Русский"),
]

# 簡易詞條；未覆蓋時回退英文 key
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # General
        "Search": "Search",
        "Reset": "Reset",
        "My Profile": "My Profile",
        "Messages": "Messages",
        "Sign out": "Sign out",
        "Sign in": "Sign in",
        "Sign up": "Sign up",
        "Native": "Native",
        "Learning": "Learning",
        "Location": "Location",
        "Email": "Email",
        "Password": "Password",
        "Name": "Name",
        "Save": "Save",
        "Back": "Back",
        "All": "All",
        "Close": "Close",
        "Cancel": "Cancel",
        "Delete": "Delete",
        "Previous": "Previous",
        "Next": "Next",

        # Homepage & Auth
        "Discover language partners": "Discover language partners",
        "See the latest members:": "See the latest members:",
        "No members yet — be the first!": "No members yet — be the first!",
        "Sign in title": "Sign in",
        "Don't have an account?": "Don't have an account?",
        "Already have an account?": "Already have an account?",
        "Create account": "Create account",
        "Please enter your name (at least 2 characters)": "Please enter your name (at least 2 characters)",
        "Invalid email or password": "Invalid email or password",
        "Please fill in name, email and password": "Please fill in name, email and password",
        "Email is already in use": "Email is already in use",
        "Your account has been disabled. Please contact support.": "Your account has been disabled. Please contact support.",

        # Discussion Board
        "Discussion Board": "Discussion Board",
        "Language Learning Community": "Language Learning Community",
        "Share ideas, exchange experiences, and grow together": "Share ideas, exchange experiences, and grow together",
        "A vibrant space where language learners connect and support each other": "A vibrant space where language learners connect and support each other",
        "Share Your Story": "Share Your Story",
        "Have a tip, question, or experience? Share it with our community!": "Have a tip, question, or experience? Share it with our community!",
        "Start a Discussion": "Start a Discussion",
        "Join Our Community": "Join Our Community",
        "Sign in to start discussions and connect with fellow learners": "Sign in to start discussions and connect with fellow learners",
        "Categories": "Categories",
        "Latest": "Latest",
        "Hot": "Hot",
        "Most Replies": "Most Replies",
        "Pinned": "Pinned",
        "Locked": "Locked",
        "views": "views",
        "replies": "replies",
        "likes": "likes",
        "Author": "Author",
        "No replies yet. Be the first to reply!": "No replies yet. Be the first to reply!",
        "Related Posts": "Related Posts",
        "Add Your Reply": "Add Your Reply",
        "Share your thoughts...": "Share your thoughts...",
        "Post Reply": "Post Reply",
        "Replies": "Replies",
        "This post is locked and cannot accept new replies.": "This post is locked and cannot accept new replies.",
        "Please": "Please",
        "login": "login",
        "to reply to this post.": "to reply to this post.",
        "Create New Post": "Create New Post",
        "Share Your Thoughts": "Share Your Thoughts",
        "Start a conversation, ask a question, or share your experience with the community": "Start a conversation, ask a question, or share your experience with the community",
        "Category": "Category",
        "Select a category": "Select a category",
        "Choose the most appropriate category for your post": "Choose the most appropriate category for your post",
        "Title": "Title",
        "Enter a clear and descriptive title": "Enter a clear and descriptive title",
        "A good title helps others understand your topic quickly": "A good title helps others understand your topic quickly",
        "Content": "Content",
        "Share your thoughts, questions, or experiences in detail...": "Share your thoughts, questions, or experiences in detail...",
        "The more details you provide, the better responses you will receive": "The more details you provide, the better responses you will receive",
        "Publish Post": "Publish Post",
        "Community Guidelines": "Community Guidelines",
        "Be respectful and considerate to others": "Be respectful and considerate to others",
        "Stay on topic and choose the right category": "Stay on topic and choose the right category",
        "Provide clear and detailed information": "Provide clear and detailed information",
        "Search before posting to avoid duplicates": "Search before posting to avoid duplicates",
        "Use proper language and formatting": "Use proper language and formatting",
        "Tips for Great Posts": "Tips for Great Posts",
        "For Questions": "For Questions",
        "Explain what you have tried already": "Explain what you have tried already",
        "Be specific about your problem": "Be specific about your problem",
        "Provide examples when possible": "Provide examples when possible",
        "For Sharing": "For Sharing",
        "Share practical tips and examples": "Share practical tips and examples",
        "Explain why it worked for you": "Explain why it worked for you",
        "Be open to different perspectives": "Be open to different perspectives",
        "You have a saved draft. Would you like to restore it?": "You have a saved draft. Would you like to restore it?",
        "Oldest": "Oldest",
        "Newest": "Newest",
        "Popular": "Popular",
        "Start Something Amazing!": "Start Something Amazing!",
        "This community is waiting for your voice. Share your insights, ask questions, or start a conversation about language learning.": "This community is waiting for your voice. Share your insights, ask questions, or start a conversation about language learning.",
        "What can you share?": "What can you share?",
        "Learning tips • Culture insights • Questions • Resources • Success stories": "Learning tips • Culture insights • Questions • Resources • Success stories",
        "Start the Conversation": "Start the Conversation",
        "Hot Topics": "Hot Topics",

        # Flash Messages
        "Please fill in all required fields": "Please fill in all required fields",
        "Title cannot exceed 200 characters": "Title cannot exceed 200 characters",
        "Post created successfully": "Post created successfully",
        "Please fill in the reply content": "Please fill in the reply content",

        # Category Names & Descriptions
        "category_learning_tips": "Learning Tips",
        "category_learning_tips_desc": "Share and discover effective techniques for language acquisition.",
        "category_language_exchange": "Language Exchange",
        "category_language_exchange_desc": "Find partners, ask for practice, and organize exchanges.",
        "category_general_discussion": "General Discussion",
        "category_general_discussion_desc": "Chat about anything related to language and culture.",
        "category_culture_and_travel": "Culture & Travel",
        "category_culture_and_travel_desc": "Discuss traditions, destinations, and cultural experiences.",
        "category_resources_and_tools": "Resources & Tools",
        "category_resources_and_tools_desc": "Recommend apps, books, websites, and other learning aids.",
        "category_challenges_and_goals": "Challenges & Goals",
        "category_challenges_and_goals_desc": "Share your progress, set goals, and motivate each other.",
    },
    "zh": {
        # General
        "Search": "搜索",
        "Reset": "重置",
        "My Profile": "我的资料",
        "Messages": "消息",
        "Sign out": "退出",
        "Sign in": "登录",
        "Sign up": "注册",
        "Native": "母语",
        "Learning": "学习",
        "Location": "地区",
        "Email": "Email",
        "Password": "密码",
        "Name": "姓名",
        "Save": "保存",
        "Back": "返回",
        "All": "全部",
        "Close": "关闭",
        "Cancel": "取消",
        "Delete": "删除",
        "Previous": "上一页",
        "Next": "下一页",

        # Homepage & Auth
        "Discover language partners": "发现语言伙伴",
        "See the latest members:": "看看最新加入的用户：",
        "No members yet — be the first!": "目前还没有用户，快来成为第一个吧！",
        "Sign in title": "登录",
        "Don't have an account?": "还没有账号？",
        "Already have an account?": "已有账号？",
        "Create account": "创建账号",
        "Please enter your name (at least 2 characters)": "请输入您的姓名（至少2个字符）",
        "Invalid email or password": "账号或密码错误",
        "Please fill in name, email and password": "请完整填写姓名、Email 与密码",
        "Email is already in use": "Email 已被使用",
        "Your account has been disabled. Please contact support.": "您的账户已被禁用，请联系客服。",

        # Discussion Board
        "Discussion Board": "讨论区",
        "Language Learning Community": "语言学习社区",
        "Share ideas, exchange experiences, and grow together": "分享想法、交流经验、共同成长",
        "A vibrant space where language learners connect and support each other": "一个充满活力的空间，供语言学习者交流和互相支持",
        "Share Your Story": "分享你的故事",
        "Have a tip, question, or experience? Share it with our community!": "有任何技巧、问题或经验吗？与我们的社区分享吧！",
        "Start a Discussion": "开始讨论",
        "Join Our Community": "加入我们的社区",
        "Sign in to start discussions and connect with fellow learners": "登录后即可开始讨论并与其他学习者交流",
        "Categories": "分类",
        "Latest": "最新",
        "Hot": "热门",
        "Most Replies": "最多回复",
        "Pinned": "已置顶",
        "Locked": "已锁定",
        "views": "浏览",
        "replies": "回复",
        "likes": "赞",
        "Author": "作者",
        "No replies yet. Be the first to reply!": "还没有回复。成为第一个回复的人吧！",
        "Related Posts": "相关帖子",
        "Add Your Reply": "添加你的回复",
        "Share your thoughts...": "分享你的想法...",
        "Post Reply": "发表回复",
        "Replies": "回复",
        "This post is locked and cannot accept new replies.": "该帖子已被锁定，无法接受新的回复。",
        "Please": "请",
        "login": "登录",
        "to reply to this post.": "以回复此帖子。",
        "Create New Post": "创建新帖子",
        "Share Your Thoughts": "分享你的想法",
        "Start a conversation, ask a question, or share your experience with the community": "开始对话、提出问题或与社区分享你的经验",
        "Category": "分类",
        "Select a category": "选择一个分类",
        "Choose the most appropriate category for your post": "为你的帖子选择最合适的分类",
        "Title": "标题",
        "Enter a clear and descriptive title": "输入一个清晰、描述性的标题",
        "A good title helps others understand your topic quickly": "一个好的标题能帮助他人快速了解你的主题",
        "Content": "内容",
        "Share your thoughts, questions, or experiences in detail...": "详细分享你的想法、问题或经历...",
        "The more details you provide, the better responses you will receive": "你提供的细节越多，收到的回复就越好",
        "Publish Post": "发布帖子",
        "Community Guidelines": "社区准则",
        "Be respectful and considerate to others": "尊重并体谅他人",
        "Stay on topic and choose the right category": "保持主题并选择正确的分类",
        "Provide clear and detailed information": "提供清晰详细的信息",
        "Search before posting to avoid duplicates": "发帖前先搜索，避免重复",
        "Use proper language and formatting": "使用恰当的语言和格式",
        "Tips for Great Posts": "优质帖子小贴士",
        "For Questions": "提问时",
        "Explain what you have tried already": "说明你已经尝试过什么",
        "Be specific about your problem": "具体说明你的问题",
        "Provide examples when possible": "尽可能提供例子",
        "For Sharing": "分享时",
        "Share practical tips and examples": "分享实用的技巧和例子",
        "Explain why it worked for you": "解释为什么它对你有效",
        "Be open to different perspectives": "对不同观点持开放态度",
        "You have a saved draft. Would you like to restore it?": "你有一个已保存的草稿。要恢复它吗？",
        "Oldest": "最早",
        "Newest": "最新",
        "Popular": "热门",
        "Start Something Amazing!": "开始创造精彩！",
        "This community is waiting for your voice. Share your insights, ask questions, or start a conversation about language learning.": "这个社区正等待你的声音。分享你的见解，提出问题，或开始一场关于语言学习的对话。",
        "What can you share?": "你能分享什么？",
        "Learning tips • Culture insights • Questions • Resources • Success stories": "学习技巧 • 文化见解 • 问题 • 资源 • 成功故事",
        "Start the Conversation": "开始对话",
        "Hot Topics": "热门话题",

        # Flash Messages
        "Please fill in all required fields": "请填写所有必填项",
        "Title cannot exceed 200 characters": "标题不能超过200个字符",
        "Post created successfully": "帖子创建成功",
        "Please fill in the reply content": "请填写回复内容",

        # Category Names & Descriptions
        "category_learning_tips": "学习技巧",
        "category_learning_tips_desc": "分享和发现有效的语言学习技巧。",
        "category_language_exchange": "语言交换",
        "category_language_exchange_desc": "寻找伙伴，请求练习，并组织交流活动。",
        "category_general_discussion": "综合讨论",
        "category_general_discussion_desc": "聊任何与语言和文化有关的话题。",
        "category_culture_and_travel": "文化与旅行",
        "category_culture_and_travel_desc": "讨论传统、目的地和文化体验。",
        "category_resources_and_tools": "资源与工具",
        "category_resources_and_tools_desc": "推荐应用、书籍、网站和其他学习辅助工具。",
        "category_challenges_and_goals": "挑战与目标",
        "category_challenges_and_goals_desc": "分享你的进步，设定目标，互相激励。",
    },
    # Other languages can be added here
}

def detect_browser_language() -> str:
    """Detect browser language preference from Accept-Language header"""
    accept_language_header = request.headers.get('Accept-Language', '')
    
    # Debug logging
    import logging
    logging.info(f"Accept-Language header: {accept_language_header}")
    
    if not accept_language_header:
        return "en"
    
    # Parse Accept-Language header
    languages = []
    
    # Parse the header: "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"
    for lang_part in accept_language_header.split(','):
        lang_part = lang_part.strip()
        if ';' in lang_part:
            lang, q_value = lang_part.split(';', 1)
            try:
                quality = float(q_value.split('=')[1])
            except (ValueError, IndexError):
                quality = 1.0
        else:
            lang = lang_part
            quality = 1.0
        
        languages.append((lang.strip(), quality))
    
    # Sort by quality (highest first)
    languages.sort(key=lambda x: x[1], reverse=True)
    
    # Find the first supported language
    supported_codes = [code for code, _ in SUPPORTED_LANGS]
    
    for lang, _ in languages:
        # Check exact match first
        if lang in supported_codes:
            logging.info(f"Detected language (exact match): {lang}")
            return lang
        
        # Check language code without country code (e.g., zh-CN -> zh)
        lang_code = lang.split('-')[0]
        if lang_code in supported_codes:
            logging.info(f"Detected language (prefix match): {lang_code} from {lang}")
            return lang_code
    
    logging.info("No language match found, defaulting to 'en'")
    return "en"

def get_lang() -> str:
    # Check if language is explicitly set by user (via language switcher)
    if "lang" in session and session.get("lang_explicit"):
        code = session.get("lang")
        if code in dict(SUPPORTED_LANGS):
            return code
    
    # Always auto-detect browser language if not explicitly set
    detected_lang = detect_browser_language()
    
    # Save detected language but don't mark as explicit
    # This allows browser language to update dynamically
    if "lang_explicit" not in session:
        session["lang"] = detected_lang
    
    return detected_lang

def set_lang(code: str) -> None:
    if code in dict(SUPPORTED_LANGS):
        session["lang"] = code
        session["lang_explicit"] = True  # Mark as explicitly chosen by user

def t(key: str, lang: str = None) -> str:
    """
    Translate a key to the specified language or current language
    
    Args:
        key: Translation key
        lang: Optional language code (defaults to current language)
    
    Returns:
        Translated string
    """
    code = lang if lang else get_lang()
    
    # First, try to get the translation from the requested language
    translation = TRANSLATIONS.get(code, {}).get(key)
    
    # If not found, fall back to English
    if translation is None:
        translation = TRANSLATIONS.get("en", {}).get(key)
        
    # If still not found, return the key itself
    if translation is None:
        return key
        
    return translation
