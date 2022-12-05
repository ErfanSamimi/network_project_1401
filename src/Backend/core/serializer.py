from .models import Message


def serialize_message(instance: Message):
    try :
        data = {
            'message_type': instance.type,
            'sender': instance.sender.email,
            'data': instance.send_date.isoformat(),
        }
    except:
        print(instance.send_date)
    if instance.type == 'text':
        data['text'] = instance.text
    else:
        data['message_id'] = instance.id

    return data