"""
fingerprint.py
"""

from user_agents import parse


def collect_fingerprint(request):
    ua_string = request.headers.get("User-Agent", "Unknown")
    user_agent = parse(ua_string)

    fingerprint = {
        "ip": request.remote_addr or request.headers.get("X-Forwarded-For", "Unknown"),
        "user_agent": ua_string,
        "browser": f"{user_agent.browser.family} {user_agent.browser.version_string}",
        "os": f"{user_agent.os.family} {user_agent.os.version_string}",
        "device": user_agent.device.family,
        "is_mobile": user_agent.is_mobile,
        "is_bot": user_agent.is_bot,
        "language": request.headers.get("Accept-Language", "Unknown"),
    }
    return fingerprint