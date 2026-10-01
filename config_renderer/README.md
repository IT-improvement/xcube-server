# Config Renderer

DB/domain projection을 공식 XCube Server가 읽는 `Datasets`와 `Styles` YAML로
결정적으로 변환하는 Phase 1 최소 모듈이다.

지원 범위:

- canonical dataset/style Identifier
- band별 `ColorBar`와 `ValueRange`
- 선택적 RGB 3채널 mapping
- 입력 순서와 무관한 정렬과 SHA-256
- runtime에서 전달한 허용 ColorBar 외 값 거부
- 변수 존재, 중복, 숫자 범위 검증

기존 config 파일을 병합하거나 수정하지 않는다. `/Users/jooseungjae/XEE/config.yml`은
reference일 뿐 이 모듈의 입출력이 아니다.

테스트:

```bash
cd xcube-server
python3 -m unittest discover -s tests -v
```
