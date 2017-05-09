def validate_file_extension(value):
    import os
    from django.core.exceptions import ValidationError
    ext = os.path.splitext(value.name)[1]
    if not ext.lower() == '.csv':
        raise ValidationError('Must be csv file.')
