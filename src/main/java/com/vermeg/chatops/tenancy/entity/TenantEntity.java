package com.vermeg.chatops.tenancy.entity;

import com.vermeg.chatops.common.persistence.AuditableEntity;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

@Entity
@Table(name = "tenants")
public class TenantEntity extends AuditableEntity {

    @Column(nullable = false, unique = true, length = 160)
    private String name;

    @Column(nullable = false)
    private boolean active;

    @OneToMany(mappedBy = "tenant", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<EnvironmentEntity> environments = new ArrayList<>();

    protected TenantEntity() {
    }

    public TenantEntity(String name) {
        this.name = name.strip();
        this.active = true;
    }

    public String getName() {
        return name;
    }

    public boolean isActive() {
        return active;
    }

    public List<EnvironmentEntity> getEnvironments() {
        return Collections.unmodifiableList(environments);
    }

    public void rename(String name) {
        this.name = name.strip();
    }

    public void deactivate() {
        this.active = false;
    }

    public EnvironmentEntity addEnvironment(String name, EnvironmentType type) {
        EnvironmentEntity environment = new EnvironmentEntity(this, name, type);
        environments.add(environment);
        return environment;
    }
}