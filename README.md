# first
최초 flask app 소스관리
배포 관련 사항
deploy.json : 도메인,아이피등 정보
            형식이 json이라서 주석불가
fabfile.py : 페브릭 작업내용 기술
fabfile_comment.py: 주석버전
wsgi.py : 엔트리 파일, 서버구동시 시작점
requirements.txt : 서버구동시 필요한 모듈을 기술(버전 포함)

#서버로그확인
접속로그
>tail -f /var/log/apache2/access.log
> ctrl + c  (나올때)
에러로그 500에러 발생시, internal server error
>tail -f /var/log/apache2/error.log
> ctrl + c  (나올때)