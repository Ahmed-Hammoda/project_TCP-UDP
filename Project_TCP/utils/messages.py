"""
Shared helper functions for encoding/decoding JSON messages
"""

import json


def encode_message(message: dict) -> str:
    """
    Encode a message dictionary to JSON string format
    
    Args:
        message: Dictionary containing message data
        
    Returns:
        JSON string with newline appended
    """
    return json.dumps(message) + '\n'


def decode_message(data: str) -> dict:
    """
    Decode JSON string to message dictionary
    
    Args:
        data: JSON string
        
    Returns:
        Dictionary containing message data
        
    Raises:
        json.JSONDecodeError: If data is not valid JSON
    """
    return json.loads(data)


def send_json_message(socket, message: dict, encoding: str = 'utf-8'):
    """
    Send a JSON message through a socket
    
    Args:
        socket: Socket object to send message through
        message: Dictionary containing message data
        encoding: Character encoding to use (default: 'utf-8')
    """
    msg = encode_message(message)
    socket.sendall(msg.encode(encoding))


def receive_json_messages(buffer: str, data: str) -> tuple:
    """
    Process incoming data and extract complete JSON messages
    
    Args:
        buffer: Current buffer of incomplete data
        data: New data received
        
    Returns:
        Tuple of (messages list, new buffer)
    """
    messages = []
    buffer += data
    
    while '\n' in buffer:
        line, buffer = buffer.split('\n', 1)
        try:
            messages.append(decode_message(line))
        except json.JSONDecodeError:
            pass
    
    return messages, buffer
