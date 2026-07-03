# MetaBridge DNA

## 소개

metabridge_dna는 Epic Games MetaHuman의 **DNA 파일**(`.dna`)을 Blender로 가져오고 내보내는 애드온입니다.

- MetaHuman DNA 파일을 Blender로 **가져오기/내보내기** (DNA / FBX / glTF)
- 헤드와 바디를 분리해서 관리하고, 하나의 캐릭터로 **조립**
- 표정을 조작할 수 있는 **페이스 리그 보드** 제공 (컨트롤로 실시간 표정 확인)
- **Rigify 연동**으로 바디에 FK/IK 컨트롤 리그를 자동 생성해 애니메이션 가능한 리그로 확장
- 여러 캐릭터를 슬롯 단위로 관리하며, 저장/불러오기 후에도 상태가 자동 복원됨

애드온은 3D 뷰포트 사이드바(`N` 패널) → **MetaBridge DNA** 탭 하나에 모두 모여 있습니다. (캐릭터 조립 기능이 메인 패널 맨 위 섹션으로 통합되어 있습니다.)

---

## MetaBridge DNA 패널 구성

패널 상단부터 순서대로:

### 1. MetaHuman Assembler (캐릭터 불러오기 — 최상단 섹션)

| 메뉴 | 설명 |
|---|---|
| **MetaHumans Directory** | MetaHuman 캐릭터들이 들어있는 상위 폴더 경로를 지정합니다. 옆의 새로고침 버튼으로 폴더를 다시 스캔합니다. |
| **캐릭터 썸네일 목록** | 스캔된 캐릭터를 아이콘 형태로 선택합니다. 선택 시 아래에 이름/경로/Head·Body·Textures 보유 여부가 표시됩니다. |
| **Head / Body / Textures 토글** | 불러올 때 헤드, 바디, 텍스처 중 무엇을 포함할지 선택합니다. |
| **LOD 슬라이더** | RigLogic 평가 및 메시 생성에 사용할 LOD를 지정합니다. (아래 LOD 항목 참고) |
| **Assemble / Re-Assemble** | 선택한 캐릭터를 씬에 실제로 불러와 조립합니다. 이미 조립된 슬롯이면 "다시 조립"으로 바뀝니다. |
| **New** | 현재 캐릭터를 새 슬롯으로 추가해, 씬에 여러 캐릭터를 동시에 둘 수 있습니다. |
| **Assembled Characters 목록** | 씬에 불러온 캐릭터들의 목록입니다. 각 항목에서: |
| ㄴ 라디오 버튼 | 조작 대상(활성 슬롯)을 전환합니다. 전환 시 위쪽 디렉터리/썸네일/LOD도 그 슬롯 기준으로 자동 동기화됩니다. |
| ㄴ **Rig ON/OFF** | 해당 캐릭터의 표정 리그(실시간 계산)를 켜고 끕니다. |
| ㄴ 휴지통 아이콘 | 해당 캐릭터를 씬에서 삭제합니다. |

> DNA 파일을 개별적으로 불러오는 Load 메뉴는 없습니다 — 캐릭터 폴더 단위로 Assemble 하는 방식이 유일한 로드 경로입니다. 헤드/바디 DNA를 저장(export)하는 기능은 아래 **Export** 섹션에 통합되어 있습니다.

### 2. Face Rig (표정 리그)
- **Append GUIArmature**: 표정 컨트롤용 GUI 아마추어(슬라이더 뼈대)를 씬에 추가합니다. 표정 조작의 핵심 컨트롤러입니다.
- **Face Rig: ON/OFF**: GUI 아마추어의 움직임을 실시간으로 DNA 블렌드셰이프/조인트에 반영할지 켜고 끕니다.
- **Dump DNA RC Names**: 로드된 DNA의 모든 컨트롤 채널 이름을 콘솔에 출력합니다. (디버깅용)
- **Generate Name Mapping**: DNA 채널과 GUI 뼈 이름 간의 매핑 JSON을 자동 생성합니다.
- **Full Diagnosis**: 리그 연결 상태를 콘솔에 상세 진단 출력합니다. 표정이 안 움직일 때 확인용입니다.

### 3. Rigify Body Control Rig (바디 애니메이션 리그)
Rigify 애드온이 활성화되어 있어야 사용 가능합니다. (`Edit > Preferences > Add-ons > Rigging: Rigify`)

1. **1. Build Meta-Rig**: 바디 스켈레톤에 맞춰 Rigify meta-rig(뼈대 초안)를 생성합니다. 생성 후 필요하면 본 위치를 수동으로 조정할 수 있습니다.
2. **2. Generate Rigify Rig**: meta-rig를 기반으로 실제 FK/IK 조작이 가능한 컨트롤 리그를 생성합니다.
3. **3. Apply Retarget**: 생성된 컨트롤 리그가 MetaHuman 바디를 실제로 움직이도록 연결합니다. (**주의**: meta-rig 위치가 잘못되면 메시가 깨질 수 있으니, 2단계 완료 후 리그가 올바르게 위치했는지 확인 후 적용하세요.)
   - **Remove Retarget**: 연결을 해제합니다.
4. **Link Head Rig** (Retarget 적용 후 표시): 헤드 리그를 바디 컨트롤 리그에 연결해 하나의 리그로 움직이게 합니다.
   - **Unlink Head Rig**: 연결을 해제합니다.
5. **Remove Rigify Rig**: 생성된 Rigify 관련 오브젝트/컨스트레인트를 모두 제거합니다.

### 4. DNA RC Inspector (채널-뼈 매핑 검사기)
DNA의 원본 컨트롤 채널과 GUI 뼈가 어떻게 연결되어 있는지 확인/수정하는 도구입니다.

- **View (DNA RC View / Bone View)**: DNA 채널 기준으로 볼지, GUI 뼈 기준으로 볼지 전환합니다.
- **검색창 / Show 필터(All·Mapped·Unmapped)**: 이름으로 검색하거나, 연결된 것만/안 된 것만 필터링합니다.
- **Per page**: 한 페이지에 표시할 항목 수를 조절합니다.
- **Re-Auto Link**: 이름 규칙 기반으로 채널-뼈를 자동 재연결합니다.
- **Clear All**: 수동으로 설정한 연결을 모두 초기화합니다.
- **Print Full Map**: 전체 매핑 내용을 콘솔에 출력합니다.
- 목록의 각 행: **Connect / Change Bone**(연결·변경), 톱니 아이콘(뼈 세부 설정 팝업), **X**(수동 연결 해제) 버튼으로 개별 채널을 관리합니다.

---

## 확장 기능 (서브 패널)

메인 패널 아래에 접혀 있는 서브 패널들입니다. 화살표를 눌러 펼칩니다.

### DNA Validation (DNA 검증) — `dna_validate.py`
- **Validate DNA File...**: `.dna` 파일을 검사해 손상/서명 오류/파싱 실패/RigLogic 초기화 실패를 구분해 알려주고, 조인트·메시·블렌드셰이프·LOD 개수를 콘솔에 출력합니다.
- **Validate Active Slot**: 활성 슬롯의 헤드/바디 DNA 파일을 한 번에 검증합니다.
- DNA 로드 실패 시 "Invalid DNA file" 대신 구체적인 원인 메시지가 표시됩니다.

### Pose Reset (포즈 초기화) — `reset_pose.py`
- **Reset All Controls**: 활성 슬롯의 얼굴 컨트롤을 모두 중립(무표정)으로 되돌립니다.
- **Reset Selected (Pose Mode)**: 포즈 모드에서 선택한 컨트롤 본만 초기화합니다.

### Expression Presets (표정 프리셋) — `pose_presets.py`
- **저장 형식/위치**: 프리셋은 JSON 파일이며 폴더에 프리셋당 1개 파일로 저장됩니다.
  형식: `{"bones": {"본이름": [x, y, z]}}` — 0이 아닌 컨트롤 위치만 기록되어 캐릭터 간 호환됩니다.
- **Save Current Expression**: 드롭다운에서 선택된 프리셋에 현재 표정을 바로 덮어씁니다. (확인 팝업 후 저장, 선택된 프리셋이 없으면 비활성)
- **Save As Current Expression...**: 파일 저장 창이 열려 새 파일명으로 저장합니다. 저장 위치가 그대로 보이며 기본 위치는 현재 프리셋 폴더입니다.
- 드롭다운에서 프리셋 선택 후 **Apply Preset**: 저장된 표정을 즉시 적용합니다. (기존 포즈는 초기화 후 적용)
- **Import...**: 다른 곳에 있는 프리셋 .json 파일을 골라 presets 폴더로 복사해 목록에 추가합니다. (형식 검증 포함)
- **Set Folder...**: 프리셋을 저장/나열할 폴더를 직접 선택합니다. 선택한 폴더는 config에 저장되어 재시작 후에도 유지되며, 애드온 기본 presets 폴더를 다시 선택하면 기본값으로 돌아갑니다. 현재 폴더는 패널 하단에 표시됩니다.
- **창 아이콘 버튼**: 현재 프리셋 폴더를 탐색기로 엽니다. 파일을 직접 넣어도 목록에 자동 반영됩니다.
- 휴지통 아이콘: 선택한 프리셋을 삭제합니다.

#### External Preset Converter (외부 프리셋 변환) — `preset_convert.py` (Expression Presets 하위 패널)
- **Convert & Import (Maya/Houdini)...**: 마야/후디니에서 저장한 JSON 프리셋을 본 이름을 변환해 가져옵니다.
  - 지원 입력 형식: `{"bones": {...}}`, `{"controls": {...}}`, 평면 딕셔너리 `{"이름": [x,y,z]}` 또는 `{"이름": 값}`(단일 값은 Y축으로 처리)
  - 자동 매칭 순서: ① 사용자 매핑 파일 → ② 정확히 일치 → ③ 대소문자 무시 → ④ 정규화 비교(네임스페이스 `rig:`/DAG 경로 `|` 제거, 특수문자 제거) → ⑤ 유일한 접미사/부분 일치
  - **Value Scale** 옵션: 소스 값 범위가 -1~1이면 0.01을 입력해 GUI 보드 이동량에 맞춥니다.
- **매칭 실패한 이름**: `name_mapping.json`에 `"소스이름": ""` 형태로 자동 기록됩니다. **Edit Name Mapping** 버튼으로 파일을 열어 대상 본 이름을 채운 뒤 다시 Import 하면 그 매핑이 최우선으로 적용됩니다.
- 변환 결과(매칭/실패 목록)는 콘솔에 상세 출력됩니다.
- **Convert ARKit Payload...**: ARKit 리맵 페이로드 JSON(`arkit52` 타깃/가중치 목록)을 읽어, ARKit 타깃(JawOpen, BrowDownLeft 등)마다 GUI 보드 포즈 프리셋을 하나씩 생성합니다.
  - `ctrl_expressions_jawopen` 같은 소스 이름을 gui_mapping.json의 `rc_names`로 역조회해 본+방향축으로 변환하고, 가중치를 보드 이동량(±0.01)으로 환산합니다.
  - **Min Weight**(기본 0.05) 미만의 미세 가중치는 제외됩니다. 생성/건너뜀/미매칭 상세는 콘솔에 출력됩니다.

### Animation Baker (애니메이션 베이킹) — `anim_baker.py`
- GUI 보드 본에 키프레임을 먼저 찍은 뒤 **Bake Face Animation**을 실행하면, 프레임 범위 전체를 평가해 헤드 리그 본과 셰이프키에 키프레임으로 굽습니다.
- 옵션: 프레임 범위/스텝, 본 굽기, 셰이프키 굽기, 베이크 후 Face Rig 자동 OFF(굽힌 키를 타이머가 덮어쓰지 않도록).
- **Clear Baked Animation**: 베이크된 액션을 제거합니다.

### Export (DNA / FBX / glTF) — `exporter.py`
DNA 저장과 FBX/glTF 내보내기가 하나의 패널에 통합되어 있습니다.

- **DNA (.dna)**: **Head / Body** 두 버튼만 있습니다 (Full 없음 — head.dna와 body.dna는 원래 별도 파일이라 하나로 합칠 수 없습니다). 각 버튼을 누르면 파일 저장 창이 열려 위치와 파일명을 직접 지정할 수 있고, Blender에서 편집한 정점 위치도 함께 저장됩니다.
- **FBX / glTF**: 포맷마다 **Full / Head / Body** 버튼으로 전체를 함께 내보내거나 헤드/바디만 따로 내보낼 수 있습니다. 파일 저장 창의 옵션에서 Head/Body 체크, GUI 보드 포함 여부(기본 제외), 애니메이션 포함 여부를 조절할 수 있습니다. 파일명에 `_Head`/`_Body`가 자동으로 붙습니다.

### Batch Tools (일괄 처리) — `batch_ops.py`
- **Assemble All Characters**: 스캔된 모든 캐릭터를 각각의 슬롯으로 한 번에 조립합니다. (이미 조립된 캐릭터 건너뛰기, 최대 개수 제한 옵션)
- **Export All Slots**: 조립된 모든 슬롯을 지정 폴더에 FBX/glTF로 일괄 내보냅니다.

---

## LOD (LOD 설정) — `lod_manager.py`
- **위치**: 메인 패널 최상단 MetaHuman Assembler 섹션의 Head/Body/Textures 토글 바로 아래 **LOD** 슬라이더.
- **로드 시 적용**: DNA를 Assemble 할 때 설정된 LOD의 **메시**가 생성되고 RigLogic도 같은 LOD로 초기화됩니다. 파일을 저장 후 다시 열어도 슬롯별 LOD가 자동 복원됩니다.
- **메시 변경**: 이미 조립된 캐릭터의 메시를 다른 LOD로 바꾸려면 LOD 값을 바꾼 뒤 **Re-Assemble**을 누르세요. 슬라이더 값과 현재 메시 LOD가 다르면 경고가 표시됩니다.
- **즉시 적용(계산만)**: 슬라이더 값을 바꾸면 활성 슬롯의 RigLogic 평가 LOD는 바로 전환됩니다. 슬롯을 전환하면 슬라이더가 해당 슬롯의 LOD로 동기화됩니다.
- LOD 0 = 최고 디테일, 숫자가 클수록 저폴리곤입니다.
