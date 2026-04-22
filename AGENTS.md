# MyFortress Operational Agent Guide

## Lifecycle Status
**Status:** quarantine_pending

## 1. Operational Parameters
- **Autonomy Level:** 4/5
- **Memory/State Model:** generalist

## 2. Hard Boundaries (Constraints)
- never_bypass_control_plane_lease_for_mutation
- never_execute_destructive_operations_without_policy_gate
- never_emit_unvalidated_manifest_changes

## 3. Federation Dependencies
Relies on: Library

## 4. Capability Mapping
Handles the following MCP event triggers:
- `myfortress.fortress_secret_scan`
- `myfortress.fortress_policy_evaluate`
