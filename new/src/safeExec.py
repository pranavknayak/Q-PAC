import traceback

def safeExec(code: str, safeGlobals: dict, variables: dict):
    """
    Executes Python code line by line.
    If a line raises an exception, mark it as a 'Compilation error',
    skip it, and continue with the rest.
    """
    cleaned_lines = []
    errors = []

    for lineno, line in enumerate(code.splitlines(), start=1):
        # Skip empty or whitespace-only lines
        if not line.strip():
            cleaned_lines.append(line)
            continue

        try:
            # Try executing this line in isolation
            exec(line, safeGlobals, variables)
            cleaned_lines.append(line)
        except Exception as e:
            errors.append(f"Line {lineno}: {line.strip()} -> Compilation error: {e}")
            # skip this line

    # Re-run only the valid lines as a block
    cleaned_code = "\n".join(cleaned_lines)
    try:
        exec(cleaned_code, safeGlobals, variables)
    except Exception as e:
        errors.append(f"Final block execution failed: {e}")
        traceback.print_exc()

    return errors
