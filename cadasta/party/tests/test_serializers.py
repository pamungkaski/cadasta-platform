"""Party serializer test cases."""
import pytest
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from rest_framework.serializers import ValidationError
from jsonattrs.models import Attribute, AttributeType, Schema

from core.tests.utils.cases import UserTestCase
from organization.tests.factories import ProjectFactory
from party import serializers

from .factories import PartyFactory


class PartySerializerTest(UserTestCase, TestCase):
    def test_serialize_party(self):
        party = PartyFactory.create()
        serializer = serializers.PartySerializer(party)
        serialized = serializer.data

        assert serialized['id'] == party.id
        assert serialized['name'] == party.name
        assert serialized['type'] == party.type
        assert 'attributes' in serialized

    def test_create_party(self):
        project = ProjectFactory.create(name='Test Project')

        party_data = {'name': 'Tea Party'}
        serializer = serializers.PartySerializer(
            data=party_data,
            context={'project': project}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        party_instance = serializer.instance
        assert party_instance.name == 'Tea Party'

    def test_validate_valid_attributes(self):
        project = ProjectFactory.create(name='Test Project')
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema,
            name='notes',
            long_name='Notes',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='age',
            long_name='Homeowner Age',
            attr_type=AttributeType.objects.get(name='integer'),
            index=1, required=True, default=0
        )

        party_data = {
            'name': 'Tea Party',
            'type': 'IN',
            'attributes': {
                'notes': 'Blah',
                'age': 2
            }
        }
        serializer = serializers.PartySerializer(
            data=party_data,
            context={'project': project}
        )

        cleaned = serializer.validate_attributes(party_data['attributes'])
        assert cleaned == party_data['attributes']

    def test_validate_invalid_attributes(self):
        project = ProjectFactory.create(name='Test Project')
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema,
            name='notes',
            long_name='Notes',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='age',
            long_name='Homeowner Age',
            attr_type=AttributeType.objects.get(name='integer'),
            index=1, required=True, default=0
        )

        party_data = {
            'name': 'Tea Party',
            'type': 'IN',
            'attributes': {
                'notes': 'Blah',
                'age': 'Blah'
            }
        }
        serializer = serializers.PartySerializer(
            data=party_data,
            context={'project': project}
        )

        with pytest.raises(ValidationError) as e:
            serializer.validate_attributes(party_data['attributes'])
        assert 'Validation failed for age: "Blah"' in e.value.detail

    def test_full_invalid(self):
        project = ProjectFactory.create(name='Test Project')
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema,
            name='notes',
            long_name='Notes',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='age',
            long_name='Homeowner Age',
            attr_type=AttributeType.objects.get(name='integer'),
            index=1, required=True, default=0
        )

        party_data = {
            'name': 'Tea Party',
            'type': 'IN',
            'attributes': {
                'notes': 'Blah',
                'age': 'Blah'
            }
        }
        serializer = serializers.PartySerializer(
            data=party_data,
            context={'project': project}
        )

        with pytest.raises(ValidationError) as e:
            serializer.is_valid(raise_exception=True)
        assert ('Validation failed for age: "Blah"'
                in e.value.detail['attributes'])

    def test_sanitize_strings(self):
        project = ProjectFactory.create(name='Test Project')
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema,
            name='notes',
            long_name='Notes',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='age',
            long_name='Homeowner Age',
            attr_type=AttributeType.objects.get(name='integer'),
            index=1, required=True, default=0
        )

        party_data = {
            'name': '<Tea Party>',
            'type': 'IN',
            'attributes': {
                'notes': 'Blah',
                'age': 2
            }
        }
        serializer = serializers.PartySerializer(
            data=party_data,
            context={'project': project}
        )

        with pytest.raises(ValidationError) as e:
            serializer.is_valid(raise_exception=True)
        # assert e.value.detail['name']
