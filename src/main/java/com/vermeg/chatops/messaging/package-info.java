/**
 * RabbitMQ integration layer connecting the Spring Boot backend to the
 * existing, independently-deployed Python Agents (git, jenkins, jira, log,
 * installation, infrastructure).
 *
 * <p>Agents never call Spring Boot directly; all communication flows through
 * RabbitMQ exchanges/queues declared here.
 */
package com.vermeg.chatops.messaging;