import os
import json
from datetime import datetime
import re

def parse_datetime(dt_str):
    """Convert datetime string to millisecond timestamp"""
    dt = datetime.strptime(dt_str, '%b %d, %Y %I:%M:%S %p')
    return int(dt.timestamp() * 1000)

def parse_message_file(file_path):
    messages = []
    current_message = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Try to match datetime pattern
        date_match = re.match(r'([A-Z][a-z]{2} \d{1,2}, \d{4}\s+\d{1,2}:\d{2}:\d{2} [AP]M)', line)
        
        if date_match:
            if current_message:
                messages.append(current_message)
                
            dt_str = date_match.group(1)
            timestamp = parse_datetime(dt_str)
            
            # Check if there's read status
            read_status = 1  # Default to read
            if "(Read by you after" in line:
                read_status = 1
            
            current_message = {
                "subscriptionId": 1,  # Default to 1
                "address": "",
                "body": "",
                "date": timestamp,
                "dateSent": 0,  # Default to 0
                "locked": 0,  # Default to unlocked
                "protocol": None,  # Default to None
                "read": read_status,
                "status": -1,  # Default to -1 (status unknown)
                "type": 1,  # Default to received
                "serviceCenter": None,  # Default to None
                "backupType": "sms",  # Default to sms
            }
            continue
            
        # Check for phone number
        if line.startswith('+'):
            current_message["address"] = line
            continue
            
        # Check for sender indicator
        if line == "Me":
            if current_message:
                current_message["type"] = 2  # Sent message
            continue
            
        # Check for deleted message
        if line == "This message was deleted from the conversation!":
            if current_message:
                current_message["deleted"] = True
            continue
            
        # Check for reactions (Tapbacks)
        if line.startswith("Tapbacks:"):
            if current_message:
                # Parse next line(s) for reactions until we hit a non-reaction line
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith(('Feb', 'Mar', 'Jan', '+', 'Me')):
                    reaction_line = lines[j].strip()
                    if reaction_line:
                        # Parse reaction line (e.g., "❤️ by +15147071515")
                        reaction_parts = reaction_line.split(' by ')
                        if len(reaction_parts) == 2:
                            current_message["reactions"].append({
                                "emoji": reaction_parts[0].strip(),
                                "sender": reaction_parts[1].strip()
                            })
                    j += 1
            continue
            
        # Add to message body if not a reaction line
        if current_message and not line.startswith("Tapbacks:"):
            if current_message["body"]:
                current_message["body"] += "\n"
            current_message["body"] += line
    
    # Add the last message
    if current_message:
        messages.append(current_message)
        
    return messages

def get_thread_id(filename):
    """Extract thread ID from filename or generate a hash if no numbers found"""
    numbers = ''.join(filter(str.isdigit, filename))
    if numbers:
        return int(numbers)
    else:
        # If no numbers in filename, use a hash of the filename
        return abs(hash(filename)) % (10 ** 8)  # Limit to 8 digits

def convert_files_to_json(folder_path):
    all_messages = []
    thread_counter = 1
    
    # Process all .txt files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            
            # Get thread_id from filename or generate one
            thread_id = get_thread_id(filename)
            
            try:
                messages = parse_message_file(file_path)
                
                # Assign thread_id to all messages from this file
                for msg in messages:
                    msg["thread_id"] = thread_id
                
                all_messages.extend(messages)
                print(f"Processed {filename} - Thread ID: {thread_id}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue
    
    # Sort messages by date
    all_messages.sort(key=lambda x: x["date"])
    
    # Write to output file
    output_path = os.path.join(folder_path, 'messages_export.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_messages, f, ensure_ascii=False, indent=2)
    
    return output_path

# Get the current directory where the script is running
current_dir = os.path.dirname(os.path.abspath(__file__))
try:
    output_file = convert_files_to_json(current_dir)
    print(f"Successfully exported messages to: {output_file}")
except Exception as e:
    print(f"Error during conversion: {str(e)}")
