pipeline {
    agent any

    environment {
        IMAGE_NAME = "idrisniyi94/image-modifier:v.0.0-${env.BUILD_NUMBER}-lite"
        DOCKERHUB_CREDENTIALS = credentials('f81abbea-2b04-4323-9b98-5964dfd2af75')
        SLACK_CHANNEL = "#jenkins"
        SENTRY_AUTH_TOKEN = credentials('d2667a6a-f631-4339-aa43-f46ff77f3753')
        SENTRY_ORG = "sentry"
        SENTRY_PROJECT = "image-modifier"
    }

    stages {
        stage("Clean Workspace") {
            steps {
                cleanWs()
            }
        }
        stage("Git Checkout") {
            steps {
                checkout scmGit(branches: [[name: '*/master']], extensions: [], userRemoteConfigs: [[url: 'https://github.com/stwins60/image-modifier.git']])
            }
        }
        stage("Install Dependencies") {
            steps {
                script {
                    sh """
                    python3 -m venv venv
                    . venv/bin/activate
                    python3 -m pip install -r requirements.txt --no-cache-dir --break-system-packages
                    """
                }
            }
        }
        stage("Trivy File Scan") {
            steps {
                script {
                    dir('./venv') {
                        def result = sh(script: "trivy filesystem --exit-code 1 --severity CRITICAL,HIGH .", returnStatus: true)
                        if (result != 0) {
                            slackSend channel: "$SLACK_CHANNEL", message: "Trivy found vulnerabilities in the site packages."
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
                    sh """
                    curl -fsSL https://raw.githubusercontent.com/docker/scout-cli/main/install.sh -o install-scout.sh
                    chmod +x install-scout.sh
                    ./install-scout.sh
                    """
                    def scanOutput = sh(script: "docker scout cves $IMAGE_NAME --only-severity critical,high", returnStdout: true).trim()
                    def result = sh(script: "docker scout cves $IMAGE_NAME --only-severity critical,high --exit-code", returnStatus: true)

                    if (result != 0) {
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
                        withKubeConfig([credentialsId: '88a9f11c-11e5-4bdb-b3bd-f63dba417648']) {
                            sh "sed -i 's|IMAGE_NAME|$IMAGE_NAME|g' deploy.yaml"
                            sh "kubectl apply -f ."
                            echo "Deployed.. Check the namespace"
                        }
                    }
                }
            }
        }
        stage("Release to Sentry") {
            steps {
                script {
                    sh """
                    VERSION=\$(sentry-cli releases propose-version)
                    sentry-cli releases new \$VERSION
                    sentry-cli releases set-commits \$VERSION --auto
                    sentry-cli releases finalize \$VERSION
                    """
                }
            }
        }
    }
}
