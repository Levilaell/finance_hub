# Pluggy API - Status vs ExecutionStatus Guide

## Overview

The Pluggy API uses two distinct fields to communicate the state of connections:

- **`status`**: High-level connection health indicator  
- **`executionStatus`**: Detailed execution state with specific reasons

Understanding the relationship between these fields is critical for proper error handling and sync logic.

## Status Field (High-Level Health)

The `status` field provides a first glance about the connection's health:

| Status | Meaning | Action Required |
|--------|---------|----------------|
| `UPDATED` | Connection successfully synced | Ready for data access |
| `UPDATING` | Update in progress | Wait and check again |
| `LOGIN_ERROR` | Invalid credentials provided | Update credentials |
| `OUTDATED` | Connection has errors | Check `executionStatus` for details |
| `WAITING_USER_INPUT` | Waiting for user input (MFA) | Provide required input |

## ExecutionStatus Field (Detailed State)

The `executionStatus` provides granular information about what happened during execution:

### Success States
| ExecutionStatus | Meaning | Sync Allowed |
|----------------|---------|--------------|
| `SUCCESS` | Complete success, all data synced | ✅ Yes |
| `PARTIAL_SUCCESS` | Some data synced, some products may have failed | ✅ Yes |

### In-Progress States
| ExecutionStatus | Meaning | Sync Allowed |
|----------------|---------|--------------|
| `CREATED` | Item just created | ⏳ Wait |
| `WAITING_USER_INPUT` | Waiting for MFA/user action | ❌ No - need input |

### Error States
| ExecutionStatus | Meaning | Sync Allowed |
|----------------|---------|--------------|
| `INVALID_CREDENTIALS` | Login failed | ❌ No - reconnect |
| `SITE_NOT_AVAILABLE` | Institution unavailable | ❌ No - try later |
| `ERROR` / `CONNECTION_ERROR` | Unexpected errors | ❌ No - reconnect |
| `USER_INPUT_TIMEOUT` | MFA timeout | ❌ No - reconnect |

## Correct Processing Logic

### 1. Priority Order for Checking

```python
# 1. Check execution_status first (more specific)
if execution_status == 'USER_INPUT_TIMEOUT':
    # Handle timeout - requires reconnection
    return handle_timeout()

# 2. Use helper function for comprehensive check  
can_sync, reason = _can_sync_with_item_status(status, execution_status)
if not can_sync:
    return handle_sync_blocked(reason)

# 3. Proceed with sync
return proceed_with_sync()
```

### 2. Success Handling

Both SUCCESS and PARTIAL_SUCCESS are valid for synchronization:

```python
# Correct: Check both success states
successful_executions = ['SUCCESS', 'PARTIAL_SUCCESS']
if execution_status in successful_executions:
    # Can proceed with sync
    
# Correct: Update status based on successful execution
if execution_status in ['SUCCESS', 'PARTIAL_SUCCESS'] and status in ['UPDATING', 'OUTDATED']:
    status = 'UPDATED'
```

### 3. OUTDATED Status Special Case

OUTDATED status requires checking executionStatus:

```python
if status == 'OUTDATED':
    if execution_status in ['SUCCESS', 'PARTIAL_SUCCESS']:
        # Connection outdated but last execution was successful - might still work
        logger.info(f"OUTDATED with successful execution {execution_status} - attempting sync")
        return proceed_with_sync()
    else:
        # OUTDATED with error execution - needs reconnection
        return handle_reconnection_required()
```

### 4. PARTIAL_SUCCESS Specific Logic

For Open Finance connections, PARTIAL_SUCCESS is common:

```python
# Handle successful connection but no accounts yet
if execution_status == 'PARTIAL_SUCCESS' and is_open_finance and status == 'UPDATED':
    # Normal scenario - accounts will be available later
    schedule_retry_task()
    return success_with_delayed_accounts()
```

## Common Mistakes to Avoid

### ❌ Wrong: Mixing status with executionStatus values
```python
# WRONG: Checking status for execution-specific values
if status == 'PARTIAL_SUCCESS':  # PARTIAL_SUCCESS is executionStatus, not status
    
# WRONG: Checking executionStatus for status-specific values  
if execution_status == 'UPDATED':  # UPDATED is status, not executionStatus
```

### ❌ Wrong: Ignoring the relationship between fields
```python
# WRONG: Only checking status without executionStatus context
if status == 'OUTDATED':
    return error()  # Should check executionStatus for the actual reason
```

### ❌ Wrong: Not handling PARTIAL_SUCCESS
```python
# WRONG: Only handling SUCCESS
if execution_status == 'SUCCESS':
    proceed_with_sync()
# MISSING: PARTIAL_SUCCESS is also valid for sync
```

## Fixed Implementation Examples

### Status Update Logic
```python
# Fixed: Only update status when appropriate
if execution_status in ['SUCCESS', 'PARTIAL_SUCCESS'] and status in ['UPDATING', 'OUTDATED']:
    status = 'UPDATED'
    logger.info(f"Updated status to UPDATED based on successful execution: {execution_status}")
```

### Sync Readiness Check
```python
def _can_sync_with_item_status(status: str, execution_status: str) -> tuple[bool, str]:
    # Error executions that prevent sync
    error_executions = ['USER_INPUT_TIMEOUT', 'INVALID_CREDENTIALS', 'SITE_NOT_AVAILABLE', 
                       'ERROR', 'CONNECTION_ERROR']
    
    if execution_status in error_executions:
        return False, f"Execution status prevents sync: {execution_status}"
    
    # Handle status with execution context
    if status == 'OUTDATED':
        if execution_status in ['SUCCESS', 'PARTIAL_SUCCESS']:
            return True, f"Item outdated but execution successful ({execution_status})"
        else:
            return False, f"Item outdated with problematic execution: {execution_status}"
    
    return True, "Sync allowed"
```

### Connection Success Handling
```python
# Fixed: Proper success detection
is_success = execution_status in ['SUCCESS', 'PARTIAL_SUCCESS']
is_connection_healthy = status == 'UPDATED'

if len(created_accounts) == 0:
    if execution_status == 'PARTIAL_SUCCESS' and is_open_finance and is_connection_healthy:
        # Normal scenario for Open Finance
        return success_with_delayed_accounts()
```

## Testing Scenarios

### Scenario 1: Normal Success
- status: `UPDATED`
- executionStatus: `SUCCESS`
- Action: ✅ Proceed with sync

### Scenario 2: Partial Success (Open Finance)
- status: `UPDATED` 
- executionStatus: `PARTIAL_SUCCESS`
- Action: ✅ Proceed with sync, schedule retry for missing accounts

### Scenario 3: Authentication Timeout
- status: `OUTDATED` or `WAITING_USER_INPUT`
- executionStatus: `USER_INPUT_TIMEOUT`
- Action: ❌ Block sync, require reconnection

### Scenario 4: Outdated but Working
- status: `OUTDATED`
- executionStatus: `SUCCESS`
- Action: ✅ Allow sync with warning, consider reconnection

### Scenario 5: Complete Failure
- status: `LOGIN_ERROR`
- executionStatus: `INVALID_CREDENTIALS`
- Action: ❌ Block sync, require credential update

## Summary

1. **Always check `executionStatus` first** - it provides the most specific information
2. **Both SUCCESS and PARTIAL_SUCCESS are valid** for synchronization
3. **OUTDATED status requires context** from executionStatus
4. **PARTIAL_SUCCESS is normal** for Open Finance connections
5. **Never mix the field values** - they belong to different domains