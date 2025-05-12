import os
from pathlib import Path


def deduplicate_java_classpath(classpath, classpath_separator):
    paths = classpath.split(classpath_separator)

    cleaned_classpath = [str(Path(p.strip())) for p in paths if p.strip()]

    return classpath_separator.join(cleaned_classpath)


def delete_missing_java_classpath(classpath, classpath_separator):
    paths = classpath.split(classpath_separator)
    existing_classpath = [p for p in paths if os.path.exists(p)]
    return classpath_separator.join(existing_classpath)


def replace_specified_value_to_target_string_in_java_classpath(classpath, classpath_separator, value, string):
    paths = classpath.split(classpath_separator)

    new_paths = [path.replace(value, string) for path in paths]

    return classpath_separator.join(new_paths)