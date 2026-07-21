from proactive_workflow.approval import decide

def test_approval_validation_still_blocks_missing_identity():
    # Existing workflow tests exercise full models; this verifies instrumentation does not bypass preconditions.
    try: decide(None, None, None, "approve", "")  # type: ignore[arg-type]
    except (AttributeError, ValueError): pass
    else: raise AssertionError("approval precondition unexpectedly bypassed")
