import os


class EnvironmentVariableHandler:
    def get_value_from_env_variable(self, env_key: str) -> str:
        """Get a value from the environment variable.

        Args:
            env_key: The environment variable to look up if the key is not
                in the dictionary.

        Returns:
            str: The value of the environment variable.

        """
        if env_key in os.environ and os.environ[env_key]:
            return os.environ[env_key]

        print(f"\nDid not find {env_key}, please add this environment variable!\n")
        raise ValueError(f"Environment variable {env_key} not found")
