ERRS = {
    'not_member': 'You are not a member',
    'not_connected': 'You are not connected into this room',
    'already_connected': 'You are already connected into some room',
    'max_name_len': 'Maximum length of the room/user name is 32 characters',
    'max_len': 'Maximum length of the message is 1024 characters',
    'unallowed_chars': 'The room/user name can only contains letters <a, z>',
    'already_exists': 'Room/user with this name already exists',
    'not_owner': 'Only owner can execute this operation',
    'no_such': 'This room is not exists',
    'owner_cant_leave': 'The room owner cannot leave from his room'
}


def fmt(event: str, **kwargs) -> dict:
    '''format json for client'''
    return {'event': event} | kwargs

def errfmt(err: str) -> dict:
    '''format json with error for client'''
    return fmt('error', name=err, description=ERRS[err])