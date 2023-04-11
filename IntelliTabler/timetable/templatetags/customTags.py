from django import template

register = template.Library()

@register.filter
def getChildClass(value):
    if(value.__class__.__name__=='Department'):
        return 'Teacher'
    else:
        return value.__class__.__name__

@register.filter
def getClass(value):
    return value.__class__.__name__

@register.filter
def getPeriodNum(periods, counter):
    counter=counter-1
    return periods[counter][2]

@register.filter
def getPeriodName(periods, counter):
    counter=counter-1
    return periods[counter][1]

@register.filter
def getCheckBoxId(period, pcounter):
    return str(pcounter) + "-"+ period

@register.filter
def forRange(val):
    return [*range(1, val+1)]

@register.filter
def dict_lookup(dict, key):
    return dict[key]

#Filter version of javascript function
@register.filter
def getTextColor(color):
    rgb = [int(color[i:i+2], 16) for i in range(1, len(color), 2)]
    r, g, b = rgb[0], rgb[1], rgb[2]
    if (r*0.299 + g*0.587 + b*0.114) > 150:
        return '#000000'
    else:
        return '#ffffff'
