# ADR-001: Aurora MySQL as Operational Source System

## Status

Accepted

## Context

The platform needs real-time access to transactional data from sales orders, appointments, POS invoices, and work orders. These systems require a relational store with ACID compliance, low-latency reads, and native CDC support for downstream streaming.

## Decision

Use AWS Aurora MySQL as the system of record for all core operational domains:

- Sales order system
- Appointment application
- POS invoice activities
- Work order activities
- Inventory snapshots

## Consequences

- Aurora MySQL provides native binary log replication compatible with AWS DMS and Debezium.
- All KPI computation depends on CDC streams originating from Aurora MySQL.
- Schema changes in Aurora MySQL must be coordinated with bronze table definitions.
- Read replicas can serve analytics workloads without impacting transactional performance.
