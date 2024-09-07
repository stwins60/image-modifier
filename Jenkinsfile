pipeline {
    agent any

    environment {
        IMAGE_NAME = "idrisniyi94/image-modifier:v.0.0-${env.BUILD_NUMBER}-lite"
        DOCKERHUB_CREDENTIALS = credentials('f81abbea-2b04-4323-9b98-5964dfd2af75')
        SLACK_CHANNEL = "#jenkins"
    }

    stages {
        stage("Clean Workspace") {
            steps {
                cleanWs()
            }
        }
        stage("Git Checkout") {
            steps {
                checkout scmGit(branches: [[name: '*/master']], extensions: [], userRemoteConfigs: [[url: 'https://github.com/stwins60/guessGame.git']])
            }
        }
        stage("Install Dependencies") {
            steps {
                script {
                    sh "python3 -m venv venv"
                    sh ". venv/bin/activate"
                    sh "python3 -m pip install -r requirements.txt --no-cache-dir --break-system-packages"
                }
            }
        }
        stage("Trivy File Scan") {
            steps {
                script {
                    dir('./venv'){
                        def result = sh(script: "trivy filesystem --exit-code 1 --severity CRITICAL,HIGH .", returnStatus: true)

                        if (result != 0) {
                            def trivy_output = sh(script: "trivy filesystem --exit-code 1 --severity CRITICAL,HIGH .", returnStatus: true)
                            slackSend channel: "$SLACK_CHANNEL", message: "Trivy found vulnerabilities in the site packages: \n${trivy_output}"
                        } else {
                            slackSend channel: "$SLACK_CHANNEL", message: "Trivy passed with no vulnerabilities."
                        }
                    }
                    
                }
            }
        }
        stage("Docker Login") {
            steps {
                script {
                    sh "echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin"
                }
            }
        }
        stage("Build Docker Image") {
            steps {
                script {
                    sh "docker build -t $IMAGE_NAME ."
                }
            }
        }
        stage("Docker Scout") {
            steps {
                script {
                    sh "curl -fsSL https://raw.githubusercontent.com/docker/scout-cli/main/install.sh -o install-scout.sh"
                    sh "chmod +x install-scout.sh"
                    sh "./install-scout.sh"

                    def scanOutput = sh(script: "docker scout cves $IMAGE_NAME --exit-code --only-severity critical,high", returnStatus: true)
                    def result = sh(script: "docker scout cves $IMAGE_NAME --exit-code --only-severity critical,high", returnStatus: true)

                    if (result != 0){
                        
                        slackSend(channel: "$SLACK_CHANNEL", message: "Docker Scout found vulnerabilities:\n${scanOutput}")
                    } else {
                        slackSend(channel: "$SLACK_CHANNEL", message: "Docker Scout scan passed with no vulnerabilities.")
                    }
                }
            }
        }
        stage("Push to DockerHub") {
            steps {
                script {
                    sh "docker push $IMAGE_NAME"
                }
            }
        }
        stage("Deploy to K8S") {
            steps {
                script {
                    dir('./k8s') {
                        withKubeCredentials(kubectlCredentials: [[caCertificate: '', clusterName: '', contextName: '', credentialsId: '88a9f11c-11e5-4bdb-b3bd-f63dba417648', namespace: '', serverUrl: '']]) {
                            sh "sed -i 's|IMAGE_NAME|$IMAGE_NAME|g' deploy.yaml"
                            sh "kubectl apply -f ."
                            echo "Deployed.. Check the namespace"
                        }
                    }
                }
            }
        }
    }
}