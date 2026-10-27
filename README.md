# AI 법률 지형도

나라별(미국·유럽·중국·일본·한국·그 외) AI 소송·입법·규제를 정리하는 정적 블로그입니다. GitHub Pages가 `docs/` 폴더를 게시합니다.

## 구조

- `data/posts/<id>.json` — 글 하나에 파일 하나
- `data/regions.json` — 나라별 개요
- `assets/style.css` — 디자인
- `scripts/build.py` — `data/`를 읽어 `docs/`에 사이트를 만듭니다
- `docs/` — 빌드 결과(직접 고치지 마세요)

## 글 추가·수정

1. `data/posts/`에 JSON 파일을 추가하거나 고칩니다. 파일 이름과 `id`가 같아야 합니다(소문자, 숫자, 하이픈).
2. `python3 scripts/build.py`를 실행합니다.
3. `data/`와 `docs/`를 함께 커밋하고 푸시합니다.

글 필드:

| 필드 | 내용 |
| --- | --- |
| `id` | 파일 이름과 같은 값, 예: `kr-voice-injunction` |
| `region` | `us`, `eu`, `cn`, `jp`, `kr`, `other` |
| `type` | `소송·판결`, `입법·규제`, `집행·조사`, `정책·지침` |
| `status` | `진행 중`, `결정·판결`, `제정·시행`, `발표`, `계류` |
| `date` | `YYYY-MM-DD`, `YYYY-MM` 또는 `YYYY` |
| `title`, `forum`, `summary` | 제목, 법원·기관·사건번호, 목록에 보이는 요약 |
| `body` | 한 줄에 한 문장(번호는 자동), 빈 줄로 문단 구분 |
| `sources` | `[{"label": "...", "url": "https://..."}]` |
| `updatedAt` | ISO 시각 |

## GitHub Pages 설정

Settings → Pages → Build and deployment에서 Source를 "Deploy from a branch", Branch를 `main` / `/docs`로 지정합니다.
