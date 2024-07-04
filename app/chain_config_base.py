class ChainConfigBase:

    def __init__(self, config: dict = None):
        if config is None or not config:
            config = {"configurable": {}}
        self._config = config

    def get_config(self) -> dict:
        return self._config

    def __setitem__(self, item, value):
        """
        Allows setting values in the configuration dictionary.
        :param item: The key(s) to set.
        :param value: The value to set.
        """
        if isinstance(item, str):
            self._config["configurable"][item] = value
        elif isinstance(item, tuple):
            result = self._config["configurable"]
            for key in item[:-1]:
                result = result[key]
            result[item[-1]] = value
        else:
            raise TypeError("Invalid key type. Must be a string or a tuple of strings.")

    def __getitem__(self, item):
        """
        Allows direct access to the configuration dictionary.
        :param item: The key(s) to access.
        :return: The value corresponding to the key(s).
        """
        if isinstance(item, str):
            return self._config["configurable"][item]
        elif isinstance(item, tuple):
            result = self._config["configurable"]
            for key in item:
                result = result[key]
            return result
        else:
            raise TypeError("Invalid key type. Must be a string or a tuple of strings.")
