def sanitize_alias(alias):
    return alias.replace(" ", "_") \
        .replace("-", "_") \
        .replace(".", "_")
