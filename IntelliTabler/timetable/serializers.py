from rest_framework import serializers
from .models import Module, ModuleGroup, ModuleParent

class ModuleParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleParent
        exclude=('user','sharedId',)


class ModuleGroupSerializer(serializers.ModelSerializer):
    parent=ModuleParentSerializer()
    class Meta:
        model = ModuleGroup
        fields = '__all__'
        depth = 1


class ModuleSerializer(serializers.ModelSerializer):
    group=ModuleGroupSerializer()
    class Meta:
        model = Module
        fields = '__all__'
        depth = 1