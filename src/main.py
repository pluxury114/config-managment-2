import sys
from pathlib import Path
from urllib.parse import urlsplit

import yaml


DEFAULT_CONFIG = Path("config/config.yaml")
CONFIG_KEYS = ("package", "repository", "test_mode", "ascii_tree")


def load_config(path):
    """Read configuration from a YAML file."""
    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("YAML должен содержать пары ключ: значение")

    return config


def require_text(config, key):
    """Check a required string parameter."""
    if key not in config:
        raise ValueError(f"отсутствует параметр '{key}'")

    value = config[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{key}' должен быть непустой строкой")

    return value.strip()


def require_bool(config, key):
    """Check a required Boolean parameter."""
    if key not in config:
        raise ValueError(f"отсутствует параметр '{key}'")

    if type(config[key]) is not bool:
        raise ValueError(f"'{key}' должен быть true или false")

    return config[key]


def validate_source(source, test_mode):
    """Check the repository address or test file."""
    if test_mode:
        if source.startswith(("http://", "https://")):
            raise ValueError("в тестовом режиме нужен путь к файлу")

        if not Path(source).is_file():
            raise ValueError(f"тестовый файл не найден: {source}")

        return

    url = urlsplit(source)
    if url.scheme not in ("http", "https") or not url.netloc:
        raise ValueError("в обычном режиме нужен URL http или https")


def validate_config(config):
    """Validate configuration parameters."""
    require_text(config, "package")
    source = require_text(config, "repository")
    test_mode = require_bool(config, "test_mode")
    require_bool(config, "ascii_tree")

    validate_source(source, test_mode)


def main():
    """Load, validate and display configuration."""
    if len(sys.argv) > 2:
        print("Использование: python src/main.py [config.yaml]")
        return 1

    if len(sys.argv) == 2:
        config_path = Path(sys.argv[1])
    else:
        config_path = DEFAULT_CONFIG

    try:
        config = load_config(config_path)
        validate_config(config)
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        return 1

    for key in CONFIG_KEYS:
        print(f"{key}: {config[key]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
