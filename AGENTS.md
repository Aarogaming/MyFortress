# MyFortress Agent Guide

## Scope
This file defines default operating behavior for IDE agents working inside `MyFortress` (auxiliary module).

## Primary Goals
1. Provide auxiliary support functionality for the ecosystem
2. Maintain integration with Library federation contracts
3. Keep cross-module communication patterns consistent
4. Support ecosystem-wide resilience

## Operating Principles
1. MyFortress is an auxiliary subsystem within AaroneousAutomationSuite
2. All v1.0.0 governance rules apply (minimal dependencies, type-safe, deterministic)
3. Auxiliary functionality must not block primary operations
4. Graceful degradation when unavailable

## Module Responsibilities
- Auxiliary support and helper functionality
- Cross-module communication facilitation
- Fallback and redundancy patterns
- Integration with Guild and Library through federation contracts

## Validation Requirements
Before committing changes:
1. Verify auxiliary functionality does not break primary operations
2. Test fallback patterns and graceful degradation
3. Confirm cross-module communication works
4. Validate federation contract compatibility

## Version Control
- Repository: `https://github.com/Aarogaming/MyFortress.git`
- Current Version: v1.0.0
- Default Branch: `main`
- Role: Auxiliary Support Module

## Federation Integration
MyFortress integrates with federation through:
- Library discovery contracts for artifact discovery
- Guild CI triage for test result synchronization
- AaroneousAutomationSuite orchestration

## Known Constraints
- Auxiliary functionality must be optional
- Primary operations cannot depend on MyFortress
- Cross-module patterns must be consistent with Guild and Library

## Support & Escalation
- Auxiliary functionality issues: Handle locally
- Federation integration: Escalate to Library
- Orchestration issues: Escalate to AaroneousAutomationSuite

---

*This guide was created as part of the v1.0.0 production release.*
