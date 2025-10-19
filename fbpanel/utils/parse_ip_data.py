def parse_ip_data(data_string):
    """
    Converts a multi-line string of IP:port:username:password into a
    list of dictionaries with 'server', 'username', and 'password' keys.

    :param data_string: The input string.
    :return: A list of dictionaries.
    """
    result_array = []

    # Split the string into individual lines
    lines = data_string.strip().split('\n')

    for line in lines:
        # Split each line by the colon (:) delimiter
        parts = line.split(':')

        # Ensure the line has exactly 4 parts (IP, Port, User, Pass)
        if len(parts) == 4:
            ip_address = parts[0].strip()
            port = parts[1]
            username = parts[2]
            password = parts[3]

            # Create the dictionary (object) in the desired format
            obj = {
                'server': f'http://{ip_address}:{port}',
                'username': username,
                'password': password
            }
            result_array.append(obj)

    return result_array
