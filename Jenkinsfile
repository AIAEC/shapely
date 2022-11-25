pipeline {

  options {
    ansiColor('xterm')
    buildDiscarder(logRotator(numToKeepStr: '13'))
  }

  agent {
    kubernetes {
      yamlFile '.jenkins/builder.yaml'
    }
  }

  environment {
    PYPI = credentials('pypi-repo-credential')
  }

  stages {
    stage('testing') {
      steps {
        container('python') {
          // copy shapely's geos library to shapely repository in order to use it during test
          sh 'cp -r /usr/local/lib/python3.10/site-packages/Shapely.libs shapely/.libs'
          sh 'pip install -r requirements-dev.txt'
          sh 'pytest'
        }
      }
    }

    stage('build package') {
      steps {
        container('builder') {
          sh './build-customized-wheel.sh'
        }
      }
    }

    stage('uploading pypi package') {
      steps {
        container('python') {
          sh 'pip install twine'
          sh 'twine upload --repository-url https://pypi.aiacesz.com -u $PYPI_USR -p $PYPI_PSW dist/*'
        }
      }
    }
  }
}
