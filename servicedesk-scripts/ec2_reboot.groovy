#!/usr/bin/env groovy

node('matviews') {
    def SLACK_CHANNEL = "#operations"

    try {
        properties([
            parameters([
                choice(name: 'Atlassian ELBs',
                       choices: ['Atlassian-LoadBala-N2P7OUR3YJ9C', 'Confluence-ELB'],
                       description: 'ELB Names for Atlassian Tools'),
            ])
        ])

        // Slack Notification Library
        library identifier: 'broker@master', retriever: modernSCM([
            $class: 'GitSCMSource',
            credentialsId: 'github-private',
            remote: 'git@github.com:fedspendingtransparency/data-act-broker-config.git',
            ])

        stage ('GitHub Pulls') {
            deleteDir()
            dir('data-act-build-tools') {
              git url: "https://github.com/fedspendingtransparency/data-act-build-tools.git",
              branch: 'ops/service-desk-restart'
            }
        }
        stage('EC2 restart') {
            dir('data-act-build-tools') {
                sh """
                docker run -i -v ~/.aws:/root/.aws -v \$(pwd):/root python /bin/bash -c \
                'pip install boto3;python -u /root/servicedesk-scripts/reboot_instance.py --elbname ${ELB}'
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
