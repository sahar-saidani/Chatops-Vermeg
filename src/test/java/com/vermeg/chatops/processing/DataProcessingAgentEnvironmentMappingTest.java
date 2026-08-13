package com.vermeg.chatops.processing;

import com.vermeg.chatops.messaging.dto.AgentMessage;
import com.vermeg.chatops.processing.entity.CanonicalEventEntity;
import com.vermeg.chatops.processing.service.DataProcessingAgent;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * canonical_events.environment must record where the <em>agent</em> ran, not
 * where the backend happens to be deployed.
 *
 * <p>Resolution used to consult only the payload-internal "env" key and then
 * fall back to the server's own active Spring profile, so with the backend on
 * the dev profile every event was stamped "dev" whatever its real environment
 * -- and the required top-level environment field was ignored entirely. These
 * tests run under the "test" profile, so a regression would surface as the
 * literal string "test" appearing in the persisted column.
 */
@SpringBootTest
@ActiveProfiles("test")
@Transactional
class DataProcessingAgentEnvironmentMappingTest {

    @Autowired
    private DataProcessingAgent dataProcessingAgent;

    private static AgentMessage message(String environment, Map<String, Object> data) {
        return new AgentMessage(
                "git",
                Instant.now(),
                data,
                "MAIF",
                environment,
                "STANDALONE",
                "MAIF-WINDOWS-01",
                null,
                null
        );
    }

    @Test
    void theTopLevelEnvironmentFieldIsWhatGetsPersisted() {
        CanonicalEventEntity saved =
                dataProcessingAgent.process("git", message("PROD", Map.of("some", "payload")));

        assertThat(saved.getEnvironment()).isEqualTo("PROD");
    }

    @Test
    void theTopLevelEnvironmentWinsOverThePayloadEnvKey() {
        CanonicalEventEntity saved =
                dataProcessingAgent.process("git", message("DEV", Map.of("env", "somethingElse")));

        assertThat(saved.getEnvironment()).isEqualTo("DEV");
    }

    @Test
    void theServerProfileIsNeverUsedWhenTheAgentStatedItsEnvironment() {
        CanonicalEventEntity saved =
                dataProcessingAgent.process("git", message("DEV", Map.of("some", "payload")));

        assertThat(saved.getEnvironment()).isNotEqualTo("test");
    }

    @Test
    void theRestOfTheEnvelopeIsMappedThrough() {
        CanonicalEventEntity saved =
                dataProcessingAgent.process("git", message("DEV", Map.of("some", "payload")));

        assertThat(saved.getAgentKey()).isEqualTo("git");
        assertThat(saved.getTenant()).isEqualTo("MAIF");
        assertThat(saved.getEnvironmentType()).isEqualTo("STANDALONE");
        assertThat(saved.getMachineReference()).isEqualTo("MAIF-WINDOWS-01");
        assertThat(saved.getData()).containsEntry("some", "payload");
        assertThat(saved.getMessageTimestamp()).isNotNull();
    }
}
