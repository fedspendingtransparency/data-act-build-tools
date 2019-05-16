#!/usr/bin/env groovy

node('matviews') {
    def SLACK_CHANNEL = "#secret"

    try {
        properties([
            parameters([
                string(name: 'ELB',
                       defaultValue: 'servicedesk-dev',
                       description: 'The Load Balancer Name of the instance that needs a restart'),
            ])
        ])

        // Slack Notification Library
        library identifier: 'broker@master', retriever: modernSCM([
            $class: 'GitSCMSource',
            credentialsId: 'github-private',
            remote: 'git@github.com:fedspendingtransparency/data-act-broker-config.git',
            ])

        stage ('Wipe Workspace') { deleteDir() }

        stage ('GitHub Pulls') {
            dir('data-act-build-tools') {
              git url: "https://github.com/fedspendingtransparency/data-act-build-tools.git",
              branch: 'ops/service-desk-restart'
            }
        }
        stage('EC2 restart') {
            dir('data-act-build-tools') {

                sh """
                docker run -i -v ~/.aws:/root/.aws -v \$(pwd):/root python /bin/bash -c \
                'pip install boto3;python -u /root/servicedesk-scripts/reboot_Instance.py --elbname ${ELB}'
                """
            }
        }
    } catch (e) {
        currentBuild.result = "FAILED"
        throw e
    } finally {
        slack(currentBuild.result, "${SLACK_CHANNEL}")
    }
} //node