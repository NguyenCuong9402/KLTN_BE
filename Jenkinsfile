pipeline {
    agent any

    stages {


        stage('Build and Deploy') {
            steps {
                sh 'sudo docker-compose -f docker-compose.yml up --build -d'
            }
        }

        stage('Remove unused images') {
            steps {
                sh 'sudo docker image prune -a -f'
            }
        }
    }
}