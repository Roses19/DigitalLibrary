pipeline {
    agent any

    environment {
        VENV_DIR = ".venv"
    }

    stages {

        stage('Clone Code') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/your-username/your-repo.git'
            }
        }

        stage('Create Virtual Environment') {
            steps {
                bat """
                py -m venv %VENV_DIR%
                """
            }
        }

        stage('Install Dependencies') {
            steps {
                bat """
                call %VENV_DIR%\\Scripts\\activate
                python -m pip install --upgrade pip
                pip install -r requirements.txt
                """
            }
        }

        stage('Run Tests') {
            steps {
                bat """
                call %VENV_DIR%\\Scripts\\activate
                python -m unittest discover -s DigitalLibrary/tests -p "test_*.py" -v
                """
            }
        }
    }

    post {
        success {
            echo 'Test passed '
        }
        failure {
            echo 'Test failed'
        }
    }
}
