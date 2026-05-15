// ============================================================================
// Jenkinsfile — Student Records Management CI/CD Pipeline
// Course: CSE483 – Topics in Software Engineering II
//
// Pipeline stages:
//   1. Code Build                    — build the Flask app Docker image
//   2. Unit Testing                  — run pytest (SQLite, no PostgreSQL needed)
//   3. Containerized Deployment      — spin up PostgreSQL + Flask, wait for /health
//   4. Containerized Selenium Testing — run E2E tests on the live deployment
// ============================================================================

pipeline {
    agent any

    // ── Build-scoped variables ──────────────────────────────────────────────
    environment {
        APP_IMAGE      = "student-records-app"
        SELENIUM_IMAGE = "student-records-selenium"
        IMAGE_TAG      = "${BUILD_NUMBER}"

        // Container & network names are unique per build number so parallel
        // builds (or leftover containers) never collide.
        CONTAINER_APP  = "srm_app_${BUILD_NUMBER}"
        CONTAINER_DB   = "srm_db_${BUILD_NUMBER}"
        NETWORK_NAME   = "srm_net_${BUILD_NUMBER}"

        // Port the Flask app is exposed on the Jenkins host for health checks.
        // Port 5000 is opened in the EC2 security group.
        APP_PORT       = "5000"

        // PostgreSQL credentials used for both the DB container and app config
        DB_USER        = "postgres"
        DB_PASS        = "Ahsan@_123"
        DB_NAME        = "student_records_db"
    }

    stages {

        // ====================================================================
        // STAGE 1 — CODE BUILD
        // Pull latest source from GitHub (configured in Jenkins job as SCM)
        // and build the Flask application Docker image.
        // ====================================================================
        stage('Code Build') {
            steps {
                echo '======================================================='
                echo '[Stage 1] CODE BUILD — Cloning repo & building image'
                echo '======================================================='

                // Checkout configured SCM (GitHub repo set in Jenkins job)
                checkout scm

                echo "Building Docker image: ${APP_IMAGE}:${IMAGE_TAG}"

                sh """
                    docker build \\
                        -t ${APP_IMAGE}:${IMAGE_TAG} \\
                        -t ${APP_IMAGE}:latest \\
                        --file Dockerfile \\
                        .
                """

                echo "Image built successfully:"
                sh "docker images ${APP_IMAGE} --format 'table {{.Repository}}\\t{{.Tag}}\\t{{.Size}}'"
            }
        }

        // ====================================================================
        // STAGE 2 — UNIT TESTING
        // Mount source code into a plain python:3.11-slim container and run
        // pytest.  Tests use SQLite in-memory — no MySQL service required.
        // The JUnit XML output is published to Jenkins for trend graphs.
        // ====================================================================
        stage('Unit Testing') {
            steps {
                echo '======================================================='
                echo '[Stage 2] UNIT TESTING — Running pytest (SQLite)'
                echo '======================================================='

                sh """
                    docker run --rm \\
                        -v \$(pwd):/app \\
                        -w /app \\
                        python:3.11-slim \\
                        sh -c "pip install -q -r requirements.txt && \\
                               pytest tests/ -v --tb=short --junitxml=test-results.xml"
                """

                echo 'All unit tests passed!'
            }

            post {
                always {
                    // Publish results to Jenkins (requires the JUnit plugin)
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                    echo 'Unit test report published to Jenkins.'
                }
            }
        }

        // ====================================================================
        // STAGE 3 — CONTAINERIZED DEPLOYMENT
        // 1. Create an isolated Docker network for this build
        // 2. Start PostgreSQL 16 and wait until pg_isready succeeds
        // 3. Start the Flask app container on the same network
        // 4. Poll /health until it returns HTTP 200 (max 60 s)
        // ====================================================================
        stage('Containerized Deployment') {
            steps {
                echo '======================================================='
                echo '[Stage 3] CONTAINERIZED DEPLOYMENT — Starting services'
                echo '======================================================='

                // Create a per-build isolated bridge network
                sh "docker network create ${NETWORK_NAME}"
                echo "Docker network '${NETWORK_NAME}' created."

                // ── Start PostgreSQL ────────────────────────────────────────
                echo 'Starting PostgreSQL 16 container...'
                sh """
                    docker run -d \\
                        --name ${CONTAINER_DB} \\
                        --network ${NETWORK_NAME} \\
                        -e POSTGRES_USER=${DB_USER} \\
                        -e POSTGRES_PASSWORD=${DB_PASS} \\
                        -e POSTGRES_DB=${DB_NAME} \\
                        postgres:16
                """

                // Wait for PostgreSQL to accept connections (up to 60 s)
                echo 'Waiting for PostgreSQL to become ready...'
                sh """
                    READY=0
                    for i in \$(seq 1 12); do
                        if docker exec ${CONTAINER_DB} \\
                               pg_isready -U ${DB_USER} 2>/dev/null; then
                            echo "PostgreSQL is ready (attempt \${i})"
                            READY=1
                            sleep 3
                            break
                        fi
                        echo "Attempt \${i}/12 — PostgreSQL not ready, waiting 5 s..."
                        sleep 5
                    done
                    if [ "\${READY}" = "0" ]; then
                        echo "ERROR: PostgreSQL did not start in time."
                        exit 1
                    fi
                """

                // ── Start Flask app ─────────────────────────────────────────
                echo "Starting Flask app container (${APP_IMAGE}:${IMAGE_TAG})..."
                sh """
                    docker run -d \\
                        --name ${CONTAINER_APP} \\
                        --network ${NETWORK_NAME} \\
                        -p ${APP_PORT}:5000 \\
                        -e DB_HOST=${CONTAINER_DB} \\
                        -e DB_USER=${DB_USER} \\
                        -e DB_PASSWORD=${DB_PASS} \\
                        -e DB_NAME=${DB_NAME} \\
                        -e SECRET_KEY=jenkins-pipeline-secret \\
                        ${APP_IMAGE}:${IMAGE_TAG}
                """

                // Wait for /health to return 200 (up to 60 s)
                echo 'Waiting for Flask app health check to pass...'
                sh """
                    for i in \$(seq 1 12); do
                        STATUS=\$(curl -s -o /dev/null -w "%{http_code}" \\
                                  http://localhost:${APP_PORT}/health 2>/dev/null || echo "000")
                        if [ "\${STATUS}" = "200" ]; then
                            echo "App is healthy! (HTTP \${STATUS}) after attempt \${i}"
                            break
                        fi
                        echo "Attempt \${i}/12 — status \${STATUS}, waiting 5 s..."
                        sleep 5
                    done

                    # Final validation — fail the stage if app is still down
                    FINAL=\$(curl -s -o /dev/null -w "%{http_code}" \\
                              http://localhost:${APP_PORT}/health 2>/dev/null || echo "000")
                    if [ "\${FINAL}" != "200" ]; then
                        echo "FATAL: Flask app failed health check (last status: \${FINAL})"
                        echo "--- App container logs ---"
                        docker logs ${CONTAINER_APP}
                        exit 1
                    fi
                """

                echo "Deployment successful! App running at http://localhost:${APP_PORT}"
            }
        }

        // ====================================================================
        // STAGE 4 — CONTAINERIZED SELENIUM TESTING
        // Build the Selenium image (Python + headless Chromium) and run all
        // E2E tests against the live app on the shared Docker network.
        // The app is reachable inside the network as http://<CONTAINER_APP>:5000
        // ====================================================================
        stage('Containerized Selenium Testing') {
            steps {
                echo '======================================================='
                echo '[Stage 4] SELENIUM TESTING — Building image & running E2E tests'
                echo '======================================================='

                // Build the Selenium runner image
                echo "Building Selenium image: ${SELENIUM_IMAGE}:${IMAGE_TAG}"
                sh """
                    docker build \\
                        -t ${SELENIUM_IMAGE}:${IMAGE_TAG} \\
                        --file Dockerfile.selenium \\
                        .
                """

                // Run Selenium tests on the same network as the deployed app.
                // --shm-size=2g prevents Chrome crashes caused by /dev/shm limits.
                echo "Running Selenium tests against http://${CONTAINER_APP}:5000 ..."
                sh """
                    docker run --rm \\
                        --name srm_selenium_${BUILD_NUMBER} \\
                        --network ${NETWORK_NAME} \\
                        --shm-size=2g \\
                        -e APP_URL=http://${CONTAINER_APP}:5000 \\
                        ${SELENIUM_IMAGE}:${IMAGE_TAG}
                """

                echo 'All Selenium tests completed successfully!'
            }
        }

    } // end stages

    // ========================================================================
    // POST ACTIONS — always run cleanup; report on success / failure
    // ========================================================================
    post {

        always {
            echo '======================================================='
            echo '[Post] CLEANUP — Removing containers, network, and images'
            echo '======================================================='

            sh """
                # Stop and remove app containers (|| true so missing ones don't fail)
                docker stop  ${CONTAINER_APP} ${CONTAINER_DB} 2>/dev/null || true
                docker rm    ${CONTAINER_APP} ${CONTAINER_DB} 2>/dev/null || true

                # Remove the per-build network
                docker network rm ${NETWORK_NAME} 2>/dev/null || true

                # Remove the Selenium image (rebuilt each run to stay current)
                docker rmi ${SELENIUM_IMAGE}:${IMAGE_TAG} 2>/dev/null || true
            """

            echo 'Cleanup complete.'
        }

        success {
            echo '======================================================='
            echo "[Post] SUCCESS — ${JOB_NAME} #${BUILD_NUMBER} passed all stages!"
            echo '======================================================='
        }

        failure {
            echo '======================================================='
            echo "[Post] FAILURE — ${JOB_NAME} #${BUILD_NUMBER} FAILED."
            echo 'Dumping container logs to help diagnose the issue:'
            echo '======================================================='

            sh """
                echo '--- Flask app container logs ---'
                docker logs ${CONTAINER_APP} 2>/dev/null || echo '(container not found)'
                echo '--- PostgreSQL container logs ---'
                docker logs ${CONTAINER_DB}  2>/dev/null || echo '(container not found)'
            """
        }

    }

} // end pipeline
