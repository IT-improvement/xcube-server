# xcube-server

공식 xcube Server 실행·배포 경계(`8080`). 자체 서버가 아니며 dataset·tile·timeseries·style API를 제공한다. M2부터 Claude가 직접 작업한다(2026-10-02 사용자 지시).

- 로컬 설정: `/Users/jooseungjae/XEE/config.yml` — 수정 금지. test 계정(ID 4) 개인 Pod의 기본 config로 읽어서 등록하는 것만 허용(2026-10-02)
- 개인 Pod image: [docker/Dockerfile](./docker/Dockerfile) (`xcube-local/xcube:1.13.1`, 로컬 xcube와 같은 버전, Apple Silicon native)
- 사용자별 config 생성기: [config_renderer](./config_renderer/README.md)
- 운영 방식: 사용자별 개인 Pod + 메인(replica 2) + 새벽 병합. 공유 시 개인 Pod를 재시작하지 않는다. ([PRD §7.6](../docs/PM/PRD.md), [CI/CD](../docs/CI-CD/technical-guide.md))
- 현재 상태: 로컬 실행만 검증, image·Deployment 미구현. 배포 기준은 [CI/CD](../docs/CI-CD/CLAUDE.md)
