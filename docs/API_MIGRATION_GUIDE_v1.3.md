# API Migration Guide: v1.2 -> v1.3

> **Date:** Feb 15, 2026
> **Version:** v1.3
> **Focus:** Hero Attribute Cleanup

This document details the breaking changes introduced in version 1.3 of the Spellcasters Community API.

## 🚨 Breaking Changes

### 1. Removal of `movement_speed` from Heroes

The `movement_speed` attribute has been **removed** from the Hero schema and all Hero data files.

- **Old Behavior:** Heroes had a `movement_speed` property (e.g., `6`) in their root object.
- **New Behavior:** `movement_speed` is **no longer present** on Heroes. Attempting to validate a Hero with this property will result in a schema validation error.
- **Rationale:** Heroes do not use standard movement logic in the same way as Units; their mobility is often defined by abilities or client-side constants.

**Note:** Units and Titans **retain** the `movement_speed` property.

## 🛠️ Developer Migration Checklist

1.  [ ] **Update Hero Parsers:** Remove any logic that reads or depends on `hero.movement_speed`.
2.  [ ] **Update Interaction Logic:** If your tool calculates "Time to Arrive" or similar metrics for Heroes, you must update your formulas to use the new client-side constants or Ability-based mobility.
