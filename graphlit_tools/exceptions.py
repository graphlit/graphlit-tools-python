class ToolException(Exception):
    """
    Custom exception class for tool-related errors.

    Args:
        error_message (str): A descriptive error message for the exception.
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)
        self.error_message = error_message

    def __str__(self) -> str:
        """
        String representation of the exception.

        Returns:
            str: The error message.
        """
        return self.error_message
