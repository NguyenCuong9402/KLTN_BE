pipeline {
    agent any

    stages {
        stage('Build and Deploy') {
            steps {
                sh 'sudo docker-compose -f docker-compose.yml --env-file ./config/.build.prd up --build -d'
            }
        }

        stage('Remove unused images') {
            steps {
                sh 'sudo docker image prune -a -f'
            }
        }
    }
}