from .models import Message


def serialize_message(instance: Message):
    try :
        data = {
            'message_type': instance.type,
            'message_id': instance.id,
            'sender': instance.sender.email,
            'date': instance.send_date.isoformat(),
        }
    except:
        print(instance.send_date)

    if instance.type == 'text':
        data['text'] = instance.text


    return data