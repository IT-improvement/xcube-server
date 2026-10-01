# xcube-server

공식 xcube Server 실행·배포 경계(`8080`). 자체 서버가 아니며 dataset·tile·timeseries·style API를 제공한다. Claude는 이 폴더를 수정하지 않는다.

- 로컬 설정: `/Users/jooseungjae/XEE/config.yml` (읽거나 수정하지 않는다)
- 사용자별 config 생성기: [config_renderer](./config_renderer/README.md)
- 운영 방식: 사용자별 개인 Pod + 메인(replica 2) + 새벽 병합. 공유 시 개인 Pod를 재시작하지 않는다. ([PRD §7.6](../docs/PM/PRD.md), [CI/CD](../docs/CI-CD/technical-guide.md))
- 현재 상태: 로컬 실행만 검증, image·Deployment 미구현. 배포 기준은 [CI/CD](../docs/CI-CD/CLAUDE.md)
