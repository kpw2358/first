'''
로컬 개발 pc에서 원격 서버의 환경부터 ~운용까지 모든 세팅을 진행한다
'''
from fabric.contrib.files import append, exists, sed, put
from fabric.api import local, run, sudo, env
import os
import json


#프로젝트 디렉토리

#print (__file__)
#print (os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
#print (os.path.dirname(os.path.abspath(__file__)))
print (PROJECT_DIR)
# C:\Users\Student\Downlaods\py_projects\first

#2.환경변수 로드
# json.load() json파일을 읽어서 그 구조를 유지하여 리턴ls
envs = json.load( open( os.path.join(PROJECT_DIR,'deploy.json') ) )
#자체로 경로가 만들어지고 경로가 오픈되고 오픈된 그걸로 제이슨파일로 갖고온다
print(envs)
'''
{
    "REPO_URL":"https://github.com/kpw2358/first",
    "PROJECT_NAME":"first",
    "REMOTE_HOST":"ec2-13-209-43-192.ap-northeast-2.compute.amazonaws.com",
    "REMOTE_HOST_SSH":"13.209.43.192",
    "REMOTE_USER" : "ubuntu"
}
'''
#3.로드한 환경변수를 상수(변하지않는)의미로 설정
REPO_URL            =envs['REPO_URL']
PROJECT_NAME       =envs['PROJECT_NAME']
REMOTE_HOST        =envs['REMOTE_HOST']
REMOTE_HOST_SSH    =envs['REMOTE_HOST_SSH']
REMOTE_USER        =envs['REMOTE_USER']

#4.fabic의 환경변수 env에 필요한 부분추가  hosts라고 했으니까 리스트형식인 []를 사용
env.user = REMOTE_USER
env.hosts = [
    REMOTE_HOST_SSH,
]
#4-1. pem파일로 로그인을 하기위해
env.user_ssh_config = True
env.key_filename = 'project.pem' #동일폴더 위치시키기

#5. 원격지에 세팅될 디렉토리 지정  중괄호는 .format
# /home/ubuntu/first
project_folder = '/home/{}/{}'.format(env.user,PROJECT_NAME)
print (project_folder)

# 6.리눅스에 설치될 기본 패키지 목록
apt_requirements = [
    'curl',
    'git',
    'python3-pip',
    'python3-dev',
    'build-essential',
    'apache2',
    'libapache2-mod-wsgi-py3',
    'python3-setuptools',
    'libssl-dev',
    'libffi-dev'
]
    #패브릭 구동시  fab 함수명
    #이중에서 _함수명은  구동불가
'''
작성이 모두 끝난후
>fab new_initServer
소스가 변경된후
>fab update
'''

# 7. 기본 신규 서버 세팅함수
def new_initServer():
    _setup()
    update()
#7-1.리눅스 셋업
def _setup():
    # 리눅스 패키지 업데이트 주소 or 패키지 목록 세팅
    _init_apt()
    # 필요한 패키지 설치
    _install_apt_packages()
    # 가상환경 구축


# 7-2.. apt (우분트상) 패키지를 업데이트 여부 확인 및 업데이트
def _init_apt():
    yn = input('would you want ubuntu linux update? : [y/n]')
    if yn == 'y':#사용자가 업데이트를 원했다면
        #sudo => root 권한으로 실행할때
        #sudo apt-get update
        #sudo apt-get upgrade
        sudo('apt-get update && -y upgrade')
#7-3. 리눅스 상에 필요한 패키지 설치  리콰이어먼트보면 for문을 떠올려야해!!목록을 하나씩 꺼내쓰겟네?
def _install_apt_packages(requires) :
    #설치할 패키지 목록 나열
    reqs = ''
    for req in requires :
        reqs += '' + req
        # reqs => curl git python3-pip ....
    # 수행
    # sudo apt-get install curl
    sudo ('apt-get -y install ' + reqs)

#7-4. 가상환경 구축
def _making_virtualenv():
    #설치여부확인 => 파일 여부 체크
    if not exists('~/.virtualenvs'):

        #가상환경 폴더
        
        # run 구동 => ubuntu 소유(퍼미션)
        # sudo 구동 => root 소유(퍼미션)
        run ( 'mkdir ~/.virtualenvs' )
        #패키지 설치
        sudo ('pip3 install virtualenv virtualenvwrapper')
        # 환경변수 반영 및 쉘(윈도우의배치) 구동 가상환경 구축
        cmd = '''
            "#python virtualenv global setting
            export WORKON_HOME=~/.virtualenvs
            #python location
            export VIRTUALENVWRAPPER_PYTHON="$(command \which python3)"
            # shell 실행
            source /user/local/bin/virtualenvwrapper.sh"
        '''
        run('echo {} >> ~/.bashrc'.format(cmd) )

#8.소스 수정후 서버에 반영할때 사용하는 함수
def update():
    #8-1 소스를 최신으로 github를 통해서 받는다
    _git_update()
    #8-2 가상환경  필요한 패키지 설치 (1회만 수행)
    _virtualenv_update()
    #8-3 아파치에 가상호스트 세팅 (1회만 수행)
    _virtualhost_make()
    #8-4 아파치가 프로젝트를 access할수있게 권한 처리를 하는 부분 (1회만수행)
    #신규파일에 대한 검토 필요 -> 그냥 매번 수행
    _grant_apache()
    #8-5 서버재가동(아파치)
    _restart_apache()


#가상환경 구축
        #목표 : 운영체계에는 가장 기본만 파이썬만 설치
        #프로젝트 별로 : 필요한 패키지를 설치하여 상호 프로젝트간 영향을 받지않게 만드는 방식(가상환경)
        #pip install virtualenv
        #가상환경 위치로 이동
        #virtualenv env
        # cd env/Scripts
        # activate or . activate =>프롬프트가 새로 열림
        # (env)>pip list
        # (env)>pip install flask
        # 구동
        # c:\~\py_project\env\Scripts\python run.py
        #개발 당시 버전을 기억하고 새로운 프로젝트들 이요할때 충돌발생이 되니까 가상환경 구축을 잘해놔라. 개발도 가상환경에서 운영도 가상환경에서.
#8-1 저장소에서 최신 소스로 반영
def _git_update():
    if exists(project_folder + '/.git'): # 깃트가 존재하면 first폴더로 이동 그리고 저장소로부터 fetch를 해서 최신정보 가져온다
        run('cd %s && git fetch' % (project_folder,))
    else: # 깃트가 존재하지 않으면 저장소로부터 최초로 프로젝트로 받아온다
        run('git clone %s %s' % (REPO_URL, project_folder))
    # 기트의 커밋된 로그를 최신으로 한개 가져온다 그것의 번호를 리턴
    # local : git log -n 1 --format=%H => 232655112331 랜덤숫자
    current_commit = local("git log -n 1 --format=%H", capture=True)
    #first 폴더로 이동 그리고 git reset --hard 232655112331
    #최신 커밋사항으로 소스 반영   중간필요없이 최신 커밋사항으로 소스를 반영하는거임. 최신이 중요!
    run('cd %s && git reset --hard %s' % (project_folder, current_commit))
    #run('cd %s && git reset --hard' % (project_folder, ))

#8-2 본 프로젝트에 해당되는 가상환경 구축, 그 환경에 그 프로젝트에서 사용하는 모듈 설치
def _virtualenv_update():
    # /home/ubuntu/.virtualenvs/first 라는 가상환경
    virtualenv_folder = project_folder + '/../.virtualenvs/{}'.format(PROJECT_NAME)
    # /home/ubuntu/.virtualenvs/first/bin/pip 가 존재하지 않으면
    if not exists(virtualenv_folder + '/bin/pip'):
        #/home/ubuntu/.virtualenvs로 이동하고 그리고
        # virtualenv firest 가상환경 하나 생성
        run('cd /home/%s/.virtualenvs && virtualenv %s' % (env.user, PROJECT_NAME))

    #상관없이 수행
    #/home/ubuntu/.virtualenvs/first/bin/pip install -r
    run('%s/bin/pip install -r %s/requirements.txt' % (
        virtualenv_folder, project_folder
    ))

# 여기서는 생략
def _ufw_allow():
    #ufw에서 80포트를 오픈
    sudo("ufw allow 'Apache Full'")
    #리로드
    sudo("ufw reload")

#8-3 아파치 서버와 flask로 구성된 파이썬 서버간의 연동파트 (핵심)
def _virtualhost_make():
    script = """'<VirtualHost *:80>
    ServerName {servername}
    <Directory /home/{username}/{project_name}>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>
    WSGIDaemonProcess {project_name} python-home=/home/{username}/.virtualenvs/{project_name} python-path=/home/{username}/{project_name}
    WSGIProcessGroup {project_name}
    WSGIScriptAlias / /home/{username}/{project_name}/wsgi.py
    
    ErrorLog ${{APACHE_LOG_DIR}}/error.log
    CustomLog ${{APACHE_LOG_DIR}}/access.log combined
    
    </VirtualHost>'""".format(
        username=REMOTE_USER,
        project_name=PROJECT_NAME,
        servername=REMOTE_HOST,
    )
    # 아파치 사이트 목록 설정파일에 first.conf 파일을 하나 생성해서 둔다
    sudo('echo {} > /etc/apache2/sites-available/{}.conf'.format(script, PROJECT_NAME))
    sudo('a2ensite {}.conf'.format(PROJECT_NAME))
#8-4 아파치 서버가 웹을 엑세스 할 수 있게 처리
def _grant_apache():
    #파일의 소유주나 소유그룹을 변경하기 위한 리눅스 명령어
    #아파치쪽 웹의 소유주와 프로젝트 소유주를 일치시킴
    sudo('chown -R :www-data ~/{}'.format(PROJECT_NAME))
    #프로젝트 폴더의 권한을 775로 변경
    #권한(쓰기w,읽기r,실행x)
    # 775는 루트,소유주는 다 사용가능, 누구나 경우는 읽기만 가능
    sudo('chmod -R 775 ~/{}'.format(PROJECT_NAME))
#8-5 아파치 서버 재가동
def _restart_apache():