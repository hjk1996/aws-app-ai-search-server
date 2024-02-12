pipeline {
    agent any

    environment {

        ECR_URL = "109412806537.dkr.ecr.us-east-1.amazonaws.com/app-face-search"
    }


    stages {
        stage('Checkout') {
            steps {
                // GitHub에서 최신 코드를 체크아웃
                checkout scm
            }

            post {
                success {
                    echo "Success Checkout!"
                }
                failure {
                    echo "Failure Checkout!"
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                // Docker 이미지 빌드
                sh "docker build -t ${ECR_URL}:${currentBuild.number} ."
                sh "docker tag ${ECR_URL}:${currentBuild.number} ${ECR_URL}:latest"
            }

            post {
                success {
                    echo "Success Docker Image Build!"
                }
                failure {
                    echo "Failure Docker Image Build!"
                }
            }
        }
        stage('Push to ECR') {
            steps {
                // ECR에 로그인
                sh 'aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${ECR_URL}'
                // 이미지 푸시
                sh "docker push ${ECR_URL}:${currentBuild.number}"
                sh "docker push ${ECR_URL}:latest"
            }

            post {

                always {
                    sh "docker image rm ${ECR_URL}:${currentBuild.number}"
                }

                success {
                    echo "Success Push to ECR"
                }
                failure {
                    echo "Failure Push to ECR"
                }
            }
        }
    }
}
