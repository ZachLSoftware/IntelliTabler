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