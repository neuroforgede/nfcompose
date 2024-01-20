import uuid
while True:
    i = uuid.uuid4()
    print('{"external_id": "test' + str(i) + '", "payload": {"some_data": "test' + str(i) + '"}}')
    #time.sleep(0.001)