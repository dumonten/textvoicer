import uuid


def generate_uuid() -> str:
    """
    Generates a universally unique identifier (UUID).

    Returns:
    - The generated UUID as a string.
    """

    # Generate a UUID
    my_uuid = uuid.uuid4()
    # Convert the UUID to a string
    uuid_str = str(my_uuid)
    # Return the UUID string
    return uuid_str
