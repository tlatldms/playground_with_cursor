# Discord MCP Bot

Discord 채널에서 작동하는 MCP(Model Context Protocol) 봇입니다. GPT-4를 활용하여 사용자의 질문에 답변하고 채널의 컨텍스트를 이해합니다.

## 기능

- 채널의 멤버 정보 제공
- 최근 대화 내용 기반의 컨텍스트 이해
- GPT-4를 활용한 자연스러운 대화
- 멘션 기반의 상호작용

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/tlatldms/playground_with_cursor.git
cd playground_with_cursor
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가하세요:
```
OPENAI_API_KEY=your_openai_api_key
DISCORD_TOKEN=your_discord_token
```

## 실행 방법

```bash
python discord_bot.py
```

## 주의사항

- `.env` 파일은 절대로 GitHub에 올리지 마세요.
- API 키와 토큰은 안전하게 보관하세요. 