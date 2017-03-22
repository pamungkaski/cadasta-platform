"""Party Serializers."""

from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from rest_framework import serializers

from .models import Party, PartyRelationship, TenureRelationship
from core.serializers import FieldSelectorSerializer
from core.mixins import SchemaSelectorMixin
from spatial.serializers import SpatialUnitSerializer


class PartySerializer(SchemaSelectorMixin,
                      FieldSelectorSerializer,
                      serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ('id', 'name', 'type', 'attributes', )
        read_only_fields = ('id', )

    def create(self, validated_data):
        project = self.context['project']
        return Party.objects.create(
            project=project, **validated_data)

    def validate(self, data):
        for name, field in self.fields.items():
            if not type(field) in [CharField, JSONField]:
                continue

        print(self.fields)
        return data

    def validate_attributes(self, attrs):
        errors = []
        content_type = ContentType.objects.get_for_model(self.Meta.model)
        label = '{}.{}'.format(content_type.app_label, content_type.model)
        attributes = self.get_model_attributes(self.context['project'], label)

        relevant_attributes = attributes.get(self.initial_data['type'], {})
        for key, attr in relevant_attributes.items():
            try:
                attr.validate(attrs.get(key))
            except ValidationError as e:
                errors += e.messages

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class PartyRelationshipReadSerializer(serializers.ModelSerializer):

    party1 = PartySerializer(fields=('id', 'name', 'type'))
    party2 = PartySerializer(fields=('id', 'name', 'type'))
    rel_class = serializers.SerializerMethodField()

    class Meta:
        model = PartyRelationship
        fields = ('rel_class', 'id', 'party1', 'party2', 'type', 'attributes')
        read_only_fields = ('id',)

    def get_rel_class(self, obj):
        return 'party'


class PartyRelationshipWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = PartyRelationship
        fields = ('id', 'party1', 'party2', 'type', 'attributes')
        read_only_fields = ('id',)

    def validate(self, data):
        if self.instance:
            party1 = data.get('party1', self.instance.party1)
            party2 = data.get('party2', self.instance.party2)
        else:
            party1 = data['party1']
            party2 = data['party2']
        if party1.id == party2.id:
            raise serializers.ValidationError(
                _("The parties must be different"))
        elif party1.project.slug != party2.project.slug:
            err_msg = _(
                "'party1' project ({}) should be equal to"
                " 'party2' project ({})")
            raise serializers.ValidationError(
                err_msg.format(party1.project.slug, party2.project.slug))
        return data

    def create(self, validated_data):
        project = self.context['project']
        return PartyRelationship.objects.create(
            project=project, **validated_data)


class TenureRelationshipReadSerializer(serializers.ModelSerializer):

    party = PartySerializer(fields=('id', 'name', 'type'))
    spatial_unit = SpatialUnitSerializer(fields=(
        'id', 'name', 'geometry', 'type'))
    rel_class = serializers.SerializerMethodField()

    class Meta:
        model = TenureRelationship
        fields = ('rel_class', 'id', 'party', 'spatial_unit', 'tenure_type',
                  'attributes')
        read_only_fields = ('id',)

    def get_rel_class(self, obj):
        return 'tenure'


class TenureRelationshipWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = TenureRelationship
        fields = ('id', 'party', 'spatial_unit', 'tenure_type', 'attributes')
        read_only_fields = ('id',)

    def validate(self, data):
        if self.instance:
            party = data.get('party', self.instance.party)
            spatial_unit = data.get('spatial_unit', self.instance.spatial_unit)
        else:
            party = data['party']
            spatial_unit = data['spatial_unit']
        if party.project.slug != spatial_unit.project.slug:
            err_msg = _(
                "'party' project ({}) should be equal to"
                " 'spatial_unit' project ({})")
            raise serializers.ValidationError(
                err_msg.format(party.project.slug, spatial_unit.project.slug))
        return data

    def create(self, validated_data):
        project = self.context['project']
        return TenureRelationship.objects.create(
            project=project, **validated_data)
