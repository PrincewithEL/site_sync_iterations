from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def file_extension(value, extension):
    return value.lower().endswith(extension)

