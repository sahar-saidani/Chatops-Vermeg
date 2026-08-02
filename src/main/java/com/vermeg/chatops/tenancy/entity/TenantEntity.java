package com.vermeg.chatops.tenancy.entity;

import com.vermeg.chatops.common.persistence.AuditableEntity;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import org.hibernate.annotations.LazyCollection;
import org.hibernate.annotations.LazyCollectionOption;

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

    // Extra-lazy: addEnvironment() must not pull every existing environment
    // row into memory just to append one (was a full tenant-scoped SELECT on
    // every environment create).
    @LazyCollection(LazyCollectionOption.EXTRA)
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