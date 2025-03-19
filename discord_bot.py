import discord
from dotenv import load_dotenv
import os
import ssl
import certifi
import openai
from collections import defaultdict

# SSL 컨텍스트 설정
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# 환경 변수 로드
load_dotenv(override=True)
print("[디버그] .env 파일 로드됨")

# OpenAI API 설정
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    print("[디버그] 오류: OPENAI_API_KEY가 설정되지 않았습니다.")
    raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
print(f"[디버그] OpenAI API 키 확인됨: {openai_api_key[:10]}...")
openai.api_key = openai_api_key

# 봇 설정
intents = discord.Intents.all()  # 모든 인텐트 활성화
bot = discord.Client(intents=intents)

# 채널별 메시지 히스토리 저장소
channel_history = defaultdict(list)
channel_members = defaultdict(list)

async def load_channel_history(channel):
    """채널의 메시지 히스토리를 로드하는 함수"""
    print(f"[디버그] 채널 {channel.name}의 메시지 히스토리 로드 중...")
    messages = []
    total_tokens = 0
    max_tokens = 8000  # TPM 제한을 고려하여 토큰 수 제한
    
    async for msg in channel.history(limit=None):  # 모든 메시지 가져오기
        if msg.author != bot.user:  # 봇의 메시지는 제외
            message_text = f"{msg.author.name}: {msg.content}"
            # 대략적인 토큰 수 추정 (영어 기준 1단어 = 1.3토큰)
            estimated_tokens = len(message_text.split()) * 1.3
            
            # 토큰 제한을 초과하지 않는 경우에만 메시지 추가
            if total_tokens + estimated_tokens <= max_tokens:
                messages.append(message_text)
                total_tokens += estimated_tokens
            else:
                break
    
    messages.reverse()  # 시간 순서대로 정렬
    channel_history[channel.id] = messages
    print(f"[디버그] 채널 {channel.name}에서 {len(messages)}개의 메시지 로드 완료 (예상 토큰 수: {total_tokens:.1f})")

async def update_channel_members(channel):
    """채널의 멤버 정보를 업데이트하는 함수"""
    members = channel.members
    member_info = []
    for member in members:
        if not member.bot:  # 봇 제외
            member_info.append(f"- {member.name} (상태: {member.status})")
    channel_members[channel.id] = member_info
    print(f"[디버그] 채널 {channel.name}의 멤버 정보 업데이트 완료")

@bot.event
async def on_ready():
    """봇이 준비되었을 때 실행되는 이벤트"""
    print(f'[디버그] {bot.user}이(가) 디스코드에 연결되었습니다!')
    print(f'[디버그] 봇 ID: {bot.user.id}')
    print(f'[디버그] 봇이 있는 서버 목록:')
    
    # 모든 서버의 모든 채널에서 메시지 히스토리 로드
    for guild in bot.guilds:
        print(f'  - {guild.name} (ID: {guild.id})')
        # 서버의 권한 확인
        bot_member = guild.get_member(bot.user.id)
        if bot_member:
            print(f'    권한: {[perm for perm, value in bot_member.guild_permissions if value]}')
            
        # 각 채널의 메시지 히스토리 로드
        for channel in guild.text_channels:
            await load_channel_history(channel)
            await update_channel_members(channel)
    print('------')

@bot.event
async def on_message(message):
    """메시지가 수신될 때마다 실행되는 이벤트"""
    try:
        print(f'[디버그] 메시지 수신: {message.author} - {message.content}')
        print(f'[디버그] 채널: {message.channel.name}')
        print(f'[디버그] 서버: {message.guild.name if message.guild else "DM"}')
        print(f'[디버그] 멘션된 사용자: {message.mentions}')
        print(f'[디버그] 봇이 멘션됨: {bot.user in message.mentions}')
        
        # 봇이 자신의 메시지를 무시하도록 설정
        if message.author == bot.user:
            print('[디버그] 봇 자신의 메시지 무시')
            return
        
        # 멘션을 제거하고 내용만 추출
        content = message.content
        if bot.user in message.mentions:
            content = content.replace(f'<@{bot.user.id}>', '').strip()
            print(f'[디버그] 멘션 제거 후 내용: {content}')
            
            # 멘션된 경우 OpenAI API 호출
            try:
                print("[디버그] OpenAI API 호출 시도...")
                print("[디버그] GPT-4 모델 사용 중...")
                
                # 채널의 멤버 정보와 메시지 히스토리 가져오기
                member_info = channel_members.get(message.channel.id, [])
                message_history = channel_history.get(message.channel.id, [])
                
                # 시스템 메시지 구성
                system_message = f"""당신은 MCP(Minecraft Control Protocol)입니다. 

현재 채널의 멤버 목록은 다음과 같습니다:
{chr(10).join(member_info)}

최근 대화 내용은 다음과 같습니다 (최신순):
{chr(10).join(message_history)}

사용자의 질문에 명확하고 정확하게 답변해주세요. 멤버에 대한 질문이 있다면 위 목록을 참고하여 답변해주세요.
이전 대화 내용을 참고하여 맥락을 이해하고 답변해주세요.
MCP로서 친절하고 도움이 되는 AI 어시스턴트로 활동해주세요."""
                
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": content}
                    ],
                    max_tokens=500,  # 응답 토큰 수도 줄임
                    temperature=0.7
                )
                
                answer = response.choices[0].message.content
                print(f'[디버그] 생성된 응답: {answer}')
                await message.channel.send(answer)
                
            except Exception as e:
                print(f'[디버그] OpenAI API 호출 중 오류 발생: {str(e)}')
                print(f'[디버그] 오류 타입: {type(e).__name__}')
                import traceback
                print(f'[디버그] 상세 오류: {traceback.format_exc()}')
                await message.channel.send("죄송합니다. 응답을 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
            return
                
    except Exception as e:
        print(f'[디버그] 메시지 처리 중 오류 발생: {str(e)}')
        import traceback
        print(traceback.format_exc())

@bot.event
async def on_error(event, *args, **kwargs):
    """에러 발생 시 실행되는 이벤트"""
    print(f'[디버그] 에러 발생: {event}')
    print(f'[디버그] 에러 상세: {args}')
    print(f'[디버그] 에러 추가 정보: {kwargs}')

def main():
    """메인 실행 함수"""
    print("[디버그] 봇 시작 중...")
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("[디버그] 오류: Discord 토큰이 설정되지 않았습니다.")
        raise ValueError("Discord 토큰이 설정되지 않았습니다. .env 파일을 확인해주세요.")
    
    print("[디버그] 토큰 확인됨, 봇 실행 시도 중...")
    try:
        bot.run(token)
    except Exception as e:
        print(f"[디버그] 봇 실행 중 오류 발생: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[디버그] 프로그램 실행 중 오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc()) 