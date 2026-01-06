import os

# Read the file
with open('app/routers/locations.py', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')
print(f'Null bytes found: {data.count(b"\\x00")}')

# Remove null bytes
clean_data = data.replace(b'\x00', b'')

# Write back
with open('app/routers/locations.py', 'wb') as f:
    f.write(clean_data)

print('✅ File cleaned - null bytes removed')
print(f'New file size: {len(clean_data)} bytes')
