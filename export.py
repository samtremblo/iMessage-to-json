import os
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

def parse_datetime(dt_str):
    """Convert datetime string to millisecond timestamp"""
    # Remove any text in parentheses
    dt_str = re.sub(r'\s*\([^)]*\)', '', dt_str)
    dt = datetime.strptime(dt_str.strip(), '%b %d, %Y %I:%M:%S %p')
    return int(dt.timestamp() * 1000)

def get_number_from_filename(file_path):
    """Extract recipient number from the HTML filename"""
    base_name = os.path.basename(file_path)
    match = re.search(r'(\+\d+)', base_name)
    if match:
        number = match.group(1)
        # Remove any formatting from the phone number
        return re.sub(r'[^0-9+]', '', number)
    return None

def parse_html_file(file_path):
    messages = []
    thread_number = get_number_from_filename(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        
    message_divs = soup.find_all('div', class_='message')
    
    for message_div in message_divs:
        message_container = message_div.find('div', class_=['sent', 'received'])
        if not message_container:
            continue
            
        is_sent = 'sent' in message_container.get('class', [])
        message_type = 2 if is_sent else 1  # 1 for received, 2 for sent
        
        timestamp_span = message_container.find('span', class_='timestamp')
        bubble_span = message_container.find('span', class_='bubble')
        
        if not timestamp_span or not bubble_span:
            continue
            
        address = thread_number
        timestamp = parse_datetime(timestamp_span.text)
        
        message = {
            "phone_number": address,
            "text": bubble_span.text.strip(),
            "timestamp": timestamp,
            "type": message_type,
            "read": 1,
            "thread_id": abs(hash(address)) % (10 ** 8)  # Generate consistent thread ID from phone number
        }
        
        messages.append(message)
    
    return messages

def convert_files_to_json(folder_path):
    all_messages = []
    
    for filename in os.listdir(folder_path):
        if filename.endswith('.html'):
            file_path = os.path.join(folder_path, filename)
            try:
                messages = parse_html_file(file_path)
                all_messages.extend(messages)
                print(f"Processed {filename} - {len(messages)} messages")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue
    
    # Sort messages by timestamp
    all_messages.sort(key=lambda x: x["timestamp"])
    
    # Create the proper backup structure
    backup_data = {
        "version": 1,
        "messages": all_messages
    }
    
    output_path = os.path.join(folder_path, 'messages_backup.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    return output_path

# Get the current directory where the script is running
current_dir = os.path.dirname(os.path.abspath(__file__))
try:
    output_file = convert_files_to_json(current_dir)
    print(f"Successfully exported messages to: {output_file}")
except Exception as e:
    print(f"Error during conversion: {str(e)}")
