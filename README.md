# official XCube Server workload

이 디렉터리는 자체 제작 Spring 서버가 아니라 공식 xcube Server 실행환경을 위한
workload 경계입니다.

- 포트: `8080`
- 실행 명령: `xcube serve -v -c /etc/xcube/config.yml`
- health: `GET /`
- 설정: 사용자별 `config.yml`을 image에 포함하지 않고 ConfigMap/전용 설정 저장소로 주입
- 배포 단위: Data Uploading/Generation/Analysis/AI와 분리된 Docker image 및 Kubernetes workload
- 현재 상태: 로컬 명령 실행만 검증되었고 image/Deployment/Service는 미구현

사용자별 Pod 전략은 기본 프로젝트·공유·전역 Zarr 기능 완료 후 확정합니다.

Phase 1의 결정적 YAML 생성기는 [config_renderer](config_renderer/README.md)에 있다.
원본 XEE `config.yml`을 읽거나 수정하지 않고 DB/domain projection만 입력으로 받는다.
