def get_user_by_id(users, requested_id):
    for user in users:
        if user_id == requested_id:
            return user
    return None


def is_adult(age):
    return age > 18
