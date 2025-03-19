from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
import ssl
import json

# SSL 인증서 검증 우회 (macOS용)
ssl._create_default_https_context = ssl._create_unverified_context

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# Slack 앱 초기화
app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

# Flask 앱 초기화
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

def get_last_message(channel_id):
    """
    채널의 마지막 메시지를 가져오는 함수입니다.
    
    Args:
        channel_id (str): 채널 ID
        
    Returns:
        dict: 마지막 메시지 정보
    """
    try:
        result = app.client.conversations_history(
            channel=channel_id,
            limit=1
        )
        
        if result["ok"] and result["messages"]:
            message = result["messages"][0]
            return {
                "text": message.get("text", ""),
                "user": message.get("user", ""),
                "timestamp": datetime.fromtimestamp(float(message.get("ts", 0))).strftime("%Y-%m-%d %H:%M:%S"),
                "thread_ts": message.get("thread_ts", None)
            }
        return None
    except Exception as e:
        logger.error(f"메시지 가져오기 실패: {str(e)}")
        return None

@app.event("message")
def handle_message_events(body, logger):
    """
    메시지 이벤트를 처리하는 함수입니다.
    """
    logger.info(f"메시지 이벤트 수신: {json.dumps(body, indent=2)}")
    
    event = body["event"]
    
    # 봇 메시지는 무시
    if "bot_id" in event:
        logger.info("봇 메시지 무시")
        return
    
    # 메시지 내용 가져오기
    text = event.get("text", "")
    channel = event.get("channel")
    user = event.get("user")
    
    logger.info(f"처리할 메시지: 채널={channel}, 사용자={user}, 내용={text}")
    
    # 명령어 처리
    if text.lower() == "안녕":
        logger.info("안녕 명령어 처리")
        app.client.chat_postMessage(
            channel=channel,
            text=f"안녕하세요! <@{user}>님!"
        )
    elif text.lower() == "도움말":
        logger.info("도움말 명령어 처리")
        help_text = """
*사용 가능한 명령어:*
• 안녕 - 봇이 인사합니다
• 도움말 - 이 도움말 메시지를 표시합니다
• 시간 - 현재 시간을 알려줍니다
• 마지막메시지 - 현재 채널의 마지막 메시지를 보여줍니다
        """
        app.client.chat_postMessage(
            channel=channel,
            text=help_text
        )
    elif text.lower() == "시간":
        logger.info("시간 명령어 처리")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        app.client.chat_postMessage(
            channel=channel,
            text=f"현재 시간은 {current_time} 입니다."
        )
    elif text.lower() == "마지막메시지":
        logger.info("마지막메시지 명령어 처리")
        last_msg = get_last_message(channel)
        if last_msg:
            user_info = app.client.users_info(user=last_msg["user"])
            user_name = user_info["user"]["real_name"] if user_info["ok"] else f"<@{last_msg['user']}>"
            
            message_text = f"""
*마지막 메시지 정보:*
• 작성자: {user_name}
• 시간: {last_msg['timestamp']}
• 내용: {last_msg['text']}
"""
            if last_msg["thread_ts"]:
                message_text += "• 스레드 메시지입니다"
        else:
            message_text = "메시지를 가져올 수 없습니다."
            
        app.client.chat_postMessage(
            channel=channel,
            text=message_text
        )

@app.event("app_mention")
def handle_mentions(body, logger):
    """
    봇 멘션을 처리하는 함수입니다.
    """
    logger.info(f"멘션 이벤트 수신: {json.dumps(body, indent=2)}")
    
    event = body["event"]
    text = event.get("text", "")
    channel = event.get("channel")
    user = event.get("user")
    
    logger.info(f"멘션 처리: 채널={channel}, 사용자={user}, 내용={text}")
    
    app.client.chat_postMessage(
        channel=channel,
        text=f"<@{user}>님, 제가 멘션되었네요! 어떤 도움이 필요하신가요?"
    )

def handle_slack_request(request):
    """
    Slack 요청을 처리하는 공통 함수입니다.
    """
    logger.info(f"요청 수신: {request.method} {request.path}")
    logger.info(f"요청 헤더: {dict(request.headers)}")
    logger.info(f"요청 본문: {request.get_data(as_text=True)}")
    
    # URL 검증 요청 처리
    if request.json and "challenge" in request.json:
        logger.info("URL 검증 요청 처리")
        return jsonify({"challenge": request.json["challenge"]})
    
    # 일반 이벤트 처리
    logger.info("일반 이벤트 처리")
    return handler.handle(request)

@flask_app.route("/", methods=["POST"])
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """
    Slack 이벤트를 처리하는 엔드포인트입니다.
    """
    return handle_slack_request(request)

if __name__ == "__main__":
    logger.info("Slack 봇 서버 시작")
    flask_app.run(port=3000) 